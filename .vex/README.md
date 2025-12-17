# VEX (Vulnerability Exploitability eXchange) Documentation

This directory contains VEX statements for known vulnerabilities that are either false positives or have mitigated risk in the context of our Home Assistant addons.

## What is VEX?

VEX is a standard format for communicating the actual exploitability status of vulnerabilities in software products. It helps reduce false positives and provides transparency about security issues.

## VEX Documents

### `nut-known-issues.openvex.json`

Contains VEX statements for the Network UPS Tools (NUT) addon regarding:

- **CVE-2023-45853** (zlib1g): Not affected - vulnerable code not in execution path
- **CVE-2025-7458** (libsqlite3-0): Under investigation - limited impact due to usage patterns

## Understanding VEX Status

| Status | Meaning |
|--------|---------|
| `not_affected` | The vulnerability does not affect this product |
| `affected` | The product is affected and needs patching |
| `fixed` | The vulnerability has been fixed |
| `under_investigation` | Currently being analyzed |

## Justifications

| Justification | Meaning |
|---------------|---------|
| `vulnerable_code_not_present` | The vulnerable code is not in this version |
| `vulnerable_code_not_in_execute_path` | The code exists but cannot be reached |
| `vulnerable_code_cannot_be_controlled_by_adversary` | Code exists but cannot be exploited |
| `inline_mitigations_already_exist` | Protections are in place |

## Using VEX with Trivy

To use these VEX documents with Trivy:

```bash
# Scan with VEX document
trivy image --vex .vex/nut-known-issues.openvex.json nut:latest

# This will suppress vulnerabilities marked as not_affected
```

## Updating VEX Documents

When updating VEX documents:

1. Update the `timestamp` field
2. Increment the `version` field
3. Add or modify statements as needed
4. Document rationale clearly in `impact_statement`

## References

- [OpenVEX Specification](https://github.com/openvex/spec)
- [Trivy VEX Documentation](https://trivy.dev/docs/supply-chain/vex/)
- [VEX Use Cases](https://www.cisa.gov/resources-tools/resources/vex-use-cases)

## Maintenance

VEX documents are reviewed:
- When new vulnerabilities are discovered
- During security scans
- When upstream packages are updated
- At least quarterly

Last Review: 2025-12-17

