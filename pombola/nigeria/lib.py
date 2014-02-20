def significant_positions_filter(qs):
    """Return a queryset only with 'significant' positions from it

    If you pass in a Position queryset, this should return a queryset
    which has filtered out any positions that aren't considered
    'significant' for this country; this is used to determine which
    positions are shown on place pages, for instance.

    In the case of Nigeria, we only want to consider Senators,
    Governors and Federal Representatives."""

    return qs.filter(title__slug__in=('governor', 'representative', 'senator'))
