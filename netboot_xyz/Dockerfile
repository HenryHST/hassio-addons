FROM alpine:3.20

# Set version label
ARG BUILD_DATE
ARG BUILD_VERSION
ARG BUILD_REF
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

# Default command
CMD ["/bin/bash", "/start.sh"]

