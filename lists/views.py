import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.db import IntegrityError, transaction
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CatalogForm, SimpleCatalogForm
from .models import Catalog, PassportStamp, VisitingList, VisitingPlace
from .services import WikidataQueryError, refresh_catalog_places, search_wikidata_entities

logger = logging.getLogger(__name__)


def list_index(request):
    catalogs = Catalog.objects.select_related("created_by").order_by("-created_at")
    
    user_catalogs = []
    other_catalogs = []
    
    if request.user.is_authenticated:
        user_list_catalog_ids = set(
            VisitingList.objects.filter(created_by=request.user).values_list("catalog_id", flat=True)
        )
        for catalog in catalogs:
            if catalog.id in user_list_catalog_ids:
                user_catalogs.append(catalog)
            else:
                other_catalogs.append(catalog)
    else:
        other_catalogs = list(catalogs)

    return render(
        request,
        "lists/catalog_index.html",
        {
            "user_catalogs": user_catalogs,
            "other_catalogs": other_catalogs,
        },
    )


@login_required
def catalog_create(request):
    # Check if user wants simple or advanced mode
    mode = request.GET.get("mode", "simple")
    use_simple_mode = mode == "simple"
    
    if use_simple_mode:
        form = SimpleCatalogForm()
        if request.method == "POST":
            form = SimpleCatalogForm(request.POST)
            if form.is_valid():
                # Create catalog from simple form data
                catalog = Catalog(
                    name=form.get_catalog_name(),
                    slug=form.cleaned_data["slug"],
                    description=form.get_catalog_description(),
                    query=form.get_sparql_query(),
                    created_by=request.user,
                )
                try:
                    with transaction.atomic():
                        catalog.save()
                        created_count = refresh_catalog_places(catalog)
                except WikidataQueryError as exc:
                    form.add_error(None, f"Query failed: {exc}")
                    logger.warning("Catalog query failed for %s: %s", catalog.name, exc)
                except Exception:
                    logger.exception("Catalog creation failed for %s", catalog.name)
                    form.add_error(None, "Something went wrong while creating the catalog.")
                else:
                    messages.success(request, f"Catalog created with {created_count} items.")
                    return redirect("catalog_detail", slug=catalog.slug)
    else:
        # Advanced mode with raw SPARQL
        form = CatalogForm()
        if request.method == "POST":
            form = CatalogForm(request.POST)
            if form.is_valid():
                catalog = form.save(commit=False)
                catalog.created_by = request.user
                try:
                    with transaction.atomic():
                        catalog.save()
                        created_count = refresh_catalog_places(catalog)
                except WikidataQueryError as exc:
                    form.add_error("query", f"Query failed: {exc}")
                    logger.warning("Catalog query failed for %s: %s", catalog.name, exc)
                except Exception:
                    logger.exception("Catalog creation failed for %s", catalog.name)
                    form.add_error(None, "Something went wrong while creating the catalog.")
                else:
                    messages.success(request, f"Catalog created with {created_count} items.")
                    return redirect("catalog_detail", slug=catalog.slug)
    
    return render(
        request, 
        "lists/catalog_create.html", 
        {
            "form": form,
            "mode": mode,
        }
    )


def catalog_detail(request, slug):
    catalog = get_object_or_404(Catalog.objects.select_related("created_by"), slug=slug)
    places = catalog.places.order_by("entity_id")
    
    visiting_list = None
    stamped_place_ids = set()

    if request.user.is_authenticated:
        visiting_list, _ = VisitingList.objects.get_or_create(
            catalog=catalog,
            created_by=request.user,
        )
        stamped_place_ids = set(
            PassportStamp.objects.filter(user=request.user, place__catalog=catalog).values_list(
                "place_id",
                flat=True,
            )
        )

    place_rows = [
        {
            "place": place,
            "stamped": place.id in stamped_place_ids,
        }
        for place in places
    ]

    # Handle sorting by stamped status
    sort_by = request.GET.get('sort', '')
    if sort_by == 'stamped_first':
        place_rows.sort(key=lambda x: (not x["stamped"], x["place"].entity_id))
    elif sort_by == 'unstamped_first':
        place_rows.sort(key=lambda x: (x["stamped"], x["place"].entity_id))

    return render(
        request,
        "lists/catalog_detail.html",
        {
            "catalog": catalog,
            "visiting_list": visiting_list,
            "place_rows": place_rows,
            "is_catalog_owner": request.user.is_authenticated
            and catalog.created_by_id == request.user.id,
            "sort_by": sort_by,
        },
    )





def _wants_json(request):
    requested_with = request.headers.get("X-Requested-With", "")
    if requested_with in {"fetch", "XMLHttpRequest"}:
        return True
    accept = request.headers.get("Accept", "")
    return "application/json" in accept


@login_required
@require_POST
def catalog_refresh(request, slug):
    catalog = get_object_or_404(Catalog, slug=slug)
    if catalog.created_by_id != request.user.id:
        return HttpResponseForbidden("Only the catalog owner can refresh items.")

    try:
        created_count = refresh_catalog_places(catalog)
    except WikidataQueryError as exc:
        messages.error(request, f"Query failed: {exc}")
        logger.warning("Catalog refresh failed for %s: %s", catalog.slug, exc)
    except Exception:
        logger.exception("Catalog refresh failed for %s", catalog.slug)
        messages.error(request, "Something went wrong while refreshing this catalog.")
    else:
        messages.success(request, f"Added {created_count} new items.")

    return redirect("catalog_detail", slug=catalog.slug)


@login_required
@require_POST
def stamp_toggle(request, list_id, entity_id):
    wants_json = _wants_json(request)
    visiting_list = get_object_or_404(
        VisitingList.objects.select_related("catalog"),
        pk=list_id,
    )
    if visiting_list.created_by_id != request.user.id:
        if wants_json:
            return JsonResponse({"error": "forbidden"}, status=403)
        return HttpResponseForbidden("This list is private.")
    catalog = visiting_list.catalog
    if not catalog:
        if wants_json:
            return JsonResponse({"error": "missing_catalog"}, status=400)
        return HttpResponseForbidden("List has no catalog.")
    place = get_object_or_404(
        VisitingPlace,
        catalog=catalog,
        entity_id=entity_id,
    )

    try:
        checked = request.POST.get("checked") in {"on", "true", "1"}
        if checked:
            try:
                PassportStamp.objects.get_or_create(user=request.user, place=place)
            except IntegrityError:
                pass
        else:
            PassportStamp.objects.filter(user=request.user, place=place).delete()
    except Exception:
        logger.exception(
            "Stamp toggle failed for list=%s place=%s user=%s",
            visiting_list.id,
            entity_id,
            request.user.id,
        )
        if wants_json:
            return JsonResponse({"error": "server_error"}, status=500)
        messages.error(request, "Something went wrong while saving that stamp.")
        return redirect("catalog_detail", slug=catalog.slug)

    current_checked = PassportStamp.objects.filter(user=request.user, place=place).exists()
    if wants_json:
        return JsonResponse({"checked": current_checked})

    return redirect("catalog_detail", slug=catalog.slug)


def wikidata_autocomplete(request):
    """API endpoint for Wikidata entity autocomplete."""
    search_term = request.GET.get("q", "").strip()
    if not search_term:
        return JsonResponse({"results": []})
    
    results = search_wikidata_entities(search_term)
    return JsonResponse({"results": results})
