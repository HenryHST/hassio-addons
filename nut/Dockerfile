FROM debian:bookworm-slim

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

# Install base requirements and apply security updates
# hadolint ignore=DL3008
RUN \
    apt-get update \
    && echo "Applying security updates..." \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        jq \
        tzdata \
        procps \
        xz-utils \
    && echo "Installed versions:" \
    && dpkg -l | grep -E 'libcurl|libpam|libsqlite3|zlib1g' || true \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install bashio (Home Assistant add-on utility)
ARG BASHIO_VERSION="0.16.2"
RUN \
    curl -L -o /tmp/bashio.tar.gz \
        "https://github.com/hassio-addons/bashio/archive/v${BASHIO_VERSION}.tar.gz" \
    && mkdir -p /tmp/bashio \
    && tar -xzf /tmp/bashio.tar.gz -C /tmp/bashio --strip-components=1 \
    && mv /tmp/bashio/lib /usr/lib/bashio \
    && ln -s /usr/lib/bashio/bashio /usr/bin/bashio \
    && rm -rf /tmp/*

# Install s6-overlay for service management
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

# Install NUT packages with latest security patches
# hadolint ignore=DL3008
RUN \
    apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        nut \
        nut-snmp \
        nut-xml \
        nut-modbus \
        usbutils \
    && echo "NUT version:" \
    && upsd -V || true \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy root filesystem
COPY rootfs /

# Set executable permissions for service scripts
RUN chmod +x /etc/cont-init.d/* \
    && chmod +x /etc/services.d/upsmon/run \
    && chmod +x /etc/services.d/upsmon/finish \
    && chmod +x /etc/services.d/upsd/run \
    && chmod +x /etc/services.d/upsd/finish \
    && chmod +x /usr/bin/notify \
    && chmod +x /usr/bin/shutdownhost

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

# Set s6-overlay entrypoint
ENTRYPOINT ["/init"]
