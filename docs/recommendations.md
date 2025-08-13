# Recommendations & Ranking Logic

Nightly recommendations are published to `docs/nightly_recommendations.md` to highlight the best candidate base images per detected language.

## Current Ranking Criteria (in order)
1. Lowest critical vulnerabilities
2. Lowest high vulnerabilities
3. Lowest total vulnerabilities
4. Smallest image size

Tie-breaking proceeds sequentially through the criteria. The top N (default 3) images per language are reported.

## Generation Script
Script: `scripts/generate_nightly_recommendations_md.py`

Responsibilities:
- Connects to the SQLite DB
- Groups images by detected language
- Computes vulnerability + size metrics
- Sorts using the criteria above
- Emits markdown table(s) to `docs/nightly_recommendations.md`

Adjustable parameters:
- `TOP_N` (constant inside the script) — change to widen/narrow the output set
- Potential to add flags for weighting or additional criteria (see below)

## Possible Enhancements
| Idea | Description | Notes |
| ---- | ----------- | ----- |
| Weighted scoring | Convert criteria into a composite score with adjustable weights | Allows nuanced trade-offs |
| Age / freshness | Prefer recently published or updated images | Requires reliable timestamp sourcing |
| Provenance / signature | Integrate image signing or SBOM attestation checks | Security supply chain boost |
| License compliance | Filter / rank by package license risk | Needs license extraction pass |
| CVE density | Normalize vulnerabilities per MB | Helps compare differently sized images |
| Stability channel | Distinguish LTS vs preview tags | Tag pattern heuristics |

## Customizing Locally
1. Open `scripts/generate_nightly_recommendations_md.py`
2. Adjust `TOP_N` or modify the sort key list
3. (Optional) Add new computed metrics to the query / in-memory aggregation
4. Re-run the script:
```bash
python scripts/generate_nightly_recommendations_md.py
```
5. Commit both the updated script and regenerated markdown if the logic change is intentional

## Extension Hooks (Future)
- CLI flag `--recommend-top N`
- Plugin interface allowing user-defined rankers
- JSON output variant for machine ingestion

---
See also: [Nightly Recommendations Markdown](nightly_recommendations.md) and [Database & Nightly Updates](database.md)
