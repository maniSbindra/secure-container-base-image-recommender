# Database & Nightly Update Details

This project maintains a pre-scanned SQLite database (`azure_linux_images.db`) that is refreshed nightly to keep vulnerability data and image metadata current.

## Nightly Workflow Overview

Steps performed by the scheduled GitHub Actions job:
1. Run comprehensive scan: `--scan --comprehensive --update-existing --max-tags 0`
2. Update / insert new image metadata, packages, vulnerabilities
3. Commit updated `azure_linux_images.db` via Git LFS (only if changed)
4. Generate nightly recommendations markdown (see `recommendations.md`)

Only the SQLite database is persisted; the legacy JSON export is intentionally skipped to avoid bloat and redundancy.

**Important:** Image sizes are collected using `docker images` on Linux amd64 (GitHub runners) and may differ significantly on other platforms. When scanning locally on macOS, Windows, or ARM systems, size values will reflect the local platform.

## Why Git LFS?

Daily binary diffs would quickly inflate repository size. Git LFS stores lightweight pointers in Git history and fetches the binary object on demand, keeping clones fast.

## Minimal (Empty) DB Fallback

If you clone without Git LFS installed you will get a pointer text file. The application automatically detects this condition and creates an empty schema so you can still perform scans or run tests.

Example warning:
```
⚠️  Detected Git LFS pointer instead of actual SQLite DB: azure_linux_images.db
   Run 'git lfs install && git lfs pull' to download the full database, or proceed with empty DB.
```

## Getting the Full Pre-Scanned Database

Fresh clone with LFS:
```bash
git lfs install
git clone https://github.com/<owner>/<repo>.git
cd <repo>
git lfs pull
```

Already cloned:
```bash
git lfs install
git lfs pull
```

## Regenerating Locally (Optional)

You can rebuild the database from scratch (starts empty, then populated):
```bash
python src/cli.py --scan --comprehensive --update-existing --max-tags 10 --database azure_linux_images.json
```
Increase or set `--max-tags 0` to scan all tags (can be slow on large repos).

## Troubleshooting

| Symptom | Cause | Fix |
| ------- | ----- | --- |
| DB file very small (< 2KB) | LFS pointer only | Run `git lfs pull` |
| No images returned | Empty freshly created DB | Run a scan (`--scan`) or pull LFS version |
| Slow scan | Large tag enumeration | Adjust `--max-tags` |
| Missing vulnerabilities | Non-comprehensive scan | Re-run with `--comprehensive` |

## Future Ideas

- Optional compression of historical DB snapshots
- Delta diff export for CI consumption
- Automated pruning of stale image records

---
See also: [Recommendations & Ranking Logic](recommendations.md)
