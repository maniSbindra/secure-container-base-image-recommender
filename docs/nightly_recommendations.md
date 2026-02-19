# Nightly Top Recommended Images by Language

_Generated: 2026-02-19T04:23:04.320283Z from azure_linux_images.db. Criteria: lowest critical -> high -> total vulnerabilities -> size. Top 10 per language._

## Scanned Repositories and Images

This report includes analysis from **15 configured sources**:

### Repositories (6 total)

The following repositories were scanned with multiple tags enumerated:

- `mcr.microsoft.com/azurelinux/base/nodejs`
- `mcr.microsoft.com/azurelinux/base/python`
- `mcr.microsoft.com/azurelinux/distroless/base`
- `mcr.microsoft.com/azurelinux/distroless/java`
- `mcr.microsoft.com/azurelinux/distroless/node`
- `mcr.microsoft.com/azurelinux/distroless/python`

### Single Images (9 total)

The following specific image tags were scanned:

- `docker.io/library/node:20.0-slim`
- `docker.io/library/python:3-slim`
- `docker.io/library/python:3.12-slim`
- `mcr.microsoft.com/dotnet/aspnet:8.0`
- `mcr.microsoft.com/dotnet/runtime:8.0`
- `mcr.microsoft.com/dotnet/sdk:8.0`
- `mcr.microsoft.com/openjdk/jdk:21-azurelinux`
- `mcr.microsoft.com/openjdk/jdk:21-distroless`
- `mcr.microsoft.com/openjdk/jdk:21-ubuntu`

_Note: Repository scans may include multiple tags per repository, while single images represent specific tagged images._

**Note:** Image sizes are based on Linux amd64 platform as reported by `docker images` on GitHub runners. Actual sizes may vary significantly on other platforms (macOS, Windows, etc.).

## Dotnet

| Rank | Image | Version | Crit | High | Total | Size | Digest |
|------|-------|---------|------|------|-------|------|--------|
| 1 | `mcr.microsoft.com/dotnet/runtime:8.0` | 8.0.24 | 1 | 2 | 88 | 285.0 MB | `sha256:b969aeab7f6b` |
| 2 | `mcr.microsoft.com/dotnet/aspnet:8.0` | 8.0.24 | 1 | 2 | 88 | 320.0 MB | `sha256:0d6e2e245f18` |
| 3 | `mcr.microsoft.com/dotnet/sdk:8.0` | 8.0.418 | 1 | 15 | 170 | 1.20 GB | `sha256:58359d0b8fe8` |

## Java

| Rank | Image | Version | Crit | High | Total | Size | Digest |
|------|-------|---------|------|------|-------|------|--------|
| 1 | `mcr.microsoft.com/openjdk/jdk:21-azurelinux` | 21.0.10 | 0 | 0 | 0 | 726.0 MB | `sha256:1eab4bdecb9d` |
| 2 | `mcr.microsoft.com/openjdk/jdk:21-distroless` | 21.0.10 | 1 | 0 | 1 | 532.0 MB | `sha256:ed2544cbbf0f` |
| 3 | `mcr.microsoft.com/openjdk/jdk:21-ubuntu` | 21.0.10 | 1 | 0 | 64 | 722.0 MB | `sha256:0bfb17af5a1c` |

## Node

| Rank | Image | Version | Crit | High | Total | Size | Digest |
|------|-------|---------|------|------|-------|------|--------|
| 1 | `mcr.microsoft.com/azurelinux/base/nodejs:20` | 20.14.0 | 0 | 0 | 0 | 214.0 MB | `sha256:59a1e9373259` |
| 2 | `mcr.microsoft.com/azurelinux/base/nodejs:20.14` | 20.14.0 | 0 | 0 | 0 | 214.0 MB | `sha256:59a1e9373259` |
| 3 | `docker.io/library/node:20.0-slim` | 20.0.0 | 6 | 54 | 252 | 359.0 MB | `sha256:702d475af4b8` |

## Perl

| Rank | Image | Version | Crit | High | Total | Size | Digest |
|------|-------|---------|------|------|-------|------|--------|
| 1 | `docker.io/library/python:3-slim` | 5.40.1 | 0 | 2 | 69 | 179.0 MB | `sha256:486b8092bfb1` |
| 2 | `docker.io/library/python:3.12-slim` | 5.40.1 | 0 | 2 | 70 | 179.0 MB | `sha256:9e01bf1ae5db` |
| 3 | `mcr.microsoft.com/openjdk/jdk:21-ubuntu` | 5.34.0 | 1 | 0 | 64 | 722.0 MB | `sha256:0bfb17af5a1c` |
| 4 | `mcr.microsoft.com/dotnet/runtime:8.0` | 5.36.0 | 1 | 2 | 88 | 285.0 MB | `sha256:b969aeab7f6b` |
| 5 | `mcr.microsoft.com/dotnet/aspnet:8.0` | 5.36.0 | 1 | 2 | 88 | 320.0 MB | `sha256:0d6e2e245f18` |
| 6 | `mcr.microsoft.com/dotnet/sdk:8.0` | 5.36.0 | 1 | 15 | 170 | 1.20 GB | `sha256:58359d0b8fe8` |
| 7 | `docker.io/library/node:20.0-slim` | 5.32.1 | 6 | 54 | 252 | 359.0 MB | `sha256:702d475af4b8` |

## Python

| Rank | Image | Version | Crit | High | Total | Size | Digest |
|------|-------|---------|------|------|-------|------|--------|
| 1 | `mcr.microsoft.com/azurelinux/distroless/python:3` | 3.12.9 | 0 | 0 | 0 | 121.0 MB | `sha256:358a31b2fed4` |
| 2 | `mcr.microsoft.com/azurelinux/distroless/python:3-nonroot` | 3.12.9 | 0 | 0 | 0 | 121.0 MB | `sha256:66bdc517a7fe` |
| 3 | `mcr.microsoft.com/azurelinux/distroless/python:3.12` | 3.12.9 | 0 | 0 | 0 | 121.0 MB | `sha256:358a31b2fed4` |
| 4 | `mcr.microsoft.com/azurelinux/distroless/python:3.12-nonroot` | 3.12.9 | 0 | 0 | 0 | 121.0 MB | `sha256:66bdc517a7fe` |
| 5 | `mcr.microsoft.com/azurelinux/base/python:3` | 3.12.9 | 0 | 0 | 0 | 203.0 MB | `sha256:7be8b46a4dfa` |
| 6 | `mcr.microsoft.com/azurelinux/base/python:3.12` | 3.12.9 | 0 | 0 | 0 | 203.0 MB | `sha256:7be8b46a4dfa` |
| 7 | `mcr.microsoft.com/openjdk/jdk:21-azurelinux` | 3.12.9 | 0 | 0 | 0 | 726.0 MB | `sha256:1eab4bdecb9d` |
| 8 | `docker.io/library/python:3-slim` | 3.14.3 | 0 | 2 | 69 | 179.0 MB | `sha256:486b8092bfb1` |
| 9 | `docker.io/library/python:3.12-slim` | 3.12.12 | 0 | 2 | 70 | 179.0 MB | `sha256:9e01bf1ae5db` |
