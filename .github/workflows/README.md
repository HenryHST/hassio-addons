# GitHub Actions Workflows

This directory contains automated workflows for building, testing, and releasing the Home Assistant add-ons.

## Workflows

### 🏗️ Build Workflows

#### `build-netboot-xyz.yaml`
Builds and signs the netboot.xyz addon Docker images for all supported architectures.

**Triggers:**
- Push to main/master branch (when netboot_xyz files change)
- Pull requests (when netboot_xyz files change)
- Release published
- Manual dispatch

**Architectures:** aarch64, amd64, armv7

**Outputs:**
- `ghcr.io/{repo}/netboot_xyz:{version}-{arch}`
- `ghcr.io/{repo}/netboot_xyz:latest-{arch}` (on main branch)
- Multi-arch manifest: `ghcr.io/{repo}/netboot_xyz:{version}`

#### `build-nut.yaml`
Builds and signs the Network UPS Tools (NUT) addon Docker images for all supported architectures.

**Triggers:**
- Push to main/master branch (when nut files change)
- Pull requests (when nut files change)
- Release published
- Manual dispatch

**Architectures:** aarch64, amd64, armv7

**Outputs:**
- `ghcr.io/{repo}/nut:{version}-{arch}`
- `ghcr.io/{repo}/nut:latest-{arch}` (on main branch)
- Multi-arch manifest: `ghcr.io/{repo}/nut:{version}`

### ✅ Lint Workflow

#### `lint.yaml`
Runs multiple linters to ensure code quality and consistency.

**Checks:**
- **YAML Lint**: Validates YAML syntax
- **ShellCheck**: Analyzes shell scripts for potential issues
- **Hadolint**: Lints Dockerfiles for best practices
- **Config Validation**: Validates addon config.yaml files

**Triggers:**
- Push to main/master
- Pull requests
- Manual dispatch

### 🚀 Release Workflow

#### `release.yaml`
Manages addon releases and version updates.

**Features:**
- Manual version updates via workflow dispatch
- Automatic version bumping
- Release notes generation

**Triggers:**
- Release published
- Manual dispatch (with version input)

## Image Signing

All Docker images are signed using [Cosign](https://github.com/sigstore/cosign) with keyless signing (OIDC).

**Verify a signed image:**
```bash
cosign verify \
  --certificate-identity-regexp="https://github.com/{repo}" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
  ghcr.io/{repo}/netboot_xyz:1.0.0
```

## Multi-Architecture Support

Both addons support multiple architectures:

| Architecture | Platform | Description |
|--------------|----------|-------------|
| aarch64 | linux/arm64 | ARM 64-bit (Raspberry Pi 4, 5) |
| amd64 | linux/amd64 | x86 64-bit (Intel/AMD) |
| armv7 | linux/arm/v7 | ARM 32-bit (Raspberry Pi 3) |

## GitHub Actions Permissions

The workflows require the following permissions:

```yaml
permissions:
  contents: read        # Read repository content
  packages: write       # Push to GitHub Container Registry
  id-token: write       # Keyless signing with Cosign
```

## Caching

Build caching is enabled using GitHub Actions cache to speed up subsequent builds:

- Cache scope: `{addon_name}-{arch}`
- Cache mode: `max` (cache all layers)

## Manual Workflow Dispatch

### Build a specific addon manually:

1. Go to **Actions** tab
2. Select the workflow (e.g., "Build netboot.xyz Addon")
3. Click **Run workflow**
4. Select branch and click **Run workflow**

### Create a new release:

1. Go to **Actions** tab
2. Select "Release" workflow
3. Click **Run workflow**
4. Enter version (e.g., `1.0.1`)
5. Click **Run workflow**

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ADDON_NAME` | Name of the addon | Set per workflow |
| `REGISTRY` | Container registry | `ghcr.io` |

## Secrets

No additional secrets are required. The workflows use:
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions

## Troubleshooting

### Build fails with "permission denied"

Ensure the repository has **Packages** write permission enabled in Settings → Actions → General.

### Images not signed

Cosign signing requires `id-token: write` permission. Check the workflow permissions.

### Cache issues

Clear the cache:
1. Go to **Actions** → **Caches**
2. Delete relevant caches
3. Re-run the workflow

## Best Practices

1. **Test locally first**: Build and test Docker images locally before pushing
2. **Use pull requests**: Workflows run on PRs without pushing images
3. **Semantic versioning**: Follow semver for version numbers
4. **Update CHANGELOGs**: Document changes in addon CHANGELOG.md files

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Buildx](https://docs.docker.com/buildx/working-with-buildx/)
- [Cosign](https://docs.sigstore.dev/cosign/overview/)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)

