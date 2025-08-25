# Nightly Top Recommended Images by Language

_Generated: 2025-08-25T03:18:35.392705Z from azure_linux_images.db. Criteria: lowest critical -> high -> total vulnerabilities -> size. Top 10 per language._

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
| 1 | `mcr.microsoft.com/dotnet/runtime:8.0` | 8.0.19 | 1 | 7 | 83 | 193.0 MB |
| 2 | `mcr.microsoft.com/dotnet/aspnet:8.0` | 8.0.19 | 1 | 7 | 83 | 218.0 MB |
| 3 | `mcr.microsoft.com/dotnet/sdk:8.0` | 8.0.413 | 1 | 23 | 150 | 847.0 MB |

## Java

| Rank | Image | Version | Crit | High | Total | Size |
|------|-------|---------|------|------|-------|------|
| 1 | `mcr.microsoft.com/openjdk/jdk:21-distroless` | 21.0.8 | 0 | 0 | 0 | 341.0 MB |
| 2 | `mcr.microsoft.com/openjdk/jdk:21-azurelinux` | 21.0.8 | 0 | 0 | 0 | 474.0 MB |
| 3 | `mcr.microsoft.com/openjdk/jdk:21-ubuntu` | 21.0.8 | 0 | 0 | 52 | 447.0 MB |

## Node

| Rank | Image | Version | Crit | High | Total | Size |
|------|-------|---------|------|------|-------|------|
| 1 | `mcr.microsoft.com/azurelinux/base/nodejs:20` | 20.14.0 | 0 | 0 | 0 | 146.0 MB |
| 2 | `mcr.microsoft.com/azurelinux/base/nodejs:20.14` | 20.14.0 | 0 | 0 | 0 | 146.0 MB |
| 3 | `docker.io/library/node:20.0-slim` | 20.0.0 | 6 | 41 | 215 | 250.0 MB |

## Perl

| Rank | Image | Version | Crit | High | Total | Size |
|------|-------|---------|------|------|-------|------|
| 1 | `docker.io/library/python:3-slim` | 5.40.1 | 0 | 0 | 51 | 117.0 MB |
| 2 | `docker.io/library/python:3.12-slim` | 5.40.1 | 0 | 0 | 51 | 119.0 MB |
| 3 | `mcr.microsoft.com/openjdk/jdk:21-ubuntu` | 5.34.0 | 0 | 0 | 52 | 447.0 MB |
| 4 | `mcr.microsoft.com/dotnet/runtime:8.0` | 5.36.0 | 1 | 7 | 83 | 193.0 MB |
| 5 | `mcr.microsoft.com/dotnet/aspnet:8.0` | 5.36.0 | 1 | 7 | 83 | 218.0 MB |
| 6 | `mcr.microsoft.com/dotnet/sdk:8.0` | 5.36.0 | 1 | 23 | 150 | 847.0 MB |
| 7 | `docker.io/library/node:20.0-slim` | 5.32.1 | 6 | 41 | 215 | 250.0 MB |

## Python

| Rank | Image | Version | Crit | High | Total | Size |
|------|-------|---------|------|------|-------|------|
| 1 | `mcr.microsoft.com/azurelinux/distroless/python:3` | 3.12.9 | 0 | 0 | 0 | 83.8 MB |
| 2 | `mcr.microsoft.com/azurelinux/distroless/python:3-nonroot` | 3.12.9 | 0 | 0 | 0 | 83.8 MB |
| 3 | `mcr.microsoft.com/azurelinux/distroless/python:3.12` | 3.12.9 | 0 | 0 | 0 | 83.8 MB |
| 4 | `mcr.microsoft.com/azurelinux/distroless/python:3.12-nonroot` | 3.12.9 | 0 | 0 | 0 | 83.8 MB |
| 5 | `mcr.microsoft.com/azurelinux/base/python:3` | 3.12.9 | 0 | 0 | 0 | 138.0 MB |
| 6 | `mcr.microsoft.com/azurelinux/base/python:3.12` | 3.12.9 | 0 | 0 | 0 | 138.0 MB |
| 7 | `mcr.microsoft.com/openjdk/jdk:21-azurelinux` | 3.12.9 | 0 | 0 | 0 | 474.0 MB |
| 8 | `docker.io/library/python:3-slim` | 3.13.7 | 0 | 0 | 51 | 117.0 MB |
| 9 | `docker.io/library/python:3.12-slim` | 3.12.11 | 0 | 0 | 51 | 119.0 MB |
