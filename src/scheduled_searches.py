SCHEDULED_SEARCHES = [
    {
        'id': 'sched_ab12',
        'name': 'Bay Area to Tokyo',
        'enabled': True,
        'origin': ['SFO', 'OAK', 'SJC'],
        'destination': ['HND', 'NRT'],
        'cabin': 'business',
    }
]


def get_scheduled_search(search_id):
    """Return the scheduled search whose id equals ``search_id``, else None."""
    for entry in SCHEDULED_SEARCHES:
        if entry['id'] == search_id:
            return entry
