# Nightly Top Recommended Images by Language

_Generated: 2026-02-08T04:36:02.024828Z from azure_linux_images.db. Criteria: lowest critical -> high -> total vulnerabilities -> size. Top 10 per language._

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
| 1 | `mcr.microsoft.com/dotnet/runtime:8.0` | 8.0.23 | 1 | 2 | 86 | 193.0 MB | `sha256:523b82daf080` |
| 2 | `mcr.microsoft.com/dotnet/aspnet:8.0` | 8.0.23 | 1 | 2 | 86 | 218.0 MB | `sha256:0d4a76c0a692` |
| 3 | `mcr.microsoft.com/dotnet/sdk:8.0` | 8.0.417 | 2 | 15 | 168 | 850.0 MB | `sha256:1682f3cd0cb5` |

## Java

| Rank | Image | Version | Crit | High | Total | Size | Digest |
|------|-------|---------|------|------|-------|------|--------|
| 1 | `mcr.microsoft.com/openjdk/jdk:21-azurelinux` | 21.0.10 | 0 | 0 | 0 | 491.0 MB | `sha256:7e28ea3b1b26` |
| 2 | `mcr.microsoft.com/openjdk/jdk:21-ubuntu` | 21.0.10 | 0 | 0 | 64 | 476.0 MB | `sha256:1ac8d30af0bb` |
| 3 | `mcr.microsoft.com/openjdk/jdk:21-distroless` | 21.0.10 | 2 | 2 | 21 | 351.0 MB | `sha256:6d83b53c8fb9` |

## Node

| Rank | Image | Version | Crit | High | Total | Size | Digest |
|------|-------|---------|------|------|-------|------|--------|
| 1 | `mcr.microsoft.com/azurelinux/base/nodejs:20` | 20.14.0 | 2 | 6 | 30 | 146.0 MB | `sha256:0f0c0ac9ccc7` |
| 2 | `mcr.microsoft.com/azurelinux/base/nodejs:20.14` | 20.14.0 | 2 | 6 | 30 | 146.0 MB | `sha256:0f0c0ac9ccc7` |
| 3 | `docker.io/library/node:20.0-slim` | 20.0.0 | 6 | 50 | 246 | 250.0 MB | `sha256:702d475af4b8` |

## Perl

| Rank | Image | Version | Crit | High | Total | Size | Digest |
|------|-------|---------|------|------|-------|------|--------|
| 1 | `mcr.microsoft.com/openjdk/jdk:21-ubuntu` | 5.34.0 | 0 | 0 | 64 | 476.0 MB | `sha256:1ac8d30af0bb` |
| 2 | `docker.io/library/python:3-slim` | 5.40.1 | 0 | 2 | 68 | 119.0 MB | `sha256:486b8092bfb1` |
| 3 | `docker.io/library/python:3.12-slim` | 5.40.1 | 0 | 2 | 69 | 119.0 MB | `sha256:9e01bf1ae5db` |
| 4 | `mcr.microsoft.com/dotnet/runtime:8.0` | 5.36.0 | 1 | 2 | 86 | 193.0 MB | `sha256:523b82daf080` |
| 5 | `mcr.microsoft.com/dotnet/aspnet:8.0` | 5.36.0 | 1 | 2 | 86 | 218.0 MB | `sha256:0d4a76c0a692` |
| 6 | `mcr.microsoft.com/dotnet/sdk:8.0` | 5.36.0 | 2 | 15 | 168 | 850.0 MB | `sha256:1682f3cd0cb5` |
| 7 | `docker.io/library/node:20.0-slim` | 5.32.1 | 6 | 50 | 246 | 250.0 MB | `sha256:702d475af4b8` |

## Python

| Rank | Image | Version | Crit | High | Total | Size | Digest |
|------|-------|---------|------|------|-------|------|--------|
| 1 | `mcr.microsoft.com/openjdk/jdk:21-azurelinux` | 3.12.9 | 0 | 0 | 0 | 491.0 MB | `sha256:7e28ea3b1b26` |
| 2 | `docker.io/library/python:3-slim` | 3.14.3 | 0 | 2 | 68 | 119.0 MB | `sha256:486b8092bfb1` |
| 3 | `docker.io/library/python:3.12-slim` | 3.12.12 | 0 | 2 | 69 | 119.0 MB | `sha256:9e01bf1ae5db` |
| 4 | `mcr.microsoft.com/azurelinux/distroless/python:3` | 3.12.9 | 2 | 2 | 20 | 83.6 MB | `sha256:657bb43ad9ef` |
| 5 | `mcr.microsoft.com/azurelinux/distroless/python:3-nonroot` | 3.12.9 | 2 | 2 | 20 | 83.6 MB | `sha256:89458d69ad2e` |
| 6 | `mcr.microsoft.com/azurelinux/distroless/python:3.12` | 3.12.9 | 2 | 2 | 20 | 83.6 MB | `sha256:657bb43ad9ef` |
| 7 | `mcr.microsoft.com/azurelinux/distroless/python:3.12-nonroot` | 3.12.9 | 2 | 2 | 20 | 83.6 MB | `sha256:89458d69ad2e` |
| 8 | `mcr.microsoft.com/azurelinux/base/python:3` | 3.12.9 | 2 | 2 | 20 | 139.0 MB | `sha256:349502d7cedc` |
| 9 | `mcr.microsoft.com/azurelinux/base/python:3.12` | 3.12.9 | 2 | 2 | 20 | 139.0 MB | `sha256:349502d7cedc` |
