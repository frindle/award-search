FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p output && chmod 755 output

EXPOSE 8000

CMD ["uvicorn", "src.webui.app:app", "--host", "0.0.0.0", "--port", "8000"]