#!/usr/bin/env python3
"""
Model Context Protocol (MCP) Server for Container Image Recommendations

This module implements an MCP server that exposes container image recommendation
functionality through the Model Context Protocol, allowing AI assistants to
query for secure base image recommendations.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from database import ImageDatabase
from recommendation_engine import RecommendationEngine, UserRequirement

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPServer:
    """MCP Server for Container Image Recommendations"""

    def __init__(self, db_path: str = "azure_linux_images.db"):
        """Initialize the MCP server with database connection"""
        self.db_path = db_path
        self.recommendation_engine = None
        self._initialize_engine()

    def _initialize_engine(self):
        """Initialize the recommendation engine"""
        try:
            self.recommendation_engine = RecommendationEngine(
                database_path=self.db_path
            )
            logger.info(f"MCP Server initialized with database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize recommendation engine: {e}")
            raise

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")

            logger.info(f"Handling request: {method}")

            if method == "initialize":
                return await self._handle_initialize(request_id, params)
            elif method == "tools/list":
                return await self._handle_tools_list(request_id)
            elif method == "tools/call":
                return await self._handle_tools_call(request_id, params)
            elif method == "resources/list":
                return await self._handle_resources_list(request_id)
            elif method == "resources/read":
                return await self._handle_resources_read(request_id, params)
            elif method == "prompts/list":
                return await self._handle_prompts_list(request_id)
            elif method == "prompts/get":
                return await self._handle_prompts_get(request_id, params)
            else:
                return self._error_response(
                    request_id, -32601, f"Method not found: {method}"
                )

        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return self._error_response(request.get("id"), -32603, str(e))

    async def _handle_initialize(
        self, request_id: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle initialization request"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": True},
                    "resources": {"subscribe": True, "listChanged": True},
                    "prompts": {"listChanged": True},
                },
                "serverInfo": {
                    "name": "container-image-recommender",
                    "version": "1.0.0",
                },
            },
        }

    async def _handle_tools_list(self, request_id: str) -> Dict[str, Any]:
        """Handle tools list request"""
        tools = [
            {
                "name": "recommend_images",
                "description": "Get container base image recommendations based on requirements",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "language": {
                            "type": "string",
                            "description": "Programming language (e.g., python, nodejs, java, go, dotnet)",
                        },
                        "version": {
                            "type": "string",
                            "description": "Language version (e.g., 3.12, 18, 17)",
                            "default": None,
                        },
                        "packages": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Required packages",
                            "default": [],
                        },
                        "size_preference": {
                            "type": "string",
                            "enum": ["minimal", "balanced", "full"],
                            "description": "Size preference for the image",
                            "default": "balanced",
                        },
                        "security_level": {
                            "type": "string",
                            "enum": ["standard", "high", "maximum"],
                            "description": "Security level requirement",
                            "default": "high",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of recommendations to return",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 20,
                        },
                    },
                    "required": ["language"],
                },
            },
            {
                "name": "analyze_image",
                "description": "Analyze a specific container image and get recommendations for alternatives",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "image_name": {
                            "type": "string",
                            "description": "Full container image name (e.g., docker.io/library/python:3.12-slim)",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of alternative recommendations",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 20,
                        },
                    },
                    "required": ["image_name"],
                },
            },
            {
                "name": "search_images",
                "description": "Search for container images by language, security level, or other criteria",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "language": {
                            "type": "string",
                            "description": "Programming language filter",
                        },
                        "security_filter": {
                            "type": "string",
                            "enum": ["secure", "safe", "vulnerable", "all"],
                            "description": "Security level filter",
                            "default": "all",
                        },
                        "max_vulnerabilities": {
                            "type": "integer",
                            "description": "Maximum number of vulnerabilities allowed",
                            "minimum": 0,
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 50,
                        },
                    },
                },
            },
        ]

        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": tools}}

    async def _handle_tools_call(
        self, request_id: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle tool call request"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        try:
            if tool_name == "recommend_images":
                result = await self._recommend_images(arguments)
            elif tool_name == "analyze_image":
                result = await self._analyze_image(arguments)
            elif tool_name == "search_images":
                result = await self._search_images(arguments)
            else:
                return self._error_response(
                    request_id, -32602, f"Unknown tool: {tool_name}"
                )

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                },
            }

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return self._error_response(
                request_id, -32603, f"Tool execution failed: {str(e)}"
            )

    async def _recommend_images(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get image recommendations based on requirements"""
        language = arguments.get("language")
        version = arguments.get("version")
        packages = arguments.get("packages", [])
        size_preference = arguments.get("size_preference", "balanced")
        security_level = arguments.get("security_level", "high")
        limit = arguments.get("limit", 5)

        # Create user requirement
        requirement = UserRequirement(
            language=language,
            version=version,
            packages=packages,
            size_preference=size_preference,
            security_level=security_level,
        )

        # Get recommendations
        recommendations = self.recommendation_engine.recommend(requirement)

        # Limit results
        recommendations = recommendations[:limit]

        # Format response
        result = {
            "query": {
                "language": language,
                "version": version,
                "packages": packages,
                "size_preference": size_preference,
                "security_level": security_level,
            },
            "recommendations": [],
        }

        for rec in recommendations:
            # Extract vulnerability data from analysis_data
            vulnerabilities = rec.analysis_data.get("vulnerabilities", {})
            size_mb = rec.analysis_data.get("manifest", {}).get("size", 0) / (
                1024 * 1024
            )
            detected_languages = [
                lang.get("language") for lang in rec.analysis_data.get("languages", [])
            ]
            packages = []
            if "packages" in rec.analysis_data:
                packages = [
                    pkg.get("name", "") for pkg in rec.analysis_data.get("packages", [])
                ]

            result["recommendations"].append(
                {
                    "image_name": rec.image_name,
                    "score": rec.score,
                    "security_score": rec.security_score,
                    "package_compatibility": rec.package_compatibility,
                    "size_score": rec.size_score,
                    "language_match": rec.language_match,
                    "version_match": rec.version_match,
                    "reasoning": rec.reasoning,
                    "vulnerabilities": {
                        "total": vulnerabilities.get("total", 0),
                        "critical": vulnerabilities.get("critical", 0),
                        "high": vulnerabilities.get("high", 0),
                        "medium": vulnerabilities.get("medium", 0),
                        "low": vulnerabilities.get("low", 0),
                    },
                    "size_mb": round(size_mb, 1),
                    "detected_languages": detected_languages,
                    "packages": (
                        packages[:10] if packages else []
                    ),  # Limit packages for readability
                }
            )

        return result

    async def _analyze_image(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a specific image and suggest alternatives"""
        image_name = arguments.get("image_name")
        limit = arguments.get("limit", 5)

        # For now, we'll extract requirements from the image name and get recommendations
        # In a full implementation, this would actually analyze the image

        # Simple extraction of language from image name
        language = self._extract_language_from_image(image_name)
        if not language:
            return {
                "error": "Could not determine language from image name",
                "image_name": image_name,
                "suggestions": "Please provide language explicitly using recommend_images tool",
            }

        # Create a requirement based on detected language
        requirement = UserRequirement(language=language, security_level="high")

        recommendations = self.recommendation_engine.recommend(requirement)
        recommendations = recommendations[:limit]

        return {
            "analyzed_image": image_name,
            "detected_language": language,
            "alternatives": [
                {
                    "image_name": rec.image_name,
                    "score": rec.score,
                    "reasoning": rec.reasoning,
                    "security_improvement": (
                        "Lower vulnerability count"
                        if rec.analysis_data.get("vulnerabilities", {}).get("total", 0)
                        < 50
                        else "Similar security profile"
                    ),
                    "vulnerabilities": rec.analysis_data.get("vulnerabilities", {}),
                }
                for rec in recommendations
            ],
        }

    async def _search_images(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Search for images based on criteria"""
        language = arguments.get("language")
        security_filter = arguments.get("security_filter", "all")
        max_vulnerabilities = arguments.get("max_vulnerabilities")
        limit = arguments.get("limit", 10)

        db = ImageDatabase(self.db_path)
        try:
            # Set max_vulnerabilities based on security filter if not explicitly provided
            if max_vulnerabilities is None:
                if security_filter == "secure":
                    max_vulnerabilities = 0
                elif security_filter == "safe":
                    max_vulnerabilities = 10
                elif security_filter == "vulnerable":
                    # For vulnerable, we want images with more than 20 vulnerabilities
                    # We'll fetch all and filter manually
                    max_vulnerabilities = None

            # Use the query_images_by_language method if language is specified
            if language:
                images = db.query_images_by_language(
                    language=language, max_vulnerabilities=max_vulnerabilities
                )
            else:
                # For no language filter, get all images and filter manually
                all_images_query = """
                    SELECT DISTINCT i.*,
                           GROUP_CONCAT(DISTINCT l.language) as languages
                    FROM images i
                    LEFT JOIN languages l ON i.id = l.image_id
                    GROUP BY i.id
                """
                if max_vulnerabilities is not None:
                    all_images_query += (
                        f" HAVING i.total_vulnerabilities <= {max_vulnerabilities}"
                    )

                cursor = db.conn.cursor()
                cursor.execute(all_images_query)
                images = [dict(row) for row in cursor.fetchall()]

            # Filter for vulnerable images if requested
            if security_filter == "vulnerable" and max_vulnerabilities is None:
                images = [
                    img for img in images if img.get("total_vulnerabilities", 0) > 20
                ]

            # Limit results
            images = images[:limit]

            return {
                "search_criteria": {
                    "language": language,
                    "security_filter": security_filter,
                    "max_vulnerabilities": max_vulnerabilities,
                },
                "results": [
                    {
                        "image_name": img.get("name"),
                        "language": (
                            img.get("language")
                            or img.get("languages", "").split(",")[0]
                            if img.get("languages")
                            else None
                        ),
                        "version": img.get("lang_version"),
                        "size_mb": round(img.get("size", 0) / (1024 * 1024), 1),
                        "vulnerabilities": {
                            "total": img.get("total_vulnerabilities", 0),
                            "critical": img.get("critical_vulnerabilities", 0),
                            "high": img.get("high_vulnerabilities", 0),
                        },
                        "packages_count": img.get("package_count", 0),
                    }
                    for img in images
                ],
            }

        finally:
            db.close()

    def _extract_language_from_image(self, image_name: str) -> Optional[str]:
        """Extract language from image name"""
        image_lower = image_name.lower()

        if "python" in image_lower:
            return "python"
        elif "node" in image_lower or "nodejs" in image_lower:
            return "nodejs"
        elif "java" in image_lower:
            return "java"
        elif "golang" in image_lower or "go:" in image_lower:
            return "go"
        elif "dotnet" in image_lower or ".net" in image_lower:
            return "dotnet"

        return None

    async def _handle_resources_list(self, request_id: str) -> Dict[str, Any]:
        """Handle resources list request"""
        resources = [
            {
                "uri": "database://stats",
                "name": "Database Statistics",
                "description": "Current database statistics and summary",
                "mimeType": "application/json",
            },
            {
                "uri": "database://languages",
                "name": "Supported Languages",
                "description": "List of supported programming languages and their statistics",
                "mimeType": "application/json",
            },
        ]

        return {"jsonrpc": "2.0", "id": request_id, "result": {"resources": resources}}

    async def _handle_resources_read(
        self, request_id: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle resources read request"""
        uri = params.get("uri")

        try:
            if uri == "database://stats":
                content = await self._get_database_stats()
            elif uri == "database://languages":
                content = await self._get_language_stats()
            else:
                return self._error_response(
                    request_id, -32602, f"Unknown resource: {uri}"
                )

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(content, indent=2),
                        }
                    ]
                },
            }

        except Exception as e:
            logger.error(f"Error reading resource {uri}: {e}")
            return self._error_response(
                request_id, -32603, f"Resource read failed: {str(e)}"
            )

    async def _get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        db = ImageDatabase(self.db_path)
        try:
            stats = db.get_vulnerability_statistics()
            return {
                "total_images": stats.get("total_images", 0),
                "zero_vulnerability_images": stats.get("zero_vulnerability_images", 0),
                "average_vulnerabilities": stats.get("average_vulnerabilities", 0),
                "total_packages": stats.get("total_packages", 0),
                "last_updated": "Available in database",
            }
        finally:
            db.close()

    async def _get_language_stats(self) -> Dict[str, Any]:
        """Get language statistics"""
        db = ImageDatabase(self.db_path)
        try:
            languages = db.get_languages_summary()
            return {
                "supported_languages": languages,
                "total_language_variants": len(languages),
            }
        finally:
            db.close()

    def _error_response(
        self, request_id: str, code: int, message: str
    ) -> Dict[str, Any]:
        """Create error response"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": code, "message": message},
        }

    async def _handle_prompts_list(self, request_id: str) -> Dict[str, Any]:
        """Handle prompts list request"""
        prompts_dir = Path(__file__).parent / ".github" / "prompts"
        prompts = []

        try:
            if prompts_dir.exists():
                for prompt_file in prompts_dir.glob("*.md"):
                    prompt_name = prompt_file.stem

                    # Skip README files
                    if prompt_name.upper() == "README":
                        continue

                    # Read the first few lines to get description
                    try:
                        with open(prompt_file, "r", encoding="utf-8") as f:
                            content = f.read()
                            lines = content.split("\n")

                            # Extract title (first # line) and description
                            title = prompt_name.replace("-", " ").title()
                            description = f"Container security prompt: {title}"

                            # Look for ## Description section
                            for i, line in enumerate(lines):
                                if line.strip() == "## Description" and i + 1 < len(
                                    lines
                                ):
                                    description = lines[i + 1].strip()
                                    break
                                elif line.startswith("# "):
                                    title = line[2:].strip()

                            prompts.append(
                                {
                                    "name": prompt_name,
                                    "description": description,
                                    "arguments": [
                                        {
                                            "name": "language",
                                            "description": "Programming language (e.g., python, nodejs, java)",
                                            "required": False,
                                        },
                                        {
                                            "name": "security_level",
                                            "description": "Security level (basic, high, maximum)",
                                            "required": False,
                                        },
                                        {
                                            "name": "current_image",
                                            "description": "Current container image to analyze",
                                            "required": False,
                                        },
                                    ],
                                }
                            )
                    except Exception as e:
                        logger.warning(f"Error reading prompt file {prompt_file}: {e}")
                        continue

            return {"jsonrpc": "2.0", "id": request_id, "result": {"prompts": prompts}}

        except Exception as e:
            logger.error(f"Error listing prompts: {e}")
            return self._error_response(
                request_id, -32603, f"Failed to list prompts: {str(e)}"
            )

    async def _handle_prompts_get(
        self, request_id: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle prompts get request"""
        prompt_name = params.get("name")
        if not prompt_name:
            return self._error_response(request_id, -32602, "Missing prompt name")

        prompts_dir = Path(__file__).parent / ".github" / "prompts"
        prompt_file = prompts_dir / f"{prompt_name}.md"

        try:
            if not prompt_file.exists():
                return self._error_response(
                    request_id, -32602, f"Prompt not found: {prompt_name}"
                )

            with open(prompt_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse the markdown to extract title and description
            lines = content.split("\n")
            title = prompt_name.replace("-", " ").title()
            description = f"Container security prompt: {title}"

            for i, line in enumerate(lines):
                if line.startswith("# "):
                    title = line[2:].strip()
                elif line.strip() == "## Description" and i + 1 < len(lines):
                    description = lines[i + 1].strip()
                    break

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "description": description,
                    "messages": [
                        {"role": "user", "content": {"type": "text", "text": content}}
                    ],
                },
            }

        except Exception as e:
            logger.error(f"Error getting prompt {prompt_name}: {e}")
            return self._error_response(
                request_id, -32603, f"Failed to get prompt: {str(e)}"
            )


async def main():
    """Main entry point for the MCP server"""
    import sys

    # Initialize server
    db_path = sys.argv[1] if len(sys.argv) > 1 else "azure_linux_images.db"
    server = MCPServer(db_path)

    logger.info("Container Image Recommendation MCP Server starting...")
    logger.info("Reading from stdin, writing to stdout")

    # Read from stdin and write to stdout for MCP communication
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            line = line.strip()
            if not line:
                continue

            # Parse JSON request
            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Handle request
            response = await server.handle_request(request)

            # Write response to stdout
            print(json.dumps(response), flush=True)

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            break

    logger.info("MCP Server shutting down")


if __name__ == "__main__":
    asyncio.run(main())
