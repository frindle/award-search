"""Transfer partner registry keyed by program slug."""

PROGRAMS = {
    'amex_mr': {
        'name': 'American Express Membership Rewards',
        'transfers_to': [
            'hyatt_worldwide',
            'marriott_bonvoy',
            'hilton_honors',
            'delta_sky_miles',
        ],
    },
    'chase_ur': {
        'name': 'Chase Ultimate Rewards',
        'transfers_to': [
            'air_canada',
            'american',
            'united',
            'southwest',
            'jetblue',
            'british_airways',
            'singapore',
            'virgin_atlantic',
        ],
    },
}
