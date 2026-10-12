#!/bin/bash
# #region agent log
echo "[syslog-ng-debug] starting diagnostic wrapper"
SYNERR=$(/usr/sbin/syslog-ng --syntax-only --no-caps 2>&1) || true
echo "[syslog-ng-debug] syntax-only exit=$? output=${SYNERR}"
DEBUG_PAYLOAD="{\"sessionId\":\"92f7bb\",\"runId\":\"post-fix\",\"hypothesisId\":\"S1\",\"location\":\"syslog-ng-debug.sh\",\"message\":\"syslog-ng syntax/start probe\",\"data\":{\"syntax_output\":\"$(echo "${SYNERR}" | tr '\n' ' ' | tr -d '"')\"},\"timestamp\":$(date +%s000)}"
echo "${DEBUG_PAYLOAD}" >> /config/debug-92f7bb.ndjson 2>/dev/null || true
# #endregion
# Upstream docker-netbootxyz no longer runs syslog-ng; keep process optional.
exec /usr/sbin/syslog-ng --foreground --no-caps
