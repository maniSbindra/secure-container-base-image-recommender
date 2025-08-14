"""
Database module for Azure Linux Base Image Registry

This module handles SQLite database operations for storing and querying
container image analysis data with vulnerability information.
"""

import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class ImageDatabase:
    """SQLite database for container image analysis data"""

    def __init__(self, db_path: str = "azure_linux_images.db"):
        self.db_path = db_path
        self.conn = None
        self._initialize_database()

    def _initialize_database(self):
        """Initialize database connection and create tables if they don't exist"""
        # Detect if the file looks like a Git LFS pointer (text file with version & oid)
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "rb") as f:
                    head = f.read(200)
                # Heuristic: LFS pointer files are small and start with 'version https://git-lfs.github.com/spec/v1' and contain 'oid sha256:'
                if (
                    b"version https://git-lfs.github.com/spec/v1" in head
                    and b"oid sha256:" in head
                ):
                    print(
                        "⚠️  Detected Git LFS pointer instead of actual SQLite DB:",
                        self.db_path,
                    )
                    print(
                        "   Run 'git lfs install && git lfs pull' to download the full database, or proceed with empty DB."
                    )
            except Exception as e:
                print(f"⚠️  Could not inspect database file for LFS pointer: {e}")

        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        self._create_tables()
        self._create_indexes()

        # Verify constraints are in place
        self.verify_table_constraints()

    def _create_tables(self):
        """Create database tables"""

        # Main images table with vulnerability counts and security analysis
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                registry TEXT NOT NULL,
                repository TEXT NOT NULL,
                tag TEXT NOT NULL,
                digest TEXT,
                size_bytes INTEGER,
                layers INTEGER,
                created_date TEXT,
                scan_timestamp TEXT NOT NULL,
                base_os_name TEXT,
                base_os_version TEXT,
                total_vulnerabilities INTEGER DEFAULT 0,
                critical_vulnerabilities INTEGER DEFAULT 0,
                high_vulnerabilities INTEGER DEFAULT 0,
                medium_vulnerabilities INTEGER DEFAULT 0,
                low_vulnerabilities INTEGER DEFAULT 0,
                negligible_vulnerabilities INTEGER DEFAULT 0,
                unknown_vulnerabilities INTEGER DEFAULT 0,
                vulnerability_scan_timestamp TEXT,
                vulnerability_scanner TEXT,
                secrets_found INTEGER DEFAULT 0,
                config_issues INTEGER DEFAULT 0,
                license_issues INTEGER DEFAULT 0,
                comprehensive_scan_timestamp TEXT,
                comprehensive_scanner TEXT,
                CONSTRAINT unique_image_location UNIQUE (registry, repository, tag)
            )
        """
        )

        # Languages table
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS languages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL,
                language TEXT NOT NULL,
                version TEXT,
                major_minor TEXT,
                package_name TEXT,
                package_type TEXT,
                architecture TEXT,
                vendor TEXT,
                verified BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (image_id) REFERENCES images (id) ON DELETE CASCADE
            )
        """
        )

        # Package managers table
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS package_managers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                version TEXT,
                language TEXT,
                FOREIGN KEY (image_id) REFERENCES images (id) ON DELETE CASCADE
            )
        """
        )

        # Capabilities table
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS capabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL,
                capability TEXT NOT NULL,
                FOREIGN KEY (image_id) REFERENCES images (id) ON DELETE CASCADE
            )
        """
        )

        # System packages table
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS system_packages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                version TEXT,
                package_type TEXT,
                FOREIGN KEY (image_id) REFERENCES images (id) ON DELETE CASCADE
            )
        """
        )

        # Detailed vulnerabilities table (optional for detailed tracking)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS vulnerabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL,
                vulnerability_id TEXT NOT NULL,
                severity TEXT NOT NULL,
                package_name TEXT,
                package_version TEXT,
                fixed_version TEXT,
                description TEXT,
                cvss_score REAL,
                FOREIGN KEY (image_id) REFERENCES images (id) ON DELETE CASCADE
            )
        """
        )

        # Security findings table (for Trivy comprehensive scan results)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS security_findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL,
                finding_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                rule_id TEXT,
                title TEXT,
                description TEXT,
                file_path TEXT,
                category TEXT,
                message TEXT,
                FOREIGN KEY (image_id) REFERENCES images (id) ON DELETE CASCADE
            )
        """
        )

        self.conn.commit()

    def _create_indexes(self):
        """Create database indexes for performance"""

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_images_name ON images(name)",
            "CREATE INDEX IF NOT EXISTS idx_images_registry ON images(registry)",
            "CREATE INDEX IF NOT EXISTS idx_images_vulnerabilities ON images(total_vulnerabilities, critical_vulnerabilities, high_vulnerabilities)",
            "CREATE INDEX IF NOT EXISTS idx_languages_lang_version ON languages(language, version)",
            "CREATE INDEX IF NOT EXISTS idx_languages_image_id ON languages(image_id)",
            "CREATE INDEX IF NOT EXISTS idx_capabilities_capability ON capabilities(capability)",
            "CREATE INDEX IF NOT EXISTS idx_capabilities_image_id ON capabilities(image_id)",
            "CREATE INDEX IF NOT EXISTS idx_vulnerabilities_severity ON vulnerabilities(severity)",
            "CREATE INDEX IF NOT EXISTS idx_vulnerabilities_image_id ON vulnerabilities(image_id)",
            "CREATE INDEX IF NOT EXISTS idx_security_findings_type ON security_findings(finding_type)",
            "CREATE INDEX IF NOT EXISTS idx_security_findings_severity ON security_findings(severity)",
            "CREATE INDEX IF NOT EXISTS idx_security_findings_image_id ON security_findings(image_id)",
        ]

        for index_sql in indexes:
            self.conn.execute(index_sql)

        self.conn.commit()

    def verify_table_constraints(self) -> bool:
        """Verify that the images table has the proper unique constraints"""
        try:
            cursor = self.conn.execute("PRAGMA table_info(images)")
            columns = {row[1]: row for row in cursor.fetchall()}

            # Check if name column exists and is unique
            if "name" not in columns:
                print("⚠️  Warning: 'name' column not found in images table")
                return False

            # Check table constraints
            cursor = self.conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='images'"
            )
            table_sql = cursor.fetchone()
            if table_sql:
                sql = table_sql[0]
                has_name_unique = "name TEXT UNIQUE" in sql
                has_composite_unique = (
                    "unique_image_location UNIQUE (registry, repository, tag)"
                    in sql.lower()
                )

                print("📊 Database constraint status:")
                print(f"   Name uniqueness: {'✅' if has_name_unique else '❌'}")
                print(
                    f"   Composite uniqueness: {'✅' if has_composite_unique else '❌'}"
                )

                return has_name_unique

            return False
        except Exception as e:
            print(f"⚠️  Could not verify table constraints: {e}")
            return False

    def image_exists(self, image_name: str) -> bool:
        """Check if an image already exists in the database"""
        cursor = self.conn.execute(
            "SELECT 1 FROM images WHERE name = ? LIMIT 1", (image_name,)
        )
        return cursor.fetchone() is not None

    def get_image_scan_info(self, image_name: str) -> Optional[Dict]:
        """Get basic scan information for an existing image"""
        cursor = self.conn.execute(
            """SELECT name, scan_timestamp, total_vulnerabilities,
                      vulnerability_scan_timestamp, comprehensive_scanner
               FROM images WHERE name = ? LIMIT 1""",
            (image_name,),
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def check_image_needs_update(self, analysis_data: Dict) -> Tuple[bool, str]:
        """
        Check if an image needs to be updated based on existing data.
        Returns (needs_update, reason)
        """
        image_name = analysis_data["image"]

        # Check if image exists
        existing_info = self.get_image_scan_info(image_name)
        if not existing_info:
            return True, "Image does not exist in database"

        # Compare timestamps to see if this is newer data
        new_scan_timestamp = analysis_data.get("analysis_timestamp")
        existing_scan_timestamp = existing_info.get("scan_timestamp")

        if new_scan_timestamp and existing_scan_timestamp:
            try:
                from datetime import datetime

                new_dt = datetime.fromisoformat(
                    new_scan_timestamp.replace("Z", "+00:00")
                )
                existing_dt = datetime.fromisoformat(
                    existing_scan_timestamp.replace("Z", "+00:00")
                )

                if new_dt <= existing_dt:
                    return (
                        False,
                        f"Existing scan is newer or same ({existing_scan_timestamp} >= {new_scan_timestamp})",
                    )
            except (ValueError, AttributeError):
                # If we can't parse timestamps, allow the update
                pass

        # Check if vulnerability data has changed significantly
        new_vuln_total = analysis_data.get("vulnerabilities", {}).get("total", 0)
        existing_vuln_total = existing_info.get("total_vulnerabilities", 0)

        if abs(new_vuln_total - existing_vuln_total) > 0:
            return (
                True,
                f"Vulnerability count changed ({existing_vuln_total} -> {new_vuln_total})",
            )

        # Allow update if we have new comprehensive security data
        if analysis_data.get("comprehensive_security"):
            return True, "New comprehensive security data available"

        return True, "Updating with latest scan data"

    def insert_image_analysis(
        self, analysis_data: Dict, force_update: bool = False
    ) -> int:
        """
        Insert image analysis data and return image ID.

        Args:
            analysis_data: The image analysis data to insert
            force_update: If True, always update existing images. If False, use smart duplicate prevention.
        """

        # Extract image name components
        image_name = analysis_data["image"]

        # Check if we need to update this image (unless forced)
        if not force_update:
            needs_update, reason = self.check_image_needs_update(analysis_data)
            if not needs_update:
                print(f"    ⏭️  Skipping {image_name}: {reason}")
                # Return existing image ID
                existing_info = self.get_image_scan_info(image_name)
                if existing_info:
                    cursor = self.conn.execute(
                        "SELECT id FROM images WHERE name = ?", (image_name,)
                    )
                    row = cursor.fetchone()
                    return row["id"] if row else None

            print(f"    🔄 Updating {image_name}: {reason}")
        else:
            print(f"    🔄 Force updating {image_name} (--update-existing mode)")

        registry, repository, tag = self._parse_image_name(image_name)

        # Extract manifest data
        manifest = analysis_data.get("manifest", {})

        # Extract base OS data
        base_os = analysis_data.get("base_os", {})

        # Extract vulnerability data if available
        vulnerabilities = analysis_data.get("vulnerabilities", {})

        # Extract comprehensive security data if available
        comprehensive_security = analysis_data.get("comprehensive_security", {})

        # Prepare the data for insertion with proper type conversion
        layers_value = manifest.get("layers", 0)
        if isinstance(layers_value, list):
            print(
                f"    🐛 DEBUG: layers is a list: {layers_value}, converting to count"
            )
            layers_value = len(layers_value)
        elif not isinstance(layers_value, (int, float)):
            print(
                f"    🐛 DEBUG: layers is not a number: {layers_value} (type: {type(layers_value)}), setting to 0"
            )
            layers_value = 0

        size_value = manifest.get("size", 0)
        if not isinstance(size_value, (int, float)):
            size_value = 0

        # Additional check: Look for 'layers' anywhere in the analysis data
        for key, value in analysis_data.items():
            if key == "layers" and isinstance(value, list):
                print(
                    f"    🐛 DEBUG: Found 'layers' as list in analysis_data['{key}']: {value}"
                )
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if subkey == "layers" and isinstance(subvalue, list):
                        print(
                            f"    🐛 DEBUG: Found 'layers' as list in analysis_data['{key}']['{subkey}']: {subvalue}"
                        )

        # Debug logging for critical issues only
        print(f"    🔍 Attempting database insertion for {image_name}")

        params = [
            image_name,  # 0
            registry,  # 1
            repository,  # 2
            tag,  # 3
            str(manifest.get("digest", "")) if manifest.get("digest") else None,  # 4
            int(size_value),  # 5
            int(layers_value),  # 6 - This is the problematic one
            str(manifest.get("created", "")),  # 7
            analysis_data.get("analysis_timestamp", datetime.now().isoformat()),  # 8
            str(base_os.get("name", "")) if base_os.get("name") else None,  # 9
            str(base_os.get("version", "")) if base_os.get("version") else None,  # 10
            int(vulnerabilities.get("total", 0)),  # 11
            int(vulnerabilities.get("critical", 0)),  # 12
            int(vulnerabilities.get("high", 0)),  # 13
            int(vulnerabilities.get("medium", 0)),  # 14
            int(vulnerabilities.get("low", 0)),  # 15
            int(vulnerabilities.get("negligible", 0)),  # 16
            int(vulnerabilities.get("unknown", 0)),  # 17
            (
                str(vulnerabilities.get("scan_timestamp", ""))
                if vulnerabilities.get("scan_timestamp")
                else None
            ),  # 18
            (
                str(vulnerabilities.get("scanner", ""))
                if vulnerabilities.get("scanner")
                else None
            ),  # 19
            int(comprehensive_security.get("secrets_found", 0)),  # 20
            int(comprehensive_security.get("config_issues", 0)),  # 21
            int(comprehensive_security.get("license_issues", 0)),  # 22
            (
                str(comprehensive_security.get("scan_timestamp", ""))
                if comprehensive_security.get("scan_timestamp")
                else None
            ),  # 23
            (
                str(comprehensive_security.get("scanner", ""))
                if comprehensive_security.get("scanner")
                else None
            ),  # 24
        ]

        # Check for any list types in parameters
        for i, param in enumerate(params):
            if isinstance(param, list):
                print(f"    🐛 DEBUG: Parameter {i} is a list: {param}")
                print(f"    🐛 Manifest data: {manifest}")
                raise ValueError(f"Parameter {i} should not be a list: {param}")

        # Create a fresh, clean parameter list right before execution to avoid any mutation issues
        clean_params = [
            str(params[0]),  # 0: image_name
            str(params[1]),  # 1: registry
            str(params[2]),  # 2: repository
            str(params[3]),  # 3: tag
            params[4] if params[4] is not None else None,  # 4: digest
            int(params[5]) if params[5] is not None else 0,  # 5: size_bytes
            int(params[6]) if params[6] is not None else 0,  # 6: layers
            str(params[7]) if params[7] is not None else "",  # 7: created_date
            str(params[8]),  # 8: scan_timestamp
            params[9] if params[9] is not None else None,  # 9: base_os_name
            params[10] if params[10] is not None else None,  # 10: base_os_version
            int(params[11]),  # 11: total_vulnerabilities
            int(params[12]),  # 12: critical_vulnerabilities
            int(params[13]),  # 13: high_vulnerabilities
            int(params[14]),  # 14: medium_vulnerabilities
            int(params[15]),  # 15: low_vulnerabilities
            int(params[16]),  # 16: negligible_vulnerabilities
            int(params[17]),  # 17: unknown_vulnerabilities
            (
                params[18] if params[18] is not None else None
            ),  # 18: vulnerability_scan_timestamp
            params[19] if params[19] is not None else None,  # 19: vulnerability_scanner
            int(params[20]),  # 20: secrets_found
            int(params[21]),  # 21: config_issues
            int(params[22]),  # 22: license_issues
            (
                params[23] if params[23] is not None else None
            ),  # 23: comprehensive_scan_timestamp
            params[24] if params[24] is not None else None,  # 24: comprehensive_scanner
        ]

        # Insert main image record with proper error handling
        try:
            # Try to insert new record
            cursor = self.conn.execute(
                """
                INSERT INTO images (
                    name, registry, repository, tag, digest, size_bytes, layers,
                    created_date, scan_timestamp, base_os_name, base_os_version,
                    total_vulnerabilities, critical_vulnerabilities, high_vulnerabilities,
                    medium_vulnerabilities, low_vulnerabilities, negligible_vulnerabilities,
                    unknown_vulnerabilities, vulnerability_scan_timestamp, vulnerability_scanner,
                    secrets_found, config_issues, license_issues,
                    comprehensive_scan_timestamp, comprehensive_scanner
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                clean_params,
            )

            image_id = cursor.lastrowid
            print(f"    ✅ New image inserted with ID: {image_id}")

        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                # Handle duplicate entry
                print("    🔄 Image already exists, updating existing record...")
                # Update existing record
                cursor = self.conn.execute(
                    """
                    UPDATE images SET
                        name = ?, digest = ?, size_bytes = ?, layers = ?,
                        created_date = ?, scan_timestamp = ?, base_os_name = ?, base_os_version = ?,
                        total_vulnerabilities = ?, critical_vulnerabilities = ?, high_vulnerabilities = ?,
                        medium_vulnerabilities = ?, low_vulnerabilities = ?, negligible_vulnerabilities = ?,
                        unknown_vulnerabilities = ?, vulnerability_scan_timestamp = ?, vulnerability_scanner = ?,
                        secrets_found = ?, config_issues = ?, license_issues = ?,
                        comprehensive_scan_timestamp = ?, comprehensive_scanner = ?
                    WHERE registry = ? AND repository = ? AND tag = ?
                """,
                    [clean_params[0]]  # name
                    + clean_params[4:]  # digest onwards, skip registry/repository/tag
                    + clean_params[1:4],  # registry, repository, tag for WHERE clause
                )
                self.conn.commit()  # Ensure update is committed

                # Get the existing image ID
                cursor = self.conn.execute(
                    "SELECT id FROM images WHERE registry = ? AND repository = ? AND tag = ?",
                    clean_params[1:4],  # registry, repository, tag
                )
                row = cursor.fetchone()
                image_id = row["id"] if row else None
                print(f"    ✅ Updated existing image with ID: {image_id}")
                if image_id is None:
                    print(
                        f"    ⚠️  Warning: Could not find image ID for registry={clean_params[1]}, repository={clean_params[2]}, tag={clean_params[3]}"
                    )
                    # Try to find any record with similar details
                    cursor = self.conn.execute(
                        "SELECT id, name, registry, repository, tag FROM images LIMIT 5"
                    )
                    rows = cursor.fetchall()
                    print(
                        f"    📊 First 5 images in database: {[(r['id'], r['name'], r['registry'], r['repository'], r['tag']) for r in rows]}"
                    )
                    raise Exception(
                        f"Failed to retrieve image_id for existing record: registry={clean_params[1]}, repository={clean_params[2]}, tag={clean_params[3]}"
                    )
            else:
                # Re-raise if it's a different integrity error
                raise

        # Clear existing related data for this image
        self._clear_image_relations(image_id)

        # Insert languages
        languages_inserted = 0
        for i, lang_data in enumerate(analysis_data.get("languages", [])):
            try:
                cursor = self.conn.execute(
                    """
                    INSERT INTO languages (
                        image_id, language, version, major_minor, package_name,
                        package_type, architecture, vendor, verified
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        image_id,
                        lang_data.get("language"),
                        lang_data.get("version"),
                        lang_data.get("major_minor"),
                        lang_data.get("package_name"),
                        lang_data.get("package_type"),
                        lang_data.get("architecture"),
                        lang_data.get("vendor"),
                        lang_data.get("verified", False),
                    ),
                )
                if cursor.rowcount > 0:
                    languages_inserted += 1
                else:
                    print(
                        f"    ⚠️  Warning: Language insert {i+1} did not insert any rows: {lang_data}"
                    )
            except Exception as e:
                print(
                    f"    ❌ Error inserting language {i+1} ({lang_data.get('language', 'unknown')}): {e}"
                )

        if languages_inserted > 0:
            print(f"    ✅ Inserted {languages_inserted} languages")

        # Insert package managers
        package_managers_inserted = 0
        for i, pm_data in enumerate(analysis_data.get("package_managers", [])):
            try:
                cursor = self.conn.execute(
                    """
                    INSERT INTO package_managers (image_id, name, version, language)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        image_id,
                        pm_data.get("name"),
                        pm_data.get("version"),
                        pm_data.get("language"),
                    ),
                )
                if cursor.rowcount > 0:
                    package_managers_inserted += 1
                else:
                    print(
                        f"    ⚠️  Warning: Package manager insert {i+1} did not insert any rows: {pm_data}"
                    )
            except Exception as e:
                print(
                    f"    ❌ Error inserting package manager {i+1} ({pm_data.get('name', 'unknown')}): {e}"
                )

        if package_managers_inserted > 0:
            print(f"    ✅ Inserted {package_managers_inserted} package managers")

        # Insert capabilities
        capabilities_inserted = 0
        for i, capability in enumerate(analysis_data.get("capabilities", [])):
            try:
                cursor = self.conn.execute(
                    """
                    INSERT INTO capabilities (image_id, capability)
                    VALUES (?, ?)
                """,
                    (image_id, capability),
                )
                if cursor.rowcount > 0:
                    capabilities_inserted += 1
                else:
                    print(
                        f"    ⚠️  Warning: Capability insert {i+1} did not insert any rows: {capability}"
                    )
            except Exception as e:
                print(f"    ❌ Error inserting capability {i+1} ({capability}): {e}")

        if capabilities_inserted > 0:
            print(f"    ✅ Inserted {capabilities_inserted} capabilities")

        # Insert system packages (limit to important ones)
        system_packages_inserted = 0
        for i, pkg_data in enumerate(analysis_data.get("system_packages", [])[:]):
            try:
                cursor = self.conn.execute(
                    """
                    INSERT INTO system_packages (image_id, name, version, package_type)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        image_id,
                        pkg_data.get("name"),
                        pkg_data.get("version"),
                        pkg_data.get("type"),
                    ),
                )
                if cursor.rowcount > 0:
                    system_packages_inserted += 1
                else:
                    print(
                        f"    ⚠️  Warning: System package insert {i+1} did not insert any rows: {pkg_data}"
                    )
            except Exception as e:
                print(
                    f"    ❌ Error inserting system package {i+1} ({pkg_data.get('name', 'unknown')}): {e}"
                )

        if system_packages_inserted > 0:
            print(f"    ✅ Inserted {system_packages_inserted} system packages")

        # Insert detailed vulnerabilities if available
        vulnerabilities_inserted = 0
        for i, vuln_data in enumerate(analysis_data.get("vulnerability_details", [])):
            try:
                # Handle fixed_version - convert list to string if needed
                fixed_version = vuln_data.get("fixed_version")
                if isinstance(fixed_version, list):
                    # Convert list to comma-separated string
                    fixed_version = (
                        ", ".join(str(v) for v in fixed_version)
                        if fixed_version
                        else None
                    )
                elif fixed_version is not None:
                    # Ensure it's a string
                    fixed_version = str(fixed_version)

                # Handle other potential list fields
                description = vuln_data.get("description")
                if isinstance(description, list):
                    description = (
                        "; ".join(str(d) for d in description) if description else None
                    )
                elif description is not None:
                    description = str(description)

                package_name = vuln_data.get("package_name")
                if isinstance(package_name, list):
                    package_name = (
                        ", ".join(str(p) for p in package_name)
                        if package_name
                        else None
                    )
                elif package_name is not None:
                    package_name = str(package_name)

                package_version = vuln_data.get("package_version")
                if isinstance(package_version, list):
                    package_version = (
                        ", ".join(str(v) for v in package_version)
                        if package_version
                        else None
                    )
                elif package_version is not None:
                    package_version = str(package_version)

                cursor = self.conn.execute(
                    """
                    INSERT INTO vulnerabilities (
                        image_id, vulnerability_id, severity, package_name,
                        package_version, fixed_version, description, cvss_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        image_id,
                        vuln_data.get("id"),
                        vuln_data.get("severity"),
                        package_name,
                        package_version,
                        fixed_version,
                        description,
                        vuln_data.get("cvss_score"),
                    ),
                )
                if cursor.rowcount > 0:
                    vulnerabilities_inserted += 1
                else:
                    print(
                        f"    ⚠️  Warning: Vulnerability insert {i+1} did not insert any rows: {vuln_data}"
                    )
            except Exception as e:
                print(
                    f"    ❌ Error inserting vulnerability {i+1} ({vuln_data.get('id', 'unknown')}): {e}"
                )
                # Debug: print the actual data that caused the error
                print(f"        Debug data: {vuln_data}")

        if vulnerabilities_inserted > 0:
            print(f"    ✅ Inserted {vulnerabilities_inserted} vulnerabilities")

        # Insert security findings if available
        security_findings_inserted = 0
        for i, finding_data in enumerate(analysis_data.get("security_findings", [])):
            try:
                cursor = self.conn.execute(
                    """
                    INSERT INTO security_findings (
                        image_id, finding_type, severity, rule_id, title,
                        description, file_path, category, message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        image_id,
                        finding_data.get("finding_type"),
                        finding_data.get("severity"),
                        finding_data.get("rule_id"),
                        finding_data.get("title"),
                        finding_data.get("description"),
                        finding_data.get("file_path"),
                        finding_data.get("category"),
                        finding_data.get("message"),
                    ),
                )
                if cursor.rowcount > 0:
                    security_findings_inserted += 1
                else:
                    print(
                        f"    ⚠️  Warning: Security finding insert {i+1} did not insert any rows: {finding_data}"
                    )
            except Exception as e:
                print(
                    f"    ❌ Error inserting security finding {i+1} ({finding_data.get('title', 'unknown')}): {e}"
                )

        if security_findings_inserted > 0:
            print(f"    ✅ Inserted {security_findings_inserted} security findings")

        # Insert security findings from comprehensive scan
        comprehensive_findings_inserted = 0
        if comprehensive_security and comprehensive_security.get("scanner"):
            # Insert secret findings
            for i, secret in enumerate(
                comprehensive_security.get("secret_details", [])
            ):
                try:
                    cursor = self.conn.execute(
                        """
                        INSERT INTO security_findings (
                            image_id, finding_type, severity, rule_id, title,
                            file_path, category
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            image_id,
                            "secret",
                            secret.get("severity", "unknown"),
                            secret.get("rule_id"),
                            secret.get("title"),
                            secret.get("file_path"),
                            secret.get("category"),
                        ),
                    )
                    if cursor.rowcount > 0:
                        comprehensive_findings_inserted += 1
                    else:
                        print(
                            f"    ⚠️  Warning: Secret finding insert {i+1} did not insert any rows: {secret}"
                        )
                except Exception as e:
                    print(
                        f"    ❌ Error inserting secret finding {i+1} ({secret.get('title', 'unknown')}): {e}"
                    )

            # Insert configuration findings
            for i, config in enumerate(
                comprehensive_security.get("config_details", [])
            ):
                try:
                    cursor = self.conn.execute(
                        """
                        INSERT INTO security_findings (
                            image_id, finding_type, severity, rule_id, title,
                            description, message
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            image_id,
                            "config",
                            config.get("severity", "unknown"),
                            config.get("check_id"),
                            config.get("title"),
                            config.get("description"),
                            config.get("message"),
                        ),
                    )
                    if cursor.rowcount > 0:
                        comprehensive_findings_inserted += 1
                    else:
                        print(
                            f"    ⚠️  Warning: Config finding insert {i+1} did not insert any rows: {config}"
                        )
                except Exception as e:
                    print(
                        f"    ❌ Error inserting config finding {i+1} ({config.get('title', 'unknown')}): {e}"
                    )

            # Insert license findings
            for i, license_info in enumerate(
                comprehensive_security.get("license_details", [])
            ):
                try:
                    cursor = self.conn.execute(
                        """
                        INSERT INTO security_findings (
                            image_id, finding_type, severity, title, file_path
                        ) VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            image_id,
                            "license",
                            "info",
                            license_info.get("name"),
                            license_info.get("file_path"),
                        ),
                    )
                    if cursor.rowcount > 0:
                        comprehensive_findings_inserted += 1
                    else:
                        print(
                            f"    ⚠️  Warning: License finding insert {i+1} did not insert any rows: {license_info}"
                        )
                except Exception as e:
                    print(
                        f"    ❌ Error inserting license finding {i+1} ({license_info.get('name', 'unknown')}): {e}"
                    )

        if comprehensive_findings_inserted > 0:
            print(
                f"    ✅ Inserted {comprehensive_findings_inserted} comprehensive security findings"
            )

        self.conn.commit()

        # Log summary of all inserts
        total_inserts = (
            languages_inserted
            + package_managers_inserted
            + capabilities_inserted
            + system_packages_inserted
            + vulnerabilities_inserted
            + security_findings_inserted
            + comprehensive_findings_inserted
        )
        print(f"  📊 Insert Summary: {total_inserts} total related records inserted")
        print(f"      - Languages: {languages_inserted}")
        print(f"      - Package Managers: {package_managers_inserted}")
        print(f"      - Capabilities: {capabilities_inserted}")
        print(f"      - System Packages: {system_packages_inserted}")
        print(f"      - Vulnerabilities: {vulnerabilities_inserted}")
        print(f"      - Security Findings: {security_findings_inserted}")
        print(f"      - Comprehensive Findings: {comprehensive_findings_inserted}")

        return image_id

    def _clear_image_relations(self, image_id: int):
        """Clear existing related data for an image"""
        tables = [
            "languages",
            "package_managers",
            "capabilities",
            "system_packages",
            "vulnerabilities",
            "security_findings",
        ]

        for table in tables:
            self.conn.execute(f"DELETE FROM {table} WHERE image_id = ?", (image_id,))

    def _parse_image_name(self, image_name: str) -> Tuple[str, str, str]:
        """Parse image name into registry, repository, and tag"""

        # Default values
        registry = "mcr.microsoft.com"
        repository = ""
        tag = "latest"

        # Remove protocol if present
        clean_name = image_name.replace("https://", "").replace("http://", "")

        # Split by slash
        parts = clean_name.split("/")

        if len(parts) >= 3:
            registry = parts[0]
            # Check if last part has tag
            if ":" in parts[-1]:
                repo_tag = parts[-1].split(":")
                repository = "/".join(parts[1:-1]) + "/" + repo_tag[0]
                tag = repo_tag[1]
            else:
                repository = "/".join(parts[1:])
        elif len(parts) == 2:
            # Handle cases like "small/python:3.12" or "namespace/image:tag"
            if ":" in parts[1]:
                repo_tag = parts[1].split(":")
                repository = parts[0] + "/" + repo_tag[0]
                tag = repo_tag[1]
            else:
                repository = "/".join(parts)
        elif len(parts) == 1:
            # Handle cases like "python:3.12" or just "python"
            if ":" in parts[0]:
                repo_tag = parts[0].split(":")
                repository = repo_tag[0]
                tag = repo_tag[1]
            else:
                repository = parts[0]

        return registry, repository, tag

    def query_images_by_language(
        self, language: str, version: str = None, max_vulnerabilities: int = None
    ) -> List[Dict]:
        """Query images by language with optional vulnerability filtering"""

        base_query = """
            SELECT DISTINCT i.*,
                   l.language, l.version as lang_version, l.major_minor,
                   GROUP_CONCAT(DISTINCT c.capability) as capabilities
            FROM images i
            JOIN languages l ON i.id = l.image_id
            LEFT JOIN capabilities c ON i.id = c.image_id
            WHERE l.language = ?
        """

        params = [language]

        if version:
            # Extract major.minor version for more flexible matching
            import re

            version_match = re.match(r"(\d+)\.(\d+)", version)
            if version_match:
                major_minor = f"{version_match.group(1)}.{version_match.group(2)}"
                base_query += " AND (l.version LIKE ? OR l.major_minor LIKE ? OR l.version LIKE ? OR l.major_minor = ?)"
                params.extend(
                    [f"{version}%", f"{version}%", f"{major_minor}%", major_minor]
                )
            else:
                base_query += " AND (l.version LIKE ? OR l.major_minor LIKE ?)"
                params.extend([f"{version}%", f"{version}%"])

        if max_vulnerabilities is not None:
            base_query += " AND i.total_vulnerabilities <= ?"
            params.append(max_vulnerabilities)

        base_query += (
            " GROUP BY i.id ORDER BY i.total_vulnerabilities ASC, i.size_bytes ASC"
        )

        cursor = self.conn.execute(base_query, params)
        return [dict(row) for row in cursor.fetchall()]

    def query_secure_images(
        self, max_critical: int = 0, max_high: int = 0
    ) -> List[Dict]:
        """Query images with low vulnerability counts"""

        query = """
            SELECT i.*,
                   GROUP_CONCAT(DISTINCT l.language || ':' || COALESCE(l.version, 'unknown')) as languages,
                   GROUP_CONCAT(DISTINCT c.capability) as capabilities
            FROM images i
            LEFT JOIN languages l ON i.id = l.image_id
            LEFT JOIN capabilities c ON i.id = c.image_id
            WHERE i.critical_vulnerabilities <= ? AND i.high_vulnerabilities <= ?
            GROUP BY i.id
            ORDER BY i.critical_vulnerabilities ASC, i.high_vulnerabilities ASC, i.total_vulnerabilities ASC
        """

        cursor = self.conn.execute(query, (max_critical, max_high))
        return [dict(row) for row in cursor.fetchall()]

    def get_vulnerability_statistics(self) -> Dict:
        """Get overall vulnerability statistics"""

        cursor = self.conn.execute(
            """
            SELECT
                COUNT(*) as total_images,
                AVG(total_vulnerabilities) as avg_vulnerabilities,
                AVG(critical_vulnerabilities) as avg_critical,
                AVG(high_vulnerabilities) as avg_high,
                SUM(CASE WHEN total_vulnerabilities = 0 THEN 1 ELSE 0 END) as zero_vuln_images,
                SUM(CASE WHEN critical_vulnerabilities = 0 AND high_vulnerabilities = 0 THEN 1 ELSE 0 END) as safe_images
            FROM images
        """
        )

        return dict(cursor.fetchone())

    def get_languages_summary(self) -> List[Dict]:
        """Get summary of available languages"""

        cursor = self.conn.execute(
            """
            SELECT
                l.language,
                COUNT(DISTINCT i.id) as image_count,
                GROUP_CONCAT(DISTINCT l.version) as versions,
                AVG(i.total_vulnerabilities) as avg_vulnerabilities,
                AVG(i.size_bytes) as avg_size_bytes
            FROM languages l
            JOIN images i ON l.image_id = i.id
            GROUP BY l.language
            ORDER BY image_count DESC
        """
        )

        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def get_all_images_with_details(
        self,
        page: int = 1,
        per_page: int = 20,
        language_filter: str = "",
        security_filter: str = "all",
    ) -> List[Dict]:
        """Get paginated list of images with details"""
        offset = (page - 1) * per_page

        # Build WHERE clause based on filters
        where_clauses = []
        params = []

        if language_filter:
            where_clauses.append(
                "EXISTS (SELECT 1 FROM languages l WHERE l.image_id = i.id AND l.language = ?)"
            )
            params.append(language_filter)

        if security_filter == "secure":
            where_clauses.append("i.total_vulnerabilities = 0")
        elif security_filter == "safe":
            where_clauses.append(
                "i.critical_vulnerabilities = 0 AND i.high_vulnerabilities = 0"
            )
        elif security_filter == "vulnerable":
            where_clauses.append("i.total_vulnerabilities > 0")

        where_sql = " AND ".join(where_clauses)
        if where_sql:
            where_sql = "WHERE " + where_sql

        query = f"""
            SELECT i.*,
                   GROUP_CONCAT(DISTINCT l.language || ':' || COALESCE(l.version, 'unknown')) as languages
            FROM images i
            LEFT JOIN languages l ON i.id = l.image_id
            {where_sql}
            GROUP BY i.id
            ORDER BY i.scan_timestamp DESC
            LIMIT ? OFFSET ?
        """

        params.extend([per_page, offset])
        cursor = self.conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_image_count(
        self, language_filter: str = "", security_filter: str = "all"
    ) -> int:
        """Get total count of images matching filters"""
        where_clauses = []
        params = []

        if language_filter:
            where_clauses.append(
                "EXISTS (SELECT 1 FROM languages l WHERE l.image_id = i.id AND l.language = ?)"
            )
            params.append(language_filter)

        if security_filter == "secure":
            where_clauses.append("i.total_vulnerabilities = 0")
        elif security_filter == "safe":
            where_clauses.append(
                "i.critical_vulnerabilities = 0 AND i.high_vulnerabilities = 0"
            )
        elif security_filter == "vulnerable":
            where_clauses.append("i.total_vulnerabilities > 0")

        where_sql = " AND ".join(where_clauses)
        if where_sql:
            where_sql = "WHERE " + where_sql

        query = f"SELECT COUNT(*) FROM images i {where_sql}"
        cursor = self.conn.execute(query, params)
        return cursor.fetchone()[0]

    def get_image_details(self, image_id: int) -> Optional[Dict]:
        """Get detailed information about a specific image"""
        # Get basic image info
        cursor = self.conn.execute("SELECT * FROM images WHERE id = ?", (image_id,))
        image = cursor.fetchone()
        if not image:
            return None

        image = dict(image)

        # Get languages
        cursor = self.conn.execute(
            "SELECT * FROM languages WHERE image_id = ?", (image_id,)
        )
        image["languages"] = [dict(row) for row in cursor.fetchall()]

        # Get capabilities
        cursor = self.conn.execute(
            "SELECT capability FROM capabilities WHERE image_id = ?", (image_id,)
        )
        image["capabilities"] = [row[0] for row in cursor.fetchall()]

        # Get package managers
        cursor = self.conn.execute(
            "SELECT * FROM package_managers WHERE image_id = ?", (image_id,)
        )
        image["package_managers"] = [dict(row) for row in cursor.fetchall()]

        # Get vulnerabilities (top 20)
        cursor = self.conn.execute(
            """SELECT * FROM vulnerabilities WHERE image_id = ?
               ORDER BY
                   CASE severity
                       WHEN 'critical' THEN 1
                       WHEN 'high' THEN 2
                       WHEN 'medium' THEN 3
                       WHEN 'low' THEN 4
                       ELSE 5
                   END
               LIMIT 20""",
            (image_id,),
        )
        image["vulnerability_details"] = [dict(row) for row in cursor.fetchall()]

        # Get system packages
        cursor = self.conn.execute(
            "SELECT * FROM system_packages WHERE image_id = ? ORDER BY name",
            (image_id,),
        )
        image["system_packages"] = [dict(row) for row in cursor.fetchall()]

        return image

    def search_images(self, query: str, language: str = "") -> List[Dict]:
        """Search images by name or other criteria"""
        where_clauses = ["i.name LIKE ?"]
        params = [f"%{query}%"]

        if language:
            where_clauses.append(
                "EXISTS (SELECT 1 FROM languages l WHERE l.image_id = i.id AND l.language = ?)"
            )
            params.append(language)

        where_sql = " AND ".join(where_clauses)

        query_sql = f"""
            SELECT i.*,
                   GROUP_CONCAT(DISTINCT l.language || ':' || COALESCE(l.version, 'unknown')) as languages
            FROM images i
            LEFT JOIN languages l ON i.id = l.image_id
            WHERE {where_sql}
            GROUP BY i.id
            ORDER BY i.total_vulnerabilities ASC, i.name ASC
        """

        cursor = self.conn.execute(query_sql, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_image_by_exact_name(self, image_name: str) -> Dict:
        """Get an image by its exact name"""
        query = """
            SELECT i.*, i.name as image_name, i.tag,
                   GROUP_CONCAT(DISTINCT l.language) as languages,
                   COUNT(v.id) as vulnerability_count
            FROM images i
            LEFT JOIN languages l ON i.id = l.image_id
            LEFT JOIN vulnerabilities v ON i.id = v.image_id
            WHERE i.name = ?
            GROUP BY i.id
        """

        cursor = self.conn.execute(query, [image_name])
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_vulnerability_distribution(self) -> Dict:
        """Get distribution of vulnerabilities across all images"""
        query = """
            SELECT
                COUNT(CASE WHEN total_vulnerabilities = 0 THEN 1 END) as zero,
                COUNT(CASE WHEN total_vulnerabilities BETWEEN 1 AND 5 THEN 1 END) as low,
                COUNT(CASE WHEN total_vulnerabilities BETWEEN 6 AND 15 THEN 1 END) as medium,
                COUNT(CASE WHEN total_vulnerabilities > 15 THEN 1 END) as high
            FROM images
        """
        cursor = self.conn.execute(query)
        row = cursor.fetchone()
        return dict(row) if row else {}

    def get_language_vulnerability_stats(self) -> List[Dict]:
        """Get vulnerability statistics by language"""
        query = """
            SELECT
                l.language,
                COUNT(DISTINCT i.id) as image_count,
                AVG(i.total_vulnerabilities) as avg_vulnerabilities,
                AVG(i.critical_vulnerabilities) as avg_critical,
                AVG(i.high_vulnerabilities) as avg_high,
                COUNT(CASE WHEN i.total_vulnerabilities = 0 THEN 1 END) as zero_vuln_count
            FROM languages l
            JOIN images i ON l.image_id = i.id
            GROUP BY l.language
            ORDER BY avg_vulnerabilities ASC, image_count DESC
        """
        cursor = self.conn.execute(query)
        return [dict(row) for row in cursor.fetchall()]

    def get_size_distribution(self) -> List[Dict]:
        """Get distribution of image sizes"""
        query = """
            SELECT
                CASE
                    WHEN size_bytes < 50000000 THEN 'Small (<50MB)'
                    WHEN size_bytes < 100000000 THEN 'Medium (50-100MB)'
                    WHEN size_bytes < 500000000 THEN 'Large (100-500MB)'
                    ELSE 'Very Large (>500MB)'
                END as size_category,
                COUNT(*) as count,
                AVG(total_vulnerabilities) as avg_vulnerabilities
            FROM images
            WHERE size_bytes > 0
            GROUP BY size_category
            ORDER BY avg_vulnerabilities ASC
        """
        cursor = self.conn.execute(query)
        return [dict(row) for row in cursor.fetchall()]

    def export_all_data(self) -> Dict:
        """Export all database data for backup/analysis"""
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "images": [],
            "statistics": self.get_vulnerability_statistics(),
        }

        # Get all images with full details
        cursor = self.conn.execute("SELECT * FROM images ORDER BY scan_timestamp DESC")
        for image_row in cursor.fetchall():
            image_data = dict(image_row)
            image_id = image_data["id"]

            # Get related data
            cursor2 = self.conn.execute(
                "SELECT * FROM languages WHERE image_id = ?", (image_id,)
            )
            image_data["languages"] = [dict(row) for row in cursor2.fetchall()]

            cursor2 = self.conn.execute(
                "SELECT capability FROM capabilities WHERE image_id = ?", (image_id,)
            )
            image_data["capabilities"] = [row[0] for row in cursor2.fetchall()]

            cursor2 = self.conn.execute(
                "SELECT * FROM package_managers WHERE image_id = ?", (image_id,)
            )
            image_data["package_managers"] = [dict(row) for row in cursor2.fetchall()]

            export_data["images"].append(image_data)

        return export_data

    def clear_all_data(self) -> Dict:
        """Clear all data from the database and return statistics about what was cleared"""
        # Get statistics before clearing
        stats_before = {
            "images": self.conn.execute("SELECT COUNT(*) FROM images").fetchone()[0],
            "languages": self.conn.execute("SELECT COUNT(*) FROM languages").fetchone()[
                0
            ],
            "package_managers": self.conn.execute(
                "SELECT COUNT(*) FROM package_managers"
            ).fetchone()[0],
            "capabilities": self.conn.execute(
                "SELECT COUNT(*) FROM capabilities"
            ).fetchone()[0],
            "system_packages": self.conn.execute(
                "SELECT COUNT(*) FROM system_packages"
            ).fetchone()[0],
            "vulnerabilities": self.conn.execute(
                "SELECT COUNT(*) FROM vulnerabilities"
            ).fetchone()[0],
            "security_findings": self.conn.execute(
                "SELECT COUNT(*) FROM security_findings"
            ).fetchone()[0],
        }

        # Clear all tables (order matters due to foreign key constraints)
        tables_to_clear = [
            "security_findings",
            "vulnerabilities",
            "system_packages",
            "capabilities",
            "package_managers",
            "languages",
            "images",
        ]

        for table in tables_to_clear:
            self.conn.execute(f"DELETE FROM {table}")

        # Reset auto-increment counters
        for table in tables_to_clear:
            self.conn.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")

        # Commit all changes
        self.conn.commit()

        # Verify tables are empty
        stats_after = {
            "images": self.conn.execute("SELECT COUNT(*) FROM images").fetchone()[0],
            "languages": self.conn.execute("SELECT COUNT(*) FROM languages").fetchone()[
                0
            ],
            "package_managers": self.conn.execute(
                "SELECT COUNT(*) FROM package_managers"
            ).fetchone()[0],
            "capabilities": self.conn.execute(
                "SELECT COUNT(*) FROM capabilities"
            ).fetchone()[0],
            "system_packages": self.conn.execute(
                "SELECT COUNT(*) FROM system_packages"
            ).fetchone()[0],
            "vulnerabilities": self.conn.execute(
                "SELECT COUNT(*) FROM vulnerabilities"
            ).fetchone()[0],
            "security_findings": self.conn.execute(
                "SELECT COUNT(*) FROM security_findings"
            ).fetchone()[0],
        }

        return {
            "cleared_timestamp": datetime.now().isoformat(),
            "stats_before": stats_before,
            "stats_after": stats_after,
            "total_records_cleared": sum(stats_before.values()),
        }

    def reset_database(self) -> Dict:
        """Reset the database by clearing all data and recreating tables if needed"""
        # Clear all data first
        clear_stats = self.clear_all_data()

        # Verify table structure is still intact
        self.verify_table_constraints()

        return {
            "reset_timestamp": datetime.now().isoformat(),
            "operation": "database_reset",
            "clear_stats": clear_stats,
            "message": "Database has been reset and is ready for new data",
        }

    def __enter__(self):
        return self
