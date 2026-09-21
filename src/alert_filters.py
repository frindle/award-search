"""Canonical airline-alert filter dict for the alert pipeline."""


def get_filter():
    """Return the canonical airline-alert filter dict."""
    return {'airlines': ['UA', 'NH'], 'max_points': 90000, 'max_taxes': 100.0}
