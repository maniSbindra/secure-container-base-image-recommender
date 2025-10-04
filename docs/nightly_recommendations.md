# Nightly Top Recommended Images by Language

_Generated: 2025-10-04T02:51:29.502451Z from azure_linux_images.db. Criteria: lowest critical -> high -> total vulnerabilities -> size. Top 10 per language._

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

| Rank | Image | Version | Crit | High | Total | Size |
|------|-------|---------|------|------|-------|------|
| 1 | `mcr.microsoft.com/dotnet/runtime:8.0` | 8.0.20 | 1 | 4 | 81 | 193.0 MB |
| 2 | `mcr.microsoft.com/dotnet/aspnet:8.0` | 8.0.20 | 1 | 4 | 81 | 218.0 MB |
| 3 | `mcr.microsoft.com/dotnet/sdk:8.0` | 8.0.414 | 1 | 16 | 142 | 847.0 MB |

## Java

| Rank | Image | Version | Crit | High | Total | Size |
|------|-------|---------|------|------|-------|------|
| 1 | `mcr.microsoft.com/openjdk/jdk:21-distroless` | 21.0.8 | 0 | 0 | 0 | 351.0 MB |
| 2 | `mcr.microsoft.com/openjdk/jdk:21-azurelinux` | 21.0.8 | 0 | 0 | 0 | 483.0 MB |
| 3 | `mcr.microsoft.com/openjdk/jdk:21-ubuntu` | 21.0.8 | 0 | 0 | 94 | 444.0 MB |

## Node

| Rank | Image | Version | Crit | High | Total | Size |
|------|-------|---------|------|------|-------|------|
| 1 | `mcr.microsoft.com/azurelinux/base/nodejs:20` | 20.14.0 | 0 | 0 | 0 | 146.0 MB |
| 2 | `mcr.microsoft.com/azurelinux/base/nodejs:20.14` | 20.14.0 | 0 | 0 | 0 | 146.0 MB |
| 3 | `docker.io/library/node:20.0-slim` | 20.0.0 | 6 | 41 | 216 | 250.0 MB |

## Perl

| Rank | Image | Version | Crit | High | Total | Size |
|------|-------|---------|------|------|-------|------|
| 1 | `docker.io/library/python:3-slim` | 5.40.1 | 0 | 0 | 62 | 117.0 MB |
| 2 | `docker.io/library/python:3.12-slim` | 5.40.1 | 0 | 0 | 62 | 119.0 MB |
| 3 | `mcr.microsoft.com/openjdk/jdk:21-ubuntu` | 5.34.0 | 0 | 0 | 94 | 444.0 MB |
| 4 | `mcr.microsoft.com/dotnet/runtime:8.0` | 5.36.0 | 1 | 4 | 81 | 193.0 MB |
| 5 | `mcr.microsoft.com/dotnet/aspnet:8.0` | 5.36.0 | 1 | 4 | 81 | 218.0 MB |
| 6 | `mcr.microsoft.com/dotnet/sdk:8.0` | 5.36.0 | 1 | 16 | 142 | 847.0 MB |
| 7 | `docker.io/library/node:20.0-slim` | 5.32.1 | 6 | 41 | 216 | 250.0 MB |

## Python

| Rank | Image | Version | Crit | High | Total | Size |
|------|-------|---------|------|------|-------|------|
| 1 | `mcr.microsoft.com/azurelinux/distroless/python:3` | 3.12.9 | 0 | 0 | 0 | 83.9 MB |
| 2 | `mcr.microsoft.com/azurelinux/distroless/python:3-nonroot` | 3.12.9 | 0 | 0 | 0 | 83.9 MB |
| 3 | `mcr.microsoft.com/azurelinux/distroless/python:3.12` | 3.12.9 | 0 | 0 | 0 | 83.9 MB |
| 4 | `mcr.microsoft.com/azurelinux/distroless/python:3.12-nonroot` | 3.12.9 | 0 | 0 | 0 | 83.9 MB |
| 5 | `mcr.microsoft.com/azurelinux/base/python:3` | 3.12.9 | 0 | 0 | 0 | 139.0 MB |
| 6 | `mcr.microsoft.com/azurelinux/base/python:3.12` | 3.12.9 | 0 | 0 | 0 | 139.0 MB |
| 7 | `mcr.microsoft.com/openjdk/jdk:21-azurelinux` | 3.12.9 | 0 | 0 | 0 | 483.0 MB |
| 8 | `docker.io/library/python:3-slim` | 3.13.7 | 0 | 0 | 62 | 117.0 MB |
| 9 | `docker.io/library/python:3.12-slim` | 3.12.11 | 0 | 0 | 62 | 119.0 MB |
