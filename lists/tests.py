from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import TestCase

from .models import Catalog, PassportStamp, VisitingList, VisitingPlace
from .services import PlaceResult, WikidataQueryError, refresh_catalog_places


class RefreshPlacesTests(TestCase):
    def test_refresh_places_stores_optional_fields(self):
        catalog = Catalog.objects.create(
            name="Test Catalog",
            slug="test-catalog",
            description="",
            query="SELECT ?item WHERE {}",
            created_by=User.objects.create_user(username="tester"),
        )
        payload = {
            "head": {"vars": ["item", "itemLabel", "itemDescription", "image", "coord"]},
            "results": {
                "bindings": [
                    {
                        "item": {"type": "uri", "value": "http://www.wikidata.org/entity/Q1"},
                        "itemLabel": {"type": "literal", "value": "Garden"},
                        "image": {"type": "literal", "value": "File:Example.jpg"},
                        "coord": {"type": "literal", "value": "Point(10 20)"},
                    },
                    {
                        "item": {"type": "uri", "value": "http://www.wikidata.org/entity/Q1"},
                        "itemDescription": {"type": "literal", "value": "Nice place"},
                        "image": {"type": "literal", "value": "https://example.com/evil.jpg"},
                    },
                ]
            },
        }
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = payload

        with patch("lists.services.requests.post", return_value=response):
            created = refresh_catalog_places(catalog)

        self.assertEqual(created, 1)
        self.assertEqual(VisitingPlace.objects.count(), 1)
        place = VisitingPlace.objects.get()
        self.assertEqual(place.entity_id, "Q1")
        self.assertEqual(place.label, "Garden")
        self.assertEqual(place.description, "Nice place")
        self.assertEqual(
            place.image,
            "https://commons.wikimedia.org/wiki/Special:FilePath/File%3AExample.jpg",
        )
        self.assertEqual(place.coord, "Point(10 20)")

    def test_refresh_places_caps_results(self):
        catalog = Catalog.objects.create(
            name="Cap Catalog",
            slug="cap-catalog",
            description="",
            query="SELECT ?item WHERE {}",
            created_by=User.objects.create_user(username="capper"),
        )
        results = [
            PlaceResult(entity_id=f"Q{n}", label="", description="", image="", coord="")
            for n in range(5)
        ]
        with patch("lists.services.MAX_RESULTS", 2):
            with patch("lists.services.WikidataQueryService.fetch_places", return_value=results):
                created = refresh_catalog_places(catalog)

        self.assertEqual(created, 2)
        self.assertEqual(VisitingPlace.objects.count(), 2)


class ListCreationTests(TestCase):
    def test_catalog_create_query_failure_does_not_persist(self):
        user = User.objects.create_user(username="creator")
        self.client.force_login(user)
        with patch("lists.views.refresh_catalog_places", side_effect=WikidataQueryError("fail")):
            response = self.client.post(
                "/catalogs/create/",
                data={
                    "name": "Bad Catalog",
                    "slug": "bad-catalog",
                    "description": "Nope",
                    "query": "SELECT ?item WHERE {}",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Catalog.objects.count(), 0)
        self.assertIn("query", response.context["form"].errors)


class StampToggleTests(TestCase):
    def test_stamp_created(self):
        user = User.objects.create_user(username="stamper")
        catalog = Catalog.objects.create(
            name="Stamp Catalog",
            slug="stamp-catalog",
            description="",
            query="SELECT ?item WHERE {}",
            created_by=user,
        )
        visiting_list = VisitingList.objects.create(
            catalog=catalog,
            created_by=user,
        )
        place = VisitingPlace.objects.create(catalog=catalog, entity_id="Q1")

        self.client.force_login(user)
        response = self.client.post(
            f"/lists/{visiting_list.id}/stamp/{place.entity_id}/",
            data={"checked": "on"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(PassportStamp.objects.filter(user=user, place=place).exists())
