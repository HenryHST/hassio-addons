# hadolint ignore=DL3006
ARG BUILD_FROM=ghcr.io/hassio-addons/alpine-base:3.20
FROM ${BUILD_FROM}

# Set version label
ARG BUILD_DATE
ARG BUILD_VERSION
ARG BUILD_REF
ARG WEBAPP_VERSION
ARG NETBOOTXYZ_VERSION="0.7.6"

LABEL \
    io.hass.name="netboot.xyz" \
    io.hass.description="netboot.xyz network boot manager" \
    io.hass.version="${BUILD_VERSION}" \
    io.hass.type="addon" \
    io.hass.arch="aarch64|amd64|armv7" \
    io.hass.netbootxyz.version="${NETBOOTXYZ_VERSION}"

# Store versions in environment for runtime access
ENV ADDON_VERSION="${BUILD_VERSION}" \
    NETBOOTXYZ_VERSION="${NETBOOTXYZ_VERSION}"

# Set shell with pipefail option
SHELL ["/bin/ash", "-eo", "pipefail", "-c"]

# Install required packages
# hadolint ignore=DL3018
RUN \
    apk add --no-cache \
        bash \
        busybox \
        curl \
        envsubst \
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
    && groupmod -g 1000 users \
    && useradd -u 911 -U -d /config -s /bin/false nbxyz \
    && usermod -G users nbxyz \
    && mkdir -p /app /config /defaults /assets

# Install netboot.xyz webapp
WORKDIR /app
RUN \
    if [ -z ${WEBAPP_VERSION+x} ]; then \
        WEBAPP_VERSION=$(curl -sX GET "https://api.github.com/repos/netbootxyz/webapp/releases/latest" \
        | awk '/tag_name/{print $4;exit}' FS='[""]'); \
    fi \
    && curl -o /tmp/webapp.tar.gz -L \
        "https://github.com/netbootxyz/webapp/archive/${WEBAPP_VERSION}.tar.gz" \
    && tar xf /tmp/webapp.tar.gz -C /app/ --strip-components=1 \
    && npm install --production \
    && rm -rf /tmp/*

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

# Default command
CMD ["/bin/bash", "/start.sh"]

