# checklist.toolforge.org

A scaffold for a Wikimedia Checklist tool. Users authenticate with Wikimedia OAuth, create public catalogs backed by Wikidata SPARQL queries, and build personal lists from those catalog places. A secondary goal is to encourage improving Wikidata items while visiting, without expanding the product scope.

## Features (scaffold)

- OAuth-only login with Wikimedia (no local accounts).
- Public catalogs with shareable slugs and a SPARQL query.
- Catalog queries store `?item` and optional `?itemLabel`, `?itemDescription`, `?image`, `?coord` values (stored when present).
- Catalog creation runs the query once and stores places (capped at 1000).
- Refresh pulls entities from the Wikidata Query Service and stores catalog places (capped at 1000).
- Personal lists (one per user per catalog) are automatically created when starting a checklist.
- Checklist stamps are per-user and per-place (no timestamps).

## Local setup

1. Install [uv](https://github.com/astral-sh/uv) and create a virtualenv:

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

2. Copy `.env.sample` to `.env` and set:

- `DJANGO_SECRET_KEY`
- `OAUTH_CLIENT_ID` and `OAUTH_CLIENT_SECRET` (required for standard OAuth login)

If you only need developer access (see below), you can skip the OAuth client
settings.

3. Create migrations, apply them, and start the server:

```bash
python manage.py makemigrations accounts lists
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

4. If you want standard OAuth login, register your OAuth consumer on Meta-Wiki
and set the callback to:

```
http://localhost:8000/auth/callback/
```

For local testing over HTTP, you may need:

```bash
export AUTHLIB_INSECURE_TRANSPORT=1
```

## Catalogs and lists

Catalogs are the public entry point. Create a catalog on the home page, then
share its URL (`/catalogs/<slug>/`) so others can access the same places.
Users can simply click "Start Checklist" on any catalog page to begin tracking their progress.
Each user has exactly one checklist per catalog.

### Developer access (OAuth token)

For local testing without the full OAuth consumer flow, you can use a personal
OAuth access token:

1. Request a Personal API token at <https://api.wikimedia.org/wiki/Special:AppManagement>.
2. Copy the Access token value.
3. Open <http://localhost:8000/auth/login/dev/> and paste the token to log in.

This flow does not require `OAUTH_CLIENT_ID` or `OAUTH_CLIENT_SECRET`, but it
still uses the OAuth profile endpoint configured by `OAUTH_AUTHORIZATION_SERVER`.

## Toolforge deployment (outline)

- Clone into `~/www/python/` and create a `.env` file in `~/www/python/checklist`.
- Create a ToolsDB database user and database (see Toolforge docs).
- Run migrations and collect static files inside the webservice container:

```bash
webservice python3.11 shell -- webservice-python-bootstrap
webservice python3.11 shell -- ./www/python/venv/bin/python ./www/python/checklist/manage.py migrate
webservice python3.11 shell -- ./www/python/venv/bin/python ./www/python/checklist/manage.py collectstatic --noinput
```

- Start the webservice:

```bash
webservice python3.11 start
```

Adjust `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` for your tool hostname.

## SPARQL query expectations

Queries must return at least one variable:

- `?item` with the Wikidata entity URI (or Q-id).

Optional variables are stored when present:

- `?itemLabel`
- `?itemDescription`
- `?image`
- `?coord` (coordinates in WKT format, e.g., `Point(30 10)`)

Image values should be Wikimedia URLs or `wdt:P18` file names; non-Wikimedia
URLs are ignored.

Catalog and list displays use stored values only (no live query calls). The `?item` is
the focus for improvement as people stamp items and add information.

## Example queries

Botanical gardens in Brazil (instance of Q167346, country Brazil):

```sparql
SELECT ?item ?itemLabel ?itemDescription ?image ?coord WHERE {
  ?item wdt:P31 wd:Q167346;
        wdt:P17 wd:Q155.
  OPTIONAL { ?item wdt:P18 ?image. }
  OPTIONAL { ?item wdt:P625 ?coord. }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],pt,pt-br,en,mul". }
}
LIMIT 1000
```

SESC units (instance of Q117307883):

```sparql
SELECT ?item ?itemLabel ?itemDescription ?image ?coord WHERE {
  ?item wdt:P31 wd:Q117307883.
  OPTIONAL { ?item wdt:P18 ?image. }
  OPTIONAL { ?item wdt:P625 ?coord. }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],pt,pt-br,en,mul". }
}
LIMIT 1000
```

## Roadmap to v1.0

- [ ] Search (for catalogs and in personal lists)
- [ ] Improve views for unlogged users
- [ ] Basic stats (e.g., percentage complete)
- [ ] Map display of catalogs
- [ ] Review mobile support
- [ ] Integration/links to Wikipedia 


