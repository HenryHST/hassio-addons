ARG BUILD_FROM=ghcr.io/hassio-addons/debian-base:8.1.3
# hadolint ignore=DL3006
FROM ${BUILD_FROM}

# Version labels
ARG BUILD_VERSION
ARG BUILD_DATE
ARG BUILD_REF
ARG NUT_VERSION="2.8.1-5"

# Store versions for runtime access
ENV ADDON_VERSION="${BUILD_VERSION}" \
    NUT_VERSION="${NUT_VERSION}"

# Set shell with pipefail option
SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

# Setup base
# hadolint ignore=DL3003
RUN \
    apt-get update \
    && apt-get install -y --no-install-recommends \
        nut=${NUT_VERSION} \
        nut-snmp=${NUT_VERSION} \
        nut-xml=${NUT_VERSION} \
        nut-modbus=${NUT_VERSION} \
        usbutils=1:018-2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy root filesystem
COPY rootfs /

# Build arguments
ARG BUILD_ARCH
ARG BUILD_DATE
ARG BUILD_DESCRIPTION
ARG BUILD_NAME
ARG BUILD_REF
ARG BUILD_REPOSITORY
ARG BUILD_VERSION

# Labels
LABEL \
    io.hass.name="${BUILD_NAME}" \
    io.hass.description="${BUILD_DESCRIPTION}" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version=${BUILD_VERSION} \
    io.hass.nut.version="${NUT_VERSION}" \
    maintainer="henryhst" \
    org.opencontainers.image.title="${BUILD_NAME}" \
    org.opencontainers.image.description="${BUILD_DESCRIPTION}" \
    org.opencontainers.image.vendor="henryhst Home Assistant Add-ons" \
    org.opencontainers.image.authors="henryhst" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.url="https://github.com/henryhst/hassio-addons" \
    org.opencontainers.image.source="https://github.com/${BUILD_REPOSITORY}" \
    org.opencontainers.image.documentation="https://github.com/${BUILD_REPOSITORY}/blob/main/README.md" \
    org.opencontainers.image.created=${BUILD_DATE} \
    org.opencontainers.image.revision=${BUILD_REF} \
    org.opencontainers.image.version=${BUILD_VERSION}
