FROM debian:bookworm-slim

ARG BUILD_VERSION
ARG BUILD_DATE
ARG BUILD_REF

ENV ADDON_VERSION="${BUILD_VERSION}" \
    CHRONY_VERSION_FILE=/etc/chrony-version

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
        tzdata \
        procps \
        xz-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ARG BASHIO_VERSION="0.16.2"
RUN \
    curl -L -o /tmp/bashio.tar.gz \
        "https://github.com/hassio-addons/bashio/archive/v${BASHIO_VERSION}.tar.gz" \
    && mkdir -p /tmp/bashio \
    && tar -xzf /tmp/bashio.tar.gz -C /tmp/bashio --strip-components=1 \
    && mv /tmp/bashio/lib /usr/lib/bashio \
    && ln -s /usr/lib/bashio/bashio /usr/bin/bashio \
    && rm -rf /tmp/*

ARG S6_OVERLAY_VERSION="3.1.6.2"
RUN \
    ARCH="$(uname -m)" \
    && case "${ARCH}" in \
        x86_64) S6_ARCH="x86_64" ;; \
        aarch64) S6_ARCH="aarch64" ;; \
        armv7l) S6_ARCH="armhf" ;; \
        *) echo "Unsupported architecture: ${ARCH}" && exit 1 ;; \
    esac \
    && curl -L -o /tmp/s6-overlay-noarch.tar.xz \
        "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz" \
    && curl -L -o /tmp/s6-overlay-arch.tar.xz \
        "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-${S6_ARCH}.tar.xz" \
    && tar -C / -Jxpf /tmp/s6-overlay-noarch.tar.xz \
    && tar -C / -Jxpf /tmp/s6-overlay-arch.tar.xz \
    && rm -rf /tmp/*

# hadolint ignore=DL3008
RUN \
    apt-get update \
    && apt-get install -y --no-install-recommends \
        chrony \
    && CHRONY_VERSION="$(dpkg-query -W -f='${Version}' chrony)" \
    && echo "${CHRONY_VERSION}" > /etc/chrony-version \
    && mkdir -p /run/chrony /var/lib/chrony \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY rootfs /

RUN chmod +x /etc/cont-init.d/* \
    && chmod +x /etc/services.d/chronyd/run \
    && chmod +x /etc/services.d/chronyd/finish

ARG BUILD_ARCH
ARG BUILD_NAME
ARG BUILD_DESCRIPTION
ARG BUILD_REPOSITORY

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

ENTRYPOINT ["/init"]
