#!/usr/bin/env python3
"""Generate a markdown summary of top recommended images per language.

The script queries the SQLite database (azure_linux_images.db) and for each
distinct language selects the top N (default 10) images with the fewest
critical/high/total vulnerabilities and smallest size.

Output written to docs/nightly_recommendations.md
"""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    from registry_scanner import MCRRegistryScanner
except ImportError:
    # Fallback if import fails
    MCRRegistryScanner = None

DB_PATH = Path("azure_linux_images.db")
OUTPUT_PATH = Path("docs/nightly_recommendations.md")
TOP_N = 10


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


def get_scanned_repositories_info() -> dict:
    """Get information about the repositories and images that were scanned.

    Returns a dict with repository and single image information, or empty dict if scanner unavailable.
    """
    if MCRRegistryScanner is None:
        return {}

    try:
        # Create a temporary scanner instance to get the repository list
        scanner = MCRRegistryScanner(
            db_path=str(DB_PATH),
            comprehensive_scan=False,
            cleanup_images=True,
            update_existing=False,
            max_tags_per_repo=5,
        )

        # Categorize the entries from repositories.txt
        repository_paths = []  # Repositories that enumerate tags
        single_images = []  # Full image references with tags

        for entry in scanner.image_patterns:
            # Determine if entry is a single image (has a tag component)
            is_single_image = ":" in entry.split("@")[0]  # ignore digest form for now

            if is_single_image:
                single_images.append(entry)
            else:
                # Format repository path for display
                if not entry.startswith("mcr.microsoft.com/"):
                    display_entry = f"mcr.microsoft.com/{entry}"
                else:
                    display_entry = entry
                repository_paths.append(display_entry)

        return {
            "repositories": repository_paths,
            "single_images": single_images,
            "repository_count": len(repository_paths),
            "single_image_count": len(single_images),
            "total_count": len(scanner.image_patterns),
        }
    except Exception:
        # If scanner fails, return empty info
        return {}


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

    # Get repository information
    repo_info = get_scanned_repositories_info()

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

            # Add repository information section
            if repo_info:
                f.write("## Scanned Repositories and Images\n\n")
                f.write(
                    f"This report includes analysis from **{repo_info.get('total_count', 0)} configured sources**:\n\n"
                )

                if repo_info.get("repositories"):
                    f.write(
                        f"### Repositories ({repo_info.get('repository_count', 0)} total)\n\n"
                    )
                    f.write(
                        "The following repositories were scanned with multiple tags enumerated:\n\n"
                    )
                    for repo in sorted(repo_info["repositories"]):
                        f.write(f"- `{repo}`\n")
                    f.write("\n")

                if repo_info.get("single_images"):
                    f.write(
                        f"### Single Images ({repo_info.get('single_image_count', 0)} total)\n\n"
                    )
                    f.write("The following specific image tags were scanned:\n\n")
                    for image in sorted(repo_info["single_images"]):
                        f.write(f"- `{image}`\n")
                    f.write("\n")

                f.write(
                    "_Note: Repository scans may include multiple tags per repository, while single images represent specific tagged images._\n\n"
                )
            else:
                f.write("## Scan Configuration\n\n")
                f.write(
                    "Repository and image scan details are configured in `config/repositories.txt`.\n\n"
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
