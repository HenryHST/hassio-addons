ARG BUILD_FROM
FROM ${BUILD_FROM}

# Copy root filesystem
COPY root/ /

# Set working directory
WORKDIR /

# Expose ports
EXPOSE 69/udp 80 3000

# Default command
CMD ["sh", "/start.sh"]

