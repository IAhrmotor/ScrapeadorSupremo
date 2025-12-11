"""Architecture agent for managing project structure and organization."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from .base_agent import BaseAgent, AgentCapability, AgentResponse


@dataclass
class FolderStructure:
    """Represents a folder structure definition."""
    name: str
    description: str
    subfolders: List[str]


class ArchitectureAgent(BaseAgent):
    """
    Agent specialized in managing project architecture, folder structure,
    and organizing functionalities across the codebase.
    """

    def __init__(self):
        super().__init__(
            name="architecture",
            description="Manages project structure, folders, and code organization"
        )
        self._keywords = [
            "architecture", "structure", "folder", "directory", "organize",
            "module", "package", "layout", "create", "scaffold", "setup",
            "project", "reorganize", "refactor", "move", "component"
        ]

        # Define standard project structures
        self._standard_structures: Dict[str, FolderStructure] = {
            "scraping": FolderStructure(
                name="scraping",
                description="Web scraping modules",
                subfolders=["spiders", "extractors", "parsers"]
            ),
            "data": FolderStructure(
                name="data",
                description="Data handling and storage",
                subfolders=["models", "storage", "transformers"]
            ),
            "utils": FolderStructure(
                name="utils",
                description="Utility functions and helpers",
                subfolders=["helpers", "validators", "formatters"]
            ),
            "config": FolderStructure(
                name="config",
                description="Configuration files and settings",
                subfolders=["environments", "schemas"]
            ),
            "output": FolderStructure(
                name="output",
                description="Output files and exports",
                subfolders=["reports", "exports", "logs"]
            ),
        }

    def get_capabilities(self) -> list[AgentCapability]:
        return [
            AgentCapability(
                name="folder_management",
                description="Create and organize folder structures",
                keywords=["folder", "directory", "create", "structure"],
                priority=10
            ),
            AgentCapability(
                name="project_scaffolding",
                description="Scaffold new project components",
                keywords=["scaffold", "setup", "initialize", "new"],
                priority=9
            ),
            AgentCapability(
                name="code_organization",
                description="Organize and refactor code structure",
                keywords=["organize", "refactor", "move", "restructure"],
                priority=8
            ),
            AgentCapability(
                name="architecture_analysis",
                description="Analyze and report on project architecture",
                keywords=["analyze", "architecture", "structure", "review"],
                priority=7
            ),
        ]

    def can_handle(self, task: str, context: Optional[Dict[str, Any]] = None) -> float:
        task_lower = task.lower()

        matches = sum(1 for kw in self._keywords if kw in task_lower)

        if matches >= 3:
            return 0.95
        elif matches >= 2:
            return 0.75
        elif matches >= 1:
            return 0.5

        return 0.0

    def get_project_root(self) -> Path:
        """Get the project root directory."""
        return Path(__file__).parent.parent

    def scan_structure(self) -> Dict[str, Any]:
        """Scan and return the current project structure."""
        root = self.get_project_root()
        structure = {"root": str(root), "folders": {}, "files": []}

        for item in root.iterdir():
            if item.name.startswith(".") or item.name == "__pycache__":
                continue

            if item.is_dir():
                structure["folders"][item.name] = self._scan_folder(item)
            else:
                structure["files"].append(item.name)

        return structure

    def _scan_folder(self, folder: Path, depth: int = 0, max_depth: int = 3) -> Dict[str, Any]:
        """Recursively scan a folder."""
        if depth >= max_depth:
            return {"truncated": True}

        result = {"folders": {}, "files": []}

        try:
            for item in folder.iterdir():
                if item.name.startswith(".") or item.name == "__pycache__":
                    continue

                if item.is_dir():
                    result["folders"][item.name] = self._scan_folder(item, depth + 1)
                else:
                    result["files"].append(item.name)
        except PermissionError:
            result["error"] = "Permission denied"

        return result

    def create_folder_structure(
        self,
        structure_name: str,
        base_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Create a predefined folder structure."""
        if structure_name not in self._standard_structures:
            return {
                "success": False,
                "error": f"Unknown structure: {structure_name}",
                "available": list(self._standard_structures.keys())
            }

        structure = self._standard_structures[structure_name]
        base = base_path or self.get_project_root()
        created = []

        # Create main folder
        main_folder = base / structure.name
        main_folder.mkdir(exist_ok=True)
        created.append(str(main_folder))

        # Create __init__.py
        init_file = main_folder / "__init__.py"
        if not init_file.exists():
            init_file.write_text(f'"""{structure.description}"""\n')
            created.append(str(init_file))

        # Create subfolders
        for subfolder in structure.subfolders:
            sub_path = main_folder / subfolder
            sub_path.mkdir(exist_ok=True)
            created.append(str(sub_path))

            # Create __init__.py in subfolder
            sub_init = sub_path / "__init__.py"
            if not sub_init.exists():
                sub_init.write_text(f'"""{subfolder.capitalize()} module."""\n')
                created.append(str(sub_init))

        return {
            "success": True,
            "structure": structure_name,
            "created": created
        }

    def create_custom_folder(
        self,
        folder_name: str,
        subfolders: Optional[List[str]] = None,
        base_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Create a custom folder structure."""
        base = base_path or self.get_project_root()
        created = []

        main_folder = base / folder_name
        main_folder.mkdir(exist_ok=True)
        created.append(str(main_folder))

        # Create __init__.py
        init_file = main_folder / "__init__.py"
        if not init_file.exists():
            init_file.write_text(f'"""{folder_name.capitalize()} module."""\n')
            created.append(str(init_file))

        if subfolders:
            for subfolder in subfolders:
                sub_path = main_folder / subfolder
                sub_path.mkdir(exist_ok=True)
                created.append(str(sub_path))

                sub_init = sub_path / "__init__.py"
                if not sub_init.exists():
                    sub_init.write_text(f'"""{subfolder.capitalize()} module."""\n')
                    created.append(str(sub_init))

        return {
            "success": True,
            "folder": folder_name,
            "created": created
        }

    def suggest_structure(self, project_type: str = "scraping") -> Dict[str, Any]:
        """Suggest a complete project structure based on project type."""
        suggestions = {
            "scraping": [
                "agents",      # Agent system
                "scraping",    # Scraping logic
                "data",        # Data handling
                "config",      # Configuration
                "output",      # Output files
                "utils",       # Utilities
            ],
            "api": [
                "agents",
                "api",
                "data",
                "config",
                "utils",
            ],
            "minimal": [
                "agents",
                "core",
                "utils",
            ]
        }

        return {
            "project_type": project_type,
            "suggested_folders": suggestions.get(project_type, suggestions["minimal"]),
            "available_structures": list(self._standard_structures.keys())
        }

    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Execute architecture-related tasks."""
        task_lower = task.lower()

        # Analyze/scan task
        if any(word in task_lower for word in ["scan", "analyze", "show", "list", "view"]):
            structure = self.scan_structure()
            return AgentResponse(
                success=True,
                result=structure,
                message="Project structure scanned successfully"
            )

        # Create predefined structure
        for struct_name in self._standard_structures:
            if struct_name in task_lower and "create" in task_lower:
                result = self.create_folder_structure(struct_name)
                return AgentResponse(
                    success=result["success"],
                    result=result,
                    message=f"Created {struct_name} folder structure"
                )

        # Suggest structure
        if "suggest" in task_lower or "recommend" in task_lower:
            suggestion = self.suggest_structure()
            return AgentResponse(
                success=True,
                result=suggestion,
                message="Project structure suggestion generated"
            )

        # Default: return current structure and available actions
        return AgentResponse(
            success=True,
            result={
                "current_structure": self.scan_structure(),
                "available_structures": list(self._standard_structures.keys()),
                "capabilities": [cap.name for cap in self.get_capabilities()]
            },
            message="Architecture agent ready. Specify action: scan, create, suggest"
        )
