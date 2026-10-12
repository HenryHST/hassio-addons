FROM alpine:3.24

# Set version label
ARG BUILD_DATE
ARG BUILD_VERSION
ARG BUILD_REF
ARG BUILD_ARCH
ARG BUILD_NAME
ARG BUILD_DESCRIPTION
ARG BUILD_REPOSITORY
ARG NETBOOTXYZ_VERSION="0.7.6"

LABEL \
    io.hass.name="${BUILD_NAME}" \
    io.hass.description="${BUILD_DESCRIPTION}" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version="${BUILD_VERSION}" \
    io.hass.netbootxyz.version="${NETBOOTXYZ_VERSION}" \
    maintainer="henryhst" \
    org.opencontainers.image.title="${BUILD_NAME}" \
    org.opencontainers.image.description="${BUILD_DESCRIPTION}" \
    org.opencontainers.image.vendor="henryhst Home Assistant Add-ons" \
    org.opencontainers.image.authors="henryhst" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.url="https://github.com/henryhst/hassio-addons" \
    org.opencontainers.image.source="https://github.com/${BUILD_REPOSITORY}" \
    org.opencontainers.image.documentation="https://github.com/${BUILD_REPOSITORY}/blob/main/netboot_xyz/DOCS.md" \
    org.opencontainers.image.created="${BUILD_DATE}" \
    org.opencontainers.image.revision="${BUILD_REF}" \
    org.opencontainers.image.version="${BUILD_VERSION}"

# Store versions in environment for runtime access
ENV ADDON_VERSION="${BUILD_VERSION}" \
    NETBOOTXYZ_VERSION="${NETBOOTXYZ_VERSION}"

# Set shell with pipefail option
SHELL ["/bin/ash", "-eo", "pipefail", "-c"]

# Install required packages and setup base system
# hadolint ignore=DL3018
RUN \
    apk add --no-cache \
        bash \
        busybox \
        ca-certificates \
        curl \
        gettext \
        git \
        jq \
        nginx \
        nodejs \
        npm \
        shadow \
        sudo \
        supervisor \
        syslog-ng \
        tar \
        tftp-hpa \
        tzdata \
    && rm -rf /var/cache/apk/* \
    && groupmod -g 1000 users \
    && useradd -u 911 -U -d /config -s /bin/false nbxyz \
    && usermod -G users nbxyz \
    && mkdir -p /app /config /defaults /assets /var/log/nginx \
    && ln -sf /dev/stdout /var/log/nginx/access.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log

# Install netboot.xyz webapp
WORKDIR /app
ARG NETBOOTXYZ_VERSION
RUN \
    echo "Installing netboot.xyz webapp version: ${NETBOOTXYZ_VERSION}" \
    && curl -fsSL -o /tmp/webapp.tar.gz \
        "https://github.com/netbootxyz/webapp/archive/${NETBOOTXYZ_VERSION}.tar.gz" \
    && tar xzf /tmp/webapp.tar.gz -C /app/ --strip-components=1 \
    && npm install --omit=dev \
    && echo "Applying security patches..." \
    && npm install systeminformation@5.27.14 express@4.22.2 js-yaml@4.3.0 --save --omit=dev \
    && npm audit fix --omit=dev \
    && npm cache clean --force \
    && rm -rf /tmp/* /root/.npm

# Reset workdir to root
WORKDIR /

# Environment variables
ENV TFTPD_OPTS=''
ENV NGINX_PORT='80'
ENV WEB_APP_PORT='3000'

# Copy root filesystem
COPY root/ /

# Set executable permissions for scripts
RUN chmod +x /start.sh /init.sh

# Expose ports
EXPOSE 69/udp 80 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://127.0.0.1:3000/ || exit 1

# Default command
CMD ["/bin/bash", "/start.sh"]

