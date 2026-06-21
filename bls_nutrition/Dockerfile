FROM python:3.12-slim-bookworm

ARG BUILD_VERSION
ARG BUILD_DATE
ARG BUILD_REF
ARG BUILD_ARCH
ARG BUILD_NAME
ARG BUILD_DESCRIPTION
ARG BUILD_REPOSITORY
ARG BLS_VERSION="4.0"

ENV ADDON_VERSION="${BUILD_VERSION}" \
    BLS_VERSION="${BLS_VERSION}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app"

SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

# hadolint ignore=DL3008
RUN \
    apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        jq \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY root/app /app/app
COPY root/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

LABEL \
    io.hass.name="${BUILD_NAME}" \
    io.hass.description="${BUILD_DESCRIPTION}" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version="${BUILD_VERSION}" \
    io.hass.bls.version="${BLS_VERSION}" \
    maintainer="henryhst" \
    org.opencontainers.image.title="${BUILD_NAME}" \
    org.opencontainers.image.description="${BUILD_DESCRIPTION}" \
    org.opencontainers.image.vendor="henryhst Home Assistant Add-ons" \
    org.opencontainers.image.authors="henryhst" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.url="https://github.com/henryhst/hassio-addons" \
    org.opencontainers.image.source="https://github.com/${BUILD_REPOSITORY}" \
    org.opencontainers.image.documentation="https://github.com/${BUILD_REPOSITORY}/blob/main/bls_nutrition/DOCS.md" \
    org.opencontainers.image.created="${BUILD_DATE}" \
    org.opencontainers.image.revision="${BUILD_REF}" \
    org.opencontainers.image.version="${BUILD_VERSION}"

EXPOSE 8090

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8090/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
