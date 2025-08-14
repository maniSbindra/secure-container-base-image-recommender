#!/usr/bin/env python3
"""Generate a markdown summary of top recommended images per language.

The script queries the SQLite database (azure_linux_images.db) and for each
distinct language selects the top N (default 3) images with the fewest
critical/high/total vulnerabilities and smallest size.

Output written to docs/nightly_recommendations.md
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("azure_linux_images.db")
OUTPUT_PATH = Path("docs/nightly_recommendations.md")
TOP_N = 6


def human_size(num_bytes: int | None) -> str:
    """Return a human-readable size string for a byte value."""
    if num_bytes is None:
        return "?"
    if num_bytes < 1024:
        return f"{num_bytes} B"
    mb = num_bytes / (1024 * 1024)
    if mb < 1024:
        return f"{mb:.1f} MB"
    gb = mb / 1024
    return f"{gb:.2f} GB"


def get_languages(conn: sqlite3.Connection) -> list[str]:
    """Return a sorted list of distinct languages present in the DB."""
    cur = conn.execute("SELECT DISTINCT language FROM languages ORDER BY language")
    return [row[0] for row in cur.fetchall() if row[0]]


def get_top_images_for_language(
    conn: sqlite3.Connection, language: str, top_n: int
) -> list[dict]:
    """Return top images for a language ordered by vuln severity then size."""
    sql = """
    SELECT i.name, l.version, i.total_vulnerabilities, i.critical_vulnerabilities,
           i.high_vulnerabilities, i.size_bytes
    FROM images i
    JOIN languages l ON i.id = l.image_id
    WHERE l.language = ?
    GROUP BY i.name, l.version
    ORDER BY i.critical_vulnerabilities ASC,
             i.high_vulnerabilities ASC,
             i.total_vulnerabilities ASC,
             i.size_bytes ASC
    LIMIT ?
    """
    cur = conn.execute(sql, (language, top_n))
    results = []
    for row in cur.fetchall():
        results.append(
            {
                "image": row[0],
                "version": row[1],
                "total": row[2],
                "critical": row[3],
                "high": row[4],
                "size": row[5],
            }
        )
    return results


def main() -> int:
    """Generate the nightly recommendations markdown file."""
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}, aborting markdown generation.")
        return 0
    conn = sqlite3.connect(str(DB_PATH))
    try:
        languages = get_languages(conn)
        if not languages:
            print("No languages found in database; markdown not generated.")
            return 0
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with OUTPUT_PATH.open("w", encoding="utf-8") as f:
            f.write("# Nightly Top Recommended Images by Language\n\n")
            f.write(
                f"_Generated: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')} from {DB_PATH.name}. Criteria: lowest critical -> high -> total vulnerabilities -> size. Top {TOP_N} per language._\n\n"
            )
            f.write(
                "**Note:** Image sizes are based on Linux amd64 platform as reported by `docker images` on GitHub runners. Actual sizes may vary significantly on other platforms (macOS, Windows, etc.).\n\n"
            )
            for language in languages:
                top_images = get_top_images_for_language(conn, language, TOP_N)
                if not top_images:
                    continue
                f.write(f"## {language.capitalize()}\n\n")
                f.write("| Rank | Image | Version | Crit | High | Total | Size |\n")
                f.write("|------|-------|---------|------|------|-------|------|\n")
                for idx, rec in enumerate(top_images, 1):
                    f.write(
                        f"| {idx} | `{rec['image']}` | {rec['version'] or ''} | {rec['critical']} | {rec['high']} | {rec['total']} | {human_size(rec['size'])} |\n"
                    )
                # Add single newline after each language section
                if language != languages[-1]:  # Not the last language
                    f.write("\n")

        print(f"Wrote nightly recommendations markdown to {OUTPUT_PATH}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
