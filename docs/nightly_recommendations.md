# Nightly Top Recommended Images by Language

_Generated: 2026-02-03T04:17:52.089531Z from azure_linux_images.db. Criteria: lowest critical -> high -> total vulnerabilities -> size. Top 10 per language._

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
| 1 | `mcr.microsoft.com/dotnet/runtime:8.0` | 8.0.23 | 3 | 5 | 103 | 193.0 MB | `sha256:d63a6fd96a4d` |
| 2 | `mcr.microsoft.com/dotnet/aspnet:8.0` | 8.0.23 | 3 | 5 | 103 | 218.0 MB | `sha256:4b8f0b085348` |
| 3 | `mcr.microsoft.com/dotnet/sdk:8.0` | 8.0.417 | 4 | 18 | 185 | 850.0 MB | `sha256:aa05b91be697` |

## Java

| Rank | Image | Version | Crit | High | Total | Size | Digest |
|------|-------|---------|------|------|-------|------|--------|
| 1 | `mcr.microsoft.com/openjdk/jdk:21-distroless` | 21.0.10 | 0 | 0 | 0 | 351.0 MB | `sha256:e856f44b3b6e` |
| 2 | `mcr.microsoft.com/openjdk/jdk:21-azurelinux` | 21.0.10 | 0 | 0 | 0 | 482.0 MB | `sha256:b1acde879fc1` |
| 3 | `mcr.microsoft.com/openjdk/jdk:21-ubuntu` | 21.0.10 | 0 | 0 | 67 | 476.0 MB | `sha256:572fdd27581e` |

## Node

| Rank | Image | Version | Crit | High | Total | Size | Digest |
|------|-------|---------|------|------|-------|------|--------|
| 1 | `mcr.microsoft.com/azurelinux/base/nodejs:20` | 20.14.0 | 0 | 0 | 0 | 146.0 MB | `sha256:0f0c0ac9ccc7` |
| 2 | `mcr.microsoft.com/azurelinux/base/nodejs:20.14` | 20.14.0 | 0 | 0 | 0 | 146.0 MB | `sha256:0f0c0ac9ccc7` |
| 3 | `docker.io/library/node:20.0-slim` | 20.0.0 | 6 | 49 | 246 | 250.0 MB | `sha256:702d475af4b8` |

## Perl

| Rank | Image | Version | Crit | High | Total | Size | Digest |
|------|-------|---------|------|------|-------|------|--------|
| 1 | `mcr.microsoft.com/openjdk/jdk:21-ubuntu` | 5.34.0 | 0 | 0 | 67 | 476.0 MB | `sha256:572fdd27581e` |
| 2 | `docker.io/library/python:3-slim` | 5.40.1 | 0 | 2 | 68 | 119.0 MB | `sha256:0c6bb259d537` |
| 3 | `docker.io/library/python:3.12-slim` | 5.40.1 | 0 | 2 | 69 | 119.0 MB | `sha256:4718a47de129` |
| 4 | `mcr.microsoft.com/dotnet/runtime:8.0` | 5.36.0 | 3 | 5 | 103 | 193.0 MB | `sha256:d63a6fd96a4d` |
| 5 | `mcr.microsoft.com/dotnet/aspnet:8.0` | 5.36.0 | 3 | 5 | 103 | 218.0 MB | `sha256:4b8f0b085348` |
| 6 | `mcr.microsoft.com/dotnet/sdk:8.0` | 5.36.0 | 4 | 18 | 185 | 850.0 MB | `sha256:aa05b91be697` |
| 7 | `docker.io/library/node:20.0-slim` | 5.32.1 | 6 | 49 | 246 | 250.0 MB | `sha256:702d475af4b8` |

## Python

| Rank | Image | Version | Crit | High | Total | Size | Digest |
|------|-------|---------|------|------|-------|------|--------|
| 1 | `mcr.microsoft.com/azurelinux/distroless/python:3` | 3.12.9 | 0 | 0 | 0 | 83.6 MB | `sha256:657bb43ad9ef` |
| 2 | `mcr.microsoft.com/azurelinux/distroless/python:3-nonroot` | 3.12.9 | 0 | 0 | 0 | 83.6 MB | `sha256:89458d69ad2e` |
| 3 | `mcr.microsoft.com/azurelinux/distroless/python:3.12` | 3.12.9 | 0 | 0 | 0 | 83.6 MB | `sha256:657bb43ad9ef` |
| 4 | `mcr.microsoft.com/azurelinux/distroless/python:3.12-nonroot` | 3.12.9 | 0 | 0 | 0 | 83.6 MB | `sha256:89458d69ad2e` |
| 5 | `mcr.microsoft.com/azurelinux/base/python:3` | 3.12.9 | 0 | 0 | 0 | 139.0 MB | `sha256:349502d7cedc` |
| 6 | `mcr.microsoft.com/azurelinux/base/python:3.12` | 3.12.9 | 0 | 0 | 0 | 139.0 MB | `sha256:349502d7cedc` |
| 7 | `mcr.microsoft.com/openjdk/jdk:21-azurelinux` | 3.12.9 | 0 | 0 | 0 | 482.0 MB | `sha256:b1acde879fc1` |
| 8 | `docker.io/library/python:3-slim` | 3.14.2 | 0 | 2 | 68 | 119.0 MB | `sha256:0c6bb259d537` |
| 9 | `docker.io/library/python:3.12-slim` | 3.12.12 | 0 | 2 | 69 | 119.0 MB | `sha256:4718a47de129` |
