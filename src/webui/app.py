import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
import uvicorn

from ..browser.manager import BrowserManager, BrowserConfig
from ..search.engine import SearchEngine
from ..search.programs.base import SearchQuery
from ..search.programs.base import load_programs_config
from ..awardwallet import AwardWalletClient
from ..seats_aero import SeatsAeroClient, SeatsAeroAvailability
from ..pushover import PushoverClient, send_award_notification
from ..google_flights import search_positioning_multi, SerpApiClient
from ..settings import load_settings, save_settings


search_results: Dict[str, Any] = {}
saved_alerts: Dict[str, Dict] = {}

MAX_RESULTS_AGE = timedelta(hours=24)


def _cleanup_old_results():
    """Remove results older than 24 hours."""
    cutoff = datetime.now() - MAX_RESULTS_AGE
    to_delete = [
        k for k, v in search_results.items()
        if datetime.fromisoformat(v["timestamp"]) < cutoff
    ]
    for k in to_delete:
        del search_results[k]


def _generate_search_id() -> str:
    return f"search_{uuid.uuid4().hex[:12]}"


def _validate_airport(code: str) -> str:
    """Validate airport code is 3 uppercase letters."""
    code = code.strip().upper()
    if len(code) != 3 or not code.isalpha():
        raise ValueError(f"Invalid airport code: {code}")
    return code


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("WebUI starting up")
    yield
    logger.info("WebUI shutting down")


app = FastAPI(title="Award Search", lifespan=lifespan)

BASE_DIR = Path(__file__).parent.parent.parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "src" / "webui" / "templates"))


def _jinja2_format_number(value):
    if value is None:
        return "0"
    return f"{value:,}"


def _jinja2_truncate(value, length=8, kill_long=False):
    if value is None:
        return ""
    s = str(value)
    if kill_long and len(s) > length:
        return s[:length] + "..."
    return s[:length]


templates.env.filters["formatnumber"] = _jinja2_format_number
templates.env.filters["truncate"] = _jinja2_truncate


def get_programs():
    return load_programs_config()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    programs = get_programs()
    settings = load_settings()

    seats_aero_status = "configured" if settings.get("seats_aero_api_key") else "not_configured"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "programs": programs,
        "awardwallet_user": settings.get("awardwallet_user_id", ""),
        "seats_aero_status": seats_aero_status,
    })


@app.post("/search", response_class=HTMLResponse)
async def search(
    request: Request,
    origin: str = Form(...),
    destination: str = Form(...),
    departure_date: str = Form(...),
    return_date: Optional[str] = Form(None),
    cabin: str = Form("economy"),
    round_trip: bool = Form(False),
    selected_programs: List[str] = Form(default=[]),
    search_source: str = Form("browser"),
    show_balances: bool = Form(False),
    user_id: str = Form(""),
):
    _cleanup_old_results()
    search_id = _generate_search_id()
    origin = _validate_airport(origin)
    destination = _validate_airport(destination)
    
    try:
        departure = date.fromisoformat(departure_date)
        if return_date:
            return_date = date.fromisoformat(return_date).isoformat()
    except ValueError:
        return templates.TemplateResponse("results.html", {
            "request": request,
            "search_id": "",
            "origin": origin.upper(),
            "destination": destination.upper(),
            "departure_date": departure_date,
            "return_date": return_date,
            "cabin": cabin,
            "programs": get_programs(),
            "selected_programs": selected_programs,
            "search_results": {"errors": ["Invalid date format. Use YYYY-MM-DD"]},
        })

    balances_summary = None
    seats_aero_results = []

    if show_balances:
        try:
            settings = load_settings()
            api_key = settings.get("awardwallet_api_key")
            effective_user = user_id or settings.get("awardwallet_user_id")
            if api_key and effective_user:
                client = AwardWalletClient(api_key, effective_user)
                balances_summary = client.get_balances()
        except Exception as e:
            logger.warning(f"Could not fetch balances: {e}")

    if search_source == "seats_aero":
        seats_aero_results = _search_seats_aero(origin, destination, departure_date, return_date, cabin, selected_programs)

        search_results[search_id] = {
            "query": {
                "origin": origin.upper(),
                "destination": destination.upper(),
                "departure_date": departure_date,
                "return_date": return_date,
                "cabin": cabin,
            },
            "seats_aero_results": seats_aero_results,
            "balances": _format_balances(balances_summary) if balances_summary else None,
            "timestamp": datetime.now().isoformat(),
        }
    else:
        browser_results = await _search_browser(
            origin, destination, departure_date, return_date, cabin, selected_programs
        )

        search_results[search_id] = {
            "query": {
                "origin": origin.upper(),
                "destination": destination.upper(),
                "departure_date": departure_date,
                "return_date": return_date,
                "cabin": cabin,
            },
            "browser_results": browser_results,
            "balances": _format_balances(balances_summary) if balances_summary else None,
            "timestamp": datetime.now().isoformat(),
        }

    programs = get_programs()
    return templates.TemplateResponse("results.html", {
        "request": request,
        "search_id": search_id,
        "origin": origin.upper(),
        "destination": destination.upper(),
        "departure_date": departure_date,
        "return_date": return_date,
        "cabin": cabin,
        "programs": programs,
        "selected_programs": selected_programs,
        "search_results": search_results[search_id],
    })


