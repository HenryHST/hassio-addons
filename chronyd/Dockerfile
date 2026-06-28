FROM alpine:3.24

ARG BUILD_VERSION
ARG BUILD_DATE
ARG BUILD_REF
ARG BUILD_ARCH
ARG BUILD_NAME
ARG BUILD_DESCRIPTION
ARG BUILD_REPOSITORY

ENV ADDON_VERSION="${BUILD_VERSION}" \
    CHRONY_VERSION_FILE=/etc/chrony-version \
    NTP_DIRECTIVES="ratelimit\nrtcsync"

SHELL ["/bin/sh", "-eo", "pipefail", "-c"]

# hadolint ignore=DL3018
RUN \
    apk add --no-cache \
        bash \
        chrony-nts \
        jq \
        su-exec \
        tzdata \
    && CHRONY_VERSION="$(chronyd -v 2>&1 | head -n1 | awk '{print $2}')" \
    && echo "${CHRONY_VERSION}" > /etc/chrony-version \
    && rm /etc/chrony/chrony.conf \
    && chmod 1750 /etc/chrony \
    && mkdir -p /run/chrony /var/lib/chrony \
    && chown -R chrony:chrony /etc/chrony /run/chrony /var/lib/chrony \
    && chmod 1750 /etc/chrony /run/chrony /var/lib/chrony

COPY assets/startup.sh /bin/startup
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /bin/startup /entrypoint.sh

LABEL \
    io.hass.name="${BUILD_NAME}" \
    io.hass.description="${BUILD_DESCRIPTION}" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version="${BUILD_VERSION}" \
    maintainer="henryhst" \
    org.opencontainers.image.title="${BUILD_NAME}" \
    org.opencontainers.image.description="${BUILD_DESCRIPTION}" \
    org.opencontainers.image.vendor="henryhst Home Assistant Add-ons" \
    org.opencontainers.image.authors="henryhst" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.url="https://github.com/henryhst/hassio-addons" \
    org.opencontainers.image.source="https://github.com/${BUILD_REPOSITORY}" \
    org.opencontainers.image.documentation="https://github.com/${BUILD_REPOSITORY}/blob/main/chronyd/DOCS.md" \
    org.opencontainers.image.created="${BUILD_DATE}" \
    org.opencontainers.image.revision="${BUILD_REF}" \
    org.opencontainers.image.version="${BUILD_VERSION}"

EXPOSE 123/udp

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD chronyc -n tracking || exit 1

ENTRYPOINT ["/entrypoint.sh"]
