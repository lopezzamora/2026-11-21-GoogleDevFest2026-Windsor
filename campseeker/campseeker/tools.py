"""Small ADK function tools, with source fields preserved for evaluation."""
from .client import NPSClient
from .config import Settings


def _client():
    settings = Settings.from_env()
    return NPSClient(settings.nps_api_key, settings.timeout_seconds)


def _lookup(resource, fields, **kwargs):
    try:
        result = _client().query(resource, **kwargs)
    except ValueError as exc:
        return {'status': 'error', 'error_code': 'configuration_error', 'message': str(exc)}
    if result['status'] == 'success':
        # Reduce token volume without converting missing fields or 'Unknown' to False.
        result['data'] = [{key: row[key] for key in fields if key in row}
                          for row in result['data']]
    return result


PARK_FIELDS = ('id', 'parkCode', 'fullName', 'name', 'designation', 'states', 'url',
               'description', 'activities', 'operatingHours', 'entranceFees', 'weatherInfo')
CAMPGROUND_FIELDS = ('id', 'parkCode', 'name', 'description', 'url', 'reservationUrl',
                     'reservationInfo', 'regulationsUrl', 'regulationsOverview',
                     'amenities', 'accessibility', 'operatingHours', 'fees',
                     'campsites', 'addresses', 'contacts', 'directionsUrl')
ALERT_FIELDS = ('id', 'parkCode', 'title', 'description', 'category', 'url', 'lastIndexedDate')


def search_parks(query: str = '', state_code: str = '', limit: int = 20, start: int = 0) -> dict:
    """Find NPS units by name/keyword and/or US state postal code.

    Args:
        query: Park name or keyword, e.g. Acadia. Leave empty for a state search.
        state_code: One postal abbreviation, e.g. ME for Maine or VA for Virginia.
        limit: Page size from 1 to 50.
        start: Zero-based offset; use next_start to continue a partial result.
    Returns:
        NPS park codes, public source links, descriptions and pagination metadata.
        These are NPS units, not all state/private parks or campgrounds.
    """
    return _lookup('parks', PARK_FIELDS, query=query, state_code=state_code, limit=limit, start=start)


def get_campgrounds(park_code: str, limit: int = 20, start: int = 0) -> dict:
    """Retrieve campground evidence for a park code returned by search_parks.

    Args:
        park_code: Four-character NPS park code, e.g. acad.
        limit: Page size from 1 to 50.
        start: Offset; follow next_start before claiming there are no suitable options.
    Returns:
        Campground records with amenities, operating hours, fees and source links
        where supplied by NPS. Missing fields remain missing. Descriptions do not
        establish live campsite availability or make a reservation.
    """
    return _lookup('campgrounds', CAMPGROUND_FIELDS, park_code=park_code, limit=limit, start=start)


def get_alerts(park_code: str, limit: int = 20, start: int = 0) -> dict:
    """Retrieve published NPS alerts to assess relevance to a proposed visit.

    Args:
        park_code: Four-character NPS park code obtained from park search.
        limit: Page size from 1 to 50.
        start: Offset for additional pages.
    Returns:
        Alerts with descriptions, categories and source links. Assess their
        affected area/activity and dates; a local closure need not close a park.
        lastIndexedDate is an index timestamp, not proof of the alert's validity period.
        A failed request or an empty feed is not proof that all facilities are open.
    """
    return _lookup('alerts', ALERT_FIELDS, park_code=park_code, limit=limit, start=start)