@app.get("/results/{search_id}", response_class=HTMLResponse)
async def get_results(search_id: str, request: Request):
    if search_id not in search_results:
        raise HTTPException(status_code=404, detail="Search not found")

    programs = get_programs()
    data = search_results[search_id]
    return templates.TemplateResponse("results.html", {
        "request": request,
        "search_id": search_id,
        "origin": data["query"]["origin"],
        "destination": data["query"]["destination"],
        "departure_date": data["query"]["departure_date"],
        "return_date": data["query"]["return_date"],
        "cabin": data["query"]["cabin"],
        "programs": programs,
        "selected_programs": [],
        "search_results": data,
    })


@app.get("/positioning", response_class=HTMLResponse)
async def positioning_page(request: Request):
    settings = load_settings()
    serpapi_configured = bool(settings.get("serpapi_api_key"))

    return templates.TemplateResponse("positioning.html", {
        "request": request,
        "serpapi_configured": serpapi_configured,
    })


@app.post("/positioning/search", response_class=HTMLResponse)
async def positioning_search(
    request: Request,
    home_airport: str = Form(...),
    target_hub: str = Form(...),
    departure_date: str = Form(...),
    cabin: str = Form("economy"),
    nearby_airports: str = Form(""),
):
    try:
        departure = date.fromisoformat(departure_date)
    except ValueError:
        return templates.TemplateResponse("positioning.html", {
            "request": request,
            "serpapi_configured": serpapi_configured,
            "error": "Invalid date format. Use YYYY-MM-DD",
        })
    nearby = [a.strip().upper() for a in nearby_airports.split(",") if a.strip()] if nearby_airports else None

    settings = load_settings()
    serpapi_configured = bool(settings.get("serpapi_api_key"))

    if not serpapi_configured:
        return templates.TemplateResponse("positioning.html", {
            "request": request,
            "serpapi_configured": False,
            "error": "SerpAPI not configured. Set SERPAPI_API_KEY env var or create credentials/serpapi.yml",
        })

    result = search_positioning_multi(
        origin=home_airport.upper(),
        destination=target_hub.upper(),
        departure_date=departure,
        cabin=cabin.lower(),
        nearby_origins=nearby,
    )

    flights_data = [
        {
            "airline": f.airline,
            "flight_number": f.flight_number,
            "origin": f.origin,
            "destination": f.destination,
            "departure_time": f.departure_time,
            "arrival_time": f.arrival_time,
            "duration_minutes": f.duration_minutes,
            "stops": f.stops,
            "price": f.price,
            "currency": f.currency,
            "booking_link": f.booking_link,
        }
        for f in result.flights
    ]

    return templates.TemplateResponse("positioning_results.html", {
        "request": request,
        "home_airport": home_airport.upper(),
        "target_hub": target_hub.upper(),
        "departure_date": departure_date,
        "cabin": cabin,
        "nearby_airports": nearby_airports,
        "flights": flights_data,
        "errors": result.errors,
    })


