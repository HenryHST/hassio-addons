FROM debian:bookworm-slim

# Version labels
ARG BUILD_VERSION
ARG BUILD_DATE
ARG BUILD_REF

# Store versions for runtime access
ENV ADDON_VERSION="${BUILD_VERSION}"

# Set shell with pipefail option for safer script execution
SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

# Install base requirements and apply security updates
# hadolint ignore=DL3008
RUN \
    apt-get update \
    && echo "Applying security updates for base packages..." \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        jq \
        netcat-openbsd \
        procps \
        corosync-qnetd \
    && echo "Installed Corosync QNetd version:" \
    && COROSYNC_VERSION=$(dpkg -l | grep corosync-qnetd | awk '{print $3}') \
    && echo "  Version: ${COROSYNC_VERSION}" \
    && export COROSYNC_VERSION \
    && corosync-qnetd -v \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Build arguments for labels
ARG BUILD_ARCH
ARG BUILD_NAME
ARG BUILD_DESCRIPTION
ARG BUILD_REPOSITORY

# Labels
LABEL \
    io.hass.name="${BUILD_NAME}" \
    io.hass.description="${BUILD_DESCRIPTION}" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version=${BUILD_VERSION} \
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

# Expose Corosync QNetd port
EXPOSE 5403

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD nc -z localhost 5403 || exit 1

ENTRYPOINT ["/entrypoint.sh"]
