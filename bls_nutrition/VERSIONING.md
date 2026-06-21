# Versioning Strategy

The BLS Nährwertdatenbank add-on uses **dual versioning**:

## Addon Version

Semantic versioning in `config.yaml` (e.g. `1.0.0`). Tracks add-on features, API changes, and integration updates.

## BLS Core Version

The bundled data version from Max Rubner-Institut (currently **4.0**). Visible in:

- Startup logs
- `/health` endpoint
- `sensor.bls_bls_version` (integration)

## Open Food Facts

No pinned version — live API lookups with local caching.