@app.get("/balances", response_class=HTMLResponse)
async def get_balances(request: Request, user_id: Optional[str] = None):
    settings = load_settings()

    api_key = settings.get("awardwallet_api_key")
    effective_user = user_id or settings.get("awardwallet_user_id")

    if not api_key or not effective_user:
        return templates.TemplateResponse("balances.html", {
            "request": request,
            "error": "AwardWallet not configured. Add your API key in Settings.",
            "user_id": effective_user,
            "balances": None,
        })

    try:
        client = AwardWalletClient(api_key, effective_user)
        summary = client.get_balances()
    except Exception as e:
        return templates.TemplateResponse("balances.html", {
            "request": request,
            "error": str(e),
            "user_id": effective_user,
            "balances": None,
        })

    return templates.TemplateResponse("balances.html", {
        "request": request,
        "user_id": effective_user,
        "balances": summary,
        "error": None,
    })


@app.get("/settings", response_class=HTMLResponse)
async def get_settings_page(request: Request):
    settings = load_settings()
    configured = {
        "seats_aero": bool(settings.get("seats_aero_api_key")),
        "awardwallet": bool(settings.get("awardwallet_api_key") and settings.get("awardwallet_user_id")),
        "serpapi": bool(settings.get("serpapi_api_key")),
        "pushover": bool(settings.get("pushover_app_token") and settings.get("pushover_user_key")),
    }
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "settings": settings,
        "configured": configured,
    })


@app.post("/settings/save")
async def save_settings_form(
    request: Request,
    seats_aero_api_key: str = Form(""),
    awardwallet_api_key: str = Form(""),
    awardwallet_user_id: str = Form(""),
    serpapi_api_key: str = Form(""),
    pushover_app_token: str = Form(""),
    pushover_user_key: str = Form(""),
):
    save_settings({
        "seats_aero_api_key": seats_aero_api_key,
        "awardwallet_api_key": awardwallet_api_key,
        "awardwallet_user_id": awardwallet_user_id,
        "serpapi_api_key": serpapi_api_key,
        "pushover_app_token": pushover_app_token,
        "pushover_user_key": pushover_user_key,
    })
    return RedirectResponse(url="/settings?saved=1", status_code=303)


@app.get("/alerts", response_class=HTMLResponse)
async def get_alerts(request: Request):
    return templates.TemplateResponse("alerts.html", {
        "request": request,
        "alerts": saved_alerts,
    })


@app.post("/alerts/create", response_class=HTMLResponse)
async def create_alert(
    request: Request,
    origin: str = Form(...),
    destination: str = Form(...),
    departure_date: str = Form(...),
    cabin: str = Form("economy"),
    programs: List[str] = Form(default=[]),
    notify_pushover: bool = Form(False),
):
    alert_id = f"alert_{uuid.uuid4().hex[:12]}"

    saved_alerts[alert_id] = {
        "id": alert_id,
        "origin": origin.upper(),
        "destination": destination.upper(),
        "departure_date": departure_date,
        "cabin": cabin,
        "programs": programs,
        "notify_pushover": notify_pushover,
        "created_at": datetime.now().isoformat(),
        "last_checked": None,
        "last_results": None,
    }

    return templates.TemplateResponse("alerts.html", {
        "request": request,
        "alerts": saved_alerts,
        "message": f"Alert created for {origin.upper()} → {destination.upper()}",
    })


