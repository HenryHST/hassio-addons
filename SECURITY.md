# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it by:

1. **Email**: Contact the maintainer directly
2. **GitHub Security Advisory**: Use the [Security tab](../../security/advisories/new) to report privately
3. **Do NOT** create a public issue for security vulnerabilities

We will respond within 48 hours and work with you to understand and address the issue.

## Supported Versions

| Addon | Version | Supported |
|-------|---------|-----------|
| netboot.xyz | 1.0.x | ✅ Yes |
| Network UPS Tools | 1.0.x | ✅ Yes |

## Security Measures

### Automated Security Scanning

All Docker images are automatically scanned for vulnerabilities:

- **Daily Scans**: Automated Trivy scans at 02:00 UTC
- **Pull Request Scans**: Security validation before merge
- **Build-time Scans**: Images scanned during CI/CD pipeline
- **SARIF Reports**: Results available in GitHub Security tab

### Vulnerability Severity

We follow standard CVE severity ratings:

| Severity | Response Time | Action |
|----------|---------------|--------|
| 🔴 **CRITICAL** | Immediate (< 24h) | Emergency patch release |
| 🟠 **HIGH** | 1-3 days | Priority fix in next release |
| 🟡 **MEDIUM** | 1-2 weeks | Scheduled fix |
| 🔵 **LOW** | Best effort | Fixed when convenient |

### Security Features

#### Docker Images

- ✅ **Official Base Images**: Alpine Linux and Debian from official sources
- ✅ **Minimal Attack Surface**: Only required packages installed
- ✅ **Image Signing**: All images signed with Cosign
- ✅ **Regular Updates**: Base images updated regularly
- ✅ **Non-root User**: Services run as unprivileged users where possible

#### Build Process

- ✅ **Dependency Scanning**: npm audit during build
- ✅ **Automated Patching**: Security updates applied automatically
- ✅ **Reproducible Builds**: Version-pinned dependencies
- ✅ **Supply Chain Security**: Verified sources only

#### Runtime Security

- ✅ **AppArmor Profiles**: Mandatory access control
- ✅ **Capability Dropping**: Minimal Linux capabilities
- ✅ **Network Isolation**: Only required ports exposed
- ✅ **Read-only Filesystem**: Where applicable

## Known Vulnerabilities

### Current Status

Check the [Security tab](../../security) for current vulnerability status.

### Recently Fixed

#### CVE-2025-68154 (netboot.xyz)
- **Severity**: HIGH
- **Component**: `systeminformation` npm package
- **Fixed in**: Version 1.0.2
- **Details**: OS Command Injection in fsSize() function
- **Resolution**: Updated to systeminformation@5.27.14

#### CVE-2024-10918, CVE-2025-6020 (NUT)
- **Severity**: HIGH
- **Component**: libcurl4, libpam-modules (Debian packages)
- **Fixed in**: Version 1.0.2
- **Details**: Various security vulnerabilities in system libraries
- **Resolution**: Applied apt-get upgrade during build process

#### CVE-2025-7458 (NUT)
- **Severity**: CRITICAL
- **Component**: libsqlite3-0
- **Status**: Partial fix applied via apt-get upgrade
- **Note**: Fix availability depends on Debian security updates

#### CVE-2023-45853 (NUT)
- **Severity**: CRITICAL
- **Component**: zlib1g
- **Status**: Will not fix (marked by Debian)
- **Note**: Debian team has marked this as will_not_fix
- **Mitigation**: Monitor for future updates

## Security Best Practices

### For Users

1. **Keep Updated**: Always use the latest addon version
2. **Review Logs**: Monitor addon logs for suspicious activity
3. **Network Segmentation**: Isolate addons on separate networks if possible
4. **Backup Regularly**: Maintain backups of addon configurations
5. **Review Permissions**: Only grant necessary permissions

### For Contributors

1. **Dependency Updates**: Keep dependencies up to date
2. **Code Review**: All PRs require review
3. **Security Testing**: Test security implications of changes
4. **Secrets Management**: Never commit secrets or credentials
5. **Least Privilege**: Follow principle of least privilege

## Security Contacts

- **Maintainer**: henryhst
- **Repository**: https://github.com/henryhst/hassio-addons
- **Security Tab**: https://github.com/henryhst/hassio-addons/security

## Security Tools

### Trivy Scanner

All images are scanned with [Trivy](https://trivy.dev/):

```bash
# Scan netboot.xyz image
docker build -t netboot_xyz:test ./netboot_xyz
trivy image netboot_xyz:test

# Scan NUT image
docker build -t nut:test ./nut
trivy image nut:test

# Scan with specific severity
trivy image --severity CRITICAL,HIGH netboot_xyz:test

# Scan with VEX document (suppress known false positives)
trivy image --vex .vex/nut-known-issues.openvex.json nut:test
```

### VEX (Vulnerability Exploitability eXchange)

We publish VEX statements for known vulnerabilities that are false positives or have mitigated risk:

- **Location**: `.vex/` directory
- **Format**: OpenVEX JSON
- **Purpose**: Reduce false positives and improve security transparency
- **Documentation**: See [.vex/README.md](.vex/README.md)

VEX statements help security scanners understand which vulnerabilities actually affect our addons.

### NPM Audit

For netboot.xyz addon:

```bash
cd netboot_xyz
# Check for vulnerabilities
npm audit

# Fix automatically
npm audit fix
```

## Disclosure Policy

- We follow **responsible disclosure** practices
- Security issues are fixed before public disclosure
- Credits given to reporters (unless they wish to remain anonymous)
- Security advisories published after fixes are released

## Updates and Notifications

- Watch this repository for security updates
- Subscribe to release notifications
- Check the Security tab regularly
- Follow changelog for security fixes

---

**Last Updated**: 2025-12-17

For questions about this security policy, please open a discussion or contact the maintainer.
