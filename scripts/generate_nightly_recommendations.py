"""Generate a markdown summary of top recommended images per language.

This script is intended to run in CI after the nightly scan updates the
SQLite database. It produces docs/nightly_recommendations.md with a table
for each detected language showing the top images ranked primarily by
security (critical/high/total vulnerabilities) and then by size.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

DB_PATH = os.environ.get("IMAGE_DB", "azure_linux_images.db")
OUTPUT_PATH = Path("docs/nightly_recommendations.md")
TOP_N = int(os.environ.get("TOP_N_PER_LANGUAGE", "10"))


def query_languages(conn: sqlite3.Connection) -> List[str]:
    """Return distinct languages (lowercased) from database."""
    cur = conn.execute(
        "SELECT DISTINCT LOWER(language) FROM languages ORDER BY LOWER(language)"
    )
    return [row[0] for row in cur.fetchall()]


def query_top_images(conn: sqlite3.Connection, language: str) -> List[Tuple]:
    """Return ranked image tuples for a given language."""
    # Order by critical, high, total vulns, then size ascending
    cur = conn.execute(
        """
        SELECT i.name, l.version, i.critical_vulnerabilities, i.high_vulnerabilities,
               i.total_vulnerabilities, COALESCE(i.size_bytes,0), i.digest
        FROM images i
        JOIN languages l ON i.id = l.image_id
        WHERE LOWER(l.language) = ?
        GROUP BY i.id, l.version
        ORDER BY i.critical_vulnerabilities ASC,
                 i.high_vulnerabilities ASC,
                 i.total_vulnerabilities ASC,
                 COALESCE(i.size_bytes, 0) ASC
        LIMIT ?
        """,
        (language.lower(), TOP_N),
    )
    return cur.fetchall()


def human_size(num_bytes: int) -> str:
    """Return human readable size in MB or '-' if size not positive."""
    if num_bytes <= 0:
        return "-"
    return f"{num_bytes / (1024*1024):.1f} MB"


def format_digest(digest: str | None) -> str:
    """Return a formatted digest string, shortened for display.

    Shows the first 12 characters of the hash after the 'sha256:' prefix.
    """
    if not digest:
        return ""
    # If digest starts with sha256:, show abbreviated form
    if digest.startswith("sha256:"):
        hash_part = digest[7:]  # Remove 'sha256:' prefix
        return f"sha256:{hash_part[:12]}"
    # For other formats, show first 19 characters
    return digest[:19]


def main():
    """Entry point: build and write nightly recommendations markdown."""
    if not os.path.exists(DB_PATH):
        raise SystemExit(f"Database not found at {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    try:
        languages = query_languages(conn)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        lines = []
        lines.append("# Nightly Recommended Images by Language")
        lines.append("")
        lines.append(f"_Generated: {ts}_")
        lines.append("")
        lines.append(
            "The tables below list the top images per language prioritized by minimal critical/high vulnerabilities, then total vulnerabilities, then image size."
        )
        lines.append("")
        lines.append(
            "**Note:** Image sizes are based on Linux amd64 platform as reported by `docker images` on GitHub runners. Actual sizes may vary significantly on other platforms (macOS, Windows, etc.)."
        )
        lines.append("")

        if not languages:
            lines.append("No languages detected in the current database.")
        else:
            for lang in languages:
                rows = query_top_images(conn, lang)
                if not rows:
                    continue
                lines.append(f"## {lang.title()}")
                lines.append("")
                lines.append(
                    "| Rank | Image | Version | Critical | High | Total | Size | Digest |"
                )
                lines.append(
                    "|------|-------|---------|----------|------|-------|------|--------|"
                )
                for idx, (
                    name,
                    version,
                    crit,
                    high,
                    total,
                    size_bytes,
                    digest,
                ) in enumerate(rows, start=1):
                    version_display = version or "-"
                    lines.append(
                        f"| {idx} | `{name}` | {version_display} | {crit} | {high} | {total} | {human_size(size_bytes)} | `{format_digest(digest)}` |"
                    )
                lines.append("")

        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Wrote nightly recommendations to {OUTPUT_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
