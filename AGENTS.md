# Wiki Checklist Agents

This app is a lightweight Checklist/Passport app for Wikimedians to track items (places, artworks, fruits, etc.). 

Catalogs are defined by Wikidata queries (e.g., botanical gardens in Brazil, planetaria,South American countries). 

A secondary goal is to encourage improving the
Wikidata items as they go, without expanding product scope. The main challenge is resisting scope creep. 

Do the catalog/checklist thing extremely well.

## Core scope (must stay solid)
- Wikimedia OAuth-only login (no local auth).
- Public catalogs with shareable, unique slugs and single SPARQL query.
- Personal list (one per user) created inside a catalog.
- Queries must return `?item`; optional `?itemLabel`, `?itemDescription`, `?image` and `?coord` are stored.
- Query results are capped at the first 1000 items.
- Catalog refresh pulls places; list details show stored values only.
- User stamps are simple checkboxes per catalog item (no timestamps).
– Basic support for mobile use

## Non-goals (avoid scope creep)
- No social features (follows, feeds, comments, likes).
- No rewards/gamification beyond the simple stamp.
- No editing Wikidata or writing back to WM projects.
- No complex permissions, roles, or sharing controls.
- No heavy analytics, exports, or dashboards.

## Principles
- Keep data minimal and easy to reason about.
- Reliability over features; prefer simple, clear UX.
- Avoid new dependencies unless clearly necessary.
- Keep public surfaces fast and predictable.

## Definition of done
- [x] The passport/checklist flow works end-to-end with minimal steps.
- [x] Catalog refresh is robust and handles errors gracefully.
- [x] Stamping is accurate and idempotent.
- [x] The UI makes the main flow obvious and quick.
