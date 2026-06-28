# Versioning Strategy

The Chrony NTP add-on uses **dual versioning**:

## Add-on Version

Semantic versioning in `config.yaml` (e.g. `2.0.0`). Tracks HA integration, options, docs, and container packaging.

## Chrony Core Version

Debian package version, recorded at image build in `/etc/chrony-version` and shown in startup logs.

Both versions appear in the add-on log banner on start.
