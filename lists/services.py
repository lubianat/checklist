import logging
from dataclasses import dataclass
from urllib.parse import quote, urlparse

import requests
from django.conf import settings

from .models import VisitingPlace


class WikidataQueryError(Exception):
    pass


@dataclass
class PlaceResult:
    entity_id: str
    label: str
    description: str
    image: str
    coord: str


MAX_RESULTS = 1000

logger = logging.getLogger(__name__)


def search_wikidata_entities(search_term, language="en", limit=10):
    """Search for Wikidata entities using the Wikidata search API."""
    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "search": search_term,
        "language": language,
        "limit": limit,
        "format": "json",
    }
    headers = {
        "User-Agent": settings.WIKIMEDIA_USER_AGENT,
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        results = []
        for item in data.get("search", []):
            results.append({
                "id": item.get("id", ""),
                "label": item.get("label", ""),
                "description": item.get("description", ""),
            })
        return results
    except Exception as exc:
        logger.warning("Wikidata entity search failed: %s", exc)
        return []


def generate_sparql_query(item_type_id, location_id):
    """Generate a SPARQL query for items of a given type in a given location.
    
    Uses P131 (located in administrative territorial entity) with * for any level,
    which works for countries, states, cities, etc.
    """
    query = f"""SELECT ?item ?itemLabel ?itemDescription ?image ?coord WHERE {{
  ?item wdt:P31 wd:{item_type_id};
        wdt:P131* wd:{location_id}.
  OPTIONAL {{ ?item wdt:P18 ?image. }}
  OPTIONAL {{ ?item wdt:P625 ?coord. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],pt,pt-br,en,mul". }}
}}
LIMIT 1000"""
    return query


def _extract_entity_id(value):
    if "/" in value:
        return value.rsplit("/", 1)[-1]
    return value


def _normalize_image_value(value):
    if not value:
        return ""
    if value.startswith("http://") or value.startswith("https://"):
        parsed = urlparse(value)
        if parsed.netloc.endswith("wikimedia.org") or parsed.netloc.endswith("wikidata.org"):
            return value
        return ""
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{quote(value)}"


class WikidataQueryService:
    def __init__(self, endpoint=None):
        self.endpoint = endpoint or settings.WIKIDATA_QUERY_ENDPOINT
        self.user_agent = settings.WIKIMEDIA_USER_AGENT

    def fetch_places(self, query):
        headers = {
            "Accept": "application/sparql-results+json",
            "User-Agent": self.user_agent,
        }
        response = requests.post(
            self.endpoint,
            params={"format": "json"},
            data={"query": query},
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        try:
            payload = response.json()
        except ValueError as exc:
            raise WikidataQueryError("Query response was not valid JSON.") from exc
        self._validate_payload(payload)
        return self._parse_results(payload)

    def _validate_payload(self, payload):
        if not isinstance(payload, dict):
            raise WikidataQueryError("Query response was not a JSON object.")
        vars_list = payload.get("head", {}).get("vars", [])
        if "item" not in vars_list:
            raise WikidataQueryError("Query must return ?item.")

    def _parse_results(self, payload):
        bindings = payload.get("results", {}).get("bindings") or []
        results = []
        for row in bindings:
            item = row.get("item")
            if not item or "value" not in item:
                continue
            entity_id = _extract_entity_id(item["value"])
            label = ""
            label_row = row.get("itemLabel")
            if label_row and "value" in label_row:
                label = label_row["value"]
            description = ""
            description_row = row.get("itemDescription")
            if description_row and "value" in description_row:
                description = description_row["value"]
            image = ""
            image_row = row.get("image")
            if image_row and "value" in image_row:
                image = _normalize_image_value(image_row["value"])
            coord = ""
            coord_row = row.get("coord")
            if coord_row and "value" in coord_row:
                coord = coord_row["value"]
            results.append(
                PlaceResult(
                    entity_id=entity_id,
                    label=label,
                    description=description,
                    image=image,
                    coord=coord,
                )
            )
        return results


def refresh_catalog_places(catalog):
    query = (catalog.query or "").strip()
    if not query:
        raise WikidataQueryError("Catalog query is empty.")
    service = WikidataQueryService()
    try:
        results = service.fetch_places(query)
    except requests.RequestException as exc:
        raise WikidataQueryError(str(exc))
    except Exception:
        logger.exception("Unexpected error while querying catalog %s", catalog.slug)
        raise

    deduped = {}
    for place in results:
        existing = deduped.get(place.entity_id)
        if not existing:
            deduped[place.entity_id] = place
            continue
        deduped[place.entity_id] = PlaceResult(
            entity_id=place.entity_id,
            label=existing.label or place.label,
            description=existing.description or place.description,
            image=existing.image or place.image,
            coord=existing.coord or place.coord,
        )

    results = list(deduped.values())[:MAX_RESULTS]
    existing = {
        place.entity_id: place
        for place in VisitingPlace.objects.filter(catalog=catalog)
    }
    new_places = []
    for place in results:
        existing_place = existing.get(place.entity_id)
        if existing_place:
            update_fields = []
            if place.label and place.label != existing_place.label:
                existing_place.label = place.label
                update_fields.append("label")
            if place.description and place.description != existing_place.description:
                existing_place.description = place.description
                update_fields.append("description")
            if place.image and place.image != existing_place.image:
                existing_place.image = place.image
                update_fields.append("image")
            if place.coord and place.coord != existing_place.coord:
                existing_place.coord = place.coord
                update_fields.append("coord")
            if update_fields:
                existing_place.save(update_fields=update_fields)
        else:
            new_places.append(
                VisitingPlace(
                    catalog=catalog,
                    entity_id=place.entity_id,
                    label=place.label,
                    description=place.description,
                    image=place.image,
                    coord=place.coord,
                )
            )
    try:
        VisitingPlace.objects.bulk_create(new_places, ignore_conflicts=True)
    except TypeError:
        VisitingPlace.objects.bulk_create(new_places)
    return len(new_places)
