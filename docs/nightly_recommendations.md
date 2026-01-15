# Nightly Top Recommended Images by Language

_Generated: 2026-01-15T12:45:38.424950Z from azure_linux_images.db. Criteria: lowest critical -> high -> total vulnerabilities -> size. Top 10 per language._

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
| 1 | `mcr.microsoft.com/dotnet/runtime:8.0` | 8.0.22 | 1 | 5 | 89 | 193.0 MB | `sha256:732e7faf209c` |
| 2 | `mcr.microsoft.com/dotnet/aspnet:8.0` | 8.0.22 | 1 | 5 | 89 | 218.0 MB | `sha256:aa909f799cbd` |
| 3 | `mcr.microsoft.com/dotnet/sdk:8.0` | 8.0.416 | 1 | 18 | 172 | 850.0 MB | `sha256:240dc8202f4c` |

## Java

| Rank | Image | Version | Crit | High | Total | Size | Digest |
|------|-------|---------|------|------|-------|------|--------|
| 1 | `mcr.microsoft.com/openjdk/jdk:21-distroless` | 21.0.9 | 0 | 0 | 0 | 350.0 MB | `sha256:7093e5fbb349` |
| 2 | `mcr.microsoft.com/openjdk/jdk:21-azurelinux` | 21.0.9 | 0 | 0 | 0 | 482.0 MB | `sha256:53089b12f6f0` |
| 3 | `mcr.microsoft.com/openjdk/jdk:21-ubuntu` | 21.0.9 | 0 | 0 | 68 | 454.0 MB | `sha256:dd68c5ff7586` |

## Node

| Rank | Image | Version | Crit | High | Total | Size | Digest |
|------|-------|---------|------|------|-------|------|--------|
| 1 | `mcr.microsoft.com/azurelinux/base/nodejs:20` | 20.14.0 | 0 | 0 | 0 | 146.0 MB | `sha256:a8b923334dfc` |
| 2 | `mcr.microsoft.com/azurelinux/base/nodejs:20.14` | 20.14.0 | 0 | 0 | 0 | 146.0 MB | `sha256:a8b923334dfc` |
| 3 | `docker.io/library/node:20.0-slim` | 20.0.0 | 6 | 42 | 228 | 250.0 MB | `sha256:92ac19c7253d` |

## Perl

| Rank | Image | Version | Crit | High | Total | Size | Digest |
|------|-------|---------|------|------|-------|------|--------|
| 1 | `docker.io/library/python:3-slim` | 5.40.1 | 0 | 0 | 61 | 119.0 MB | `sha256:a6b1e1d4ae3e` |
| 2 | `docker.io/library/python:3.12-slim` | 5.40.1 | 0 | 0 | 62 | 119.0 MB | `sha256:7c5aeff4dbf9` |
| 3 | `mcr.microsoft.com/openjdk/jdk:21-ubuntu` | 5.34.0 | 0 | 0 | 68 | 454.0 MB | `sha256:dd68c5ff7586` |
| 4 | `mcr.microsoft.com/dotnet/runtime:8.0` | 5.36.0 | 1 | 5 | 89 | 193.0 MB | `sha256:732e7faf209c` |
| 5 | `mcr.microsoft.com/dotnet/aspnet:8.0` | 5.36.0 | 1 | 5 | 89 | 218.0 MB | `sha256:aa909f799cbd` |
| 6 | `mcr.microsoft.com/dotnet/sdk:8.0` | 5.36.0 | 1 | 18 | 172 | 850.0 MB | `sha256:240dc8202f4c` |
| 7 | `docker.io/library/node:20.0-slim` | 5.32.1 | 6 | 42 | 228 | 250.0 MB | `sha256:92ac19c7253d` |

## Python

| Rank | Image | Version | Crit | High | Total | Size | Digest |
|------|-------|---------|------|------|-------|------|--------|
| 1 | `mcr.microsoft.com/azurelinux/distroless/python:3` | 3.12.9 | 0 | 0 | 0 | 83.6 MB | `sha256:b01f14e07b99` |
| 2 | `mcr.microsoft.com/azurelinux/distroless/python:3-nonroot` | 3.12.9 | 0 | 0 | 0 | 83.6 MB | `sha256:c91d760bab8d` |
| 3 | `mcr.microsoft.com/azurelinux/distroless/python:3.12` | 3.12.9 | 0 | 0 | 0 | 83.6 MB | `sha256:b01f14e07b99` |
| 4 | `mcr.microsoft.com/azurelinux/distroless/python:3.12-nonroot` | 3.12.9 | 0 | 0 | 0 | 83.6 MB | `sha256:c91d760bab8d` |
| 5 | `mcr.microsoft.com/azurelinux/base/python:3` | 3.12.9 | 0 | 0 | 0 | 139.0 MB | `sha256:b834bbdd622c` |
| 6 | `mcr.microsoft.com/azurelinux/base/python:3.12` | 3.12.9 | 0 | 0 | 0 | 139.0 MB | `sha256:b834bbdd622c` |
| 7 | `mcr.microsoft.com/openjdk/jdk:21-azurelinux` | 3.12.9 | 0 | 0 | 0 | 482.0 MB | `sha256:53089b12f6f0` |
| 8 | `docker.io/library/python:3-slim` | 3.14.2 | 0 | 0 | 61 | 119.0 MB | `sha256:a6b1e1d4ae3e` |
| 9 | `docker.io/library/python:3.12-slim` | 3.12.12 | 0 | 0 | 62 | 119.0 MB | `sha256:7c5aeff4dbf9` |