@app.post("/alerts/{alert_id}/check", response_class=HTMLResponse)
async def check_alert(alert_id: str, request: Request):
    if alert_id not in saved_alerts:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert = saved_alerts[alert_id]

    results = _search_seats_aero(
        alert["origin"],
        alert["destination"],
        alert["departure_date"],
        None,
        alert["cabin"],
        alert["programs"],
    )

    alert["last_checked"] = datetime.now().isoformat()
    alert["last_results"] = results

    if results and alert.get("notify_pushover"):
        for r in results:
            send_award_notification(
                origin=alert["origin"],
                destination=alert["destination"],
                date=r["date"],
                program=r["source"],
                miles=r["cost"],
                cabin=alert["cabin"],
                seats=r["seats"],
            )

    return templates.TemplateResponse("alert_result.html", {
        "request": request,
        "alert": alert,
        "results": results,
    })


@app.post("/alerts/{alert_id}/delete")
async def delete_alert(alert_id: str):
    if alert_id in saved_alerts:
        del saved_alerts[alert_id]
    return RedirectResponse(url="/alerts", status_code=303)


@app.get("/api/alerts/{alert_id}/results")
async def get_alert_results(alert_id: str):
    if alert_id not in saved_alerts:
        raise HTTPException(status_code=404, detail="Alert not found")
    return saved_alerts[alert_id].get("last_results", [])




def _search_seats_aero(origin, destination, departure_date, return_date, cabin, programs):
    try:
        client = SeatsAeroClient()
    except ValueError:
        return []

    dep_date = date.fromisoformat(departure_date)
    ret_date = date.fromisoformat(return_date) if return_date else None

    results = client.search(
        origin=origin.upper(),
        destination=destination.upper(),
        start_date=dep_date,
        end_date=dep_date,
        cabins=[cabin],
        programs=programs if programs else None,
    )

    formatted = []
    for avail in results:
        cabin_key = cabin.lower()
        if avail.cabin_avail.get(cabin_key):
            formatted.append({
                "source": avail.source,
                "date": avail.departure_date.isoformat() if avail.departure_date else departure_date,
                "cost": avail.cabin_cost.get(cabin_key, 0),
                "seats": avail.cabin_seats.get(cabin_key, 0),
                "airlines": avail.cabin_airlines.get(cabin_key, []),
                "direct": avail.cabin_direct.get(cabin_key, False),
                "last_seen": avail.last_seen,
                "availability_id": avail.availability_id,
            })

    return formatted


async def _search_browser(origin, destination, departure_date, return_date, cabin, programs):
    try:
        engine = SearchEngine()
        await engine.initialize()

        query = SearchQuery(
            origin=origin.upper(),
            destination=destination.upper(),
            departure_date=date.fromisoformat(departure_date),
            return_date=date.fromisoformat(return_date) if return_date else None,
            cabin=cabin.lower(),
        )

        program_list = programs if programs else None
        results = await engine.search(query, program_list, credentials={})
        await engine.close()

        return [
            {
                "program": r.program,
                "segments": [
                    {
                        "airline": s.airline,
                        "flight_number": s.flight_number,
                        "departure_airport": s.departure_airport,
                        "arrival_airport": s.arrival_airport,
                        "departure_time": s.departure_time,
                        "arrival_time": s.arrival_time,
                        "duration_minutes": s.duration_minutes,
                        "stops": s.stops,
                    }
                    for s in r.segments
                ],
                "miles": r.price.miles,
                "taxes": r.price.taxes,
            }
            for r in results.results
        ]
    except Exception as e:
        logger.exception("Browser search failed")
        return []


def _format_balances(summary):
    if not summary:
        return None
    return {
        "timestamp": summary.timestamp,
        "airlines": [
            {
                "name": a.display_name,
                "balance": a.balance_formatted,
                "status": a.status,
            }
            for a in summary.airlines()
        ],
        "credit_cards": [
            {
                "name": a.display_name,
                "balance": a.balance_formatted,
            }
            for a in summary.credit_cards()
        ],
    }


def run_server(host: str = "0.0.0.0", port: int = 8000):
    uvicorn.run(app, host=host, port=port)