"""Skill validator - validates skill structure and content."""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional


class SkillValidator:
    """Validates OpenClaw skill structure and content."""
    
    REQUIRED_FILES = ["SKILL.md", "src/__init__.py", "src/skill.py"]
    OPTIONAL_FILES = ["config.yaml", "README.md", "tests/test_skill.py"]
    
    REQUIRED_SKILLMD_FIELDS = ["name", "description", "version"]
    VALID_CATEGORIES = [
        "automation", "browser", "code", "data", "system", 
        "search", "control", "analysis", "notification", "utility"
    ]
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate(self, skill_path: str) -> Dict[str, Any]:
        """
        Validate a skill directory.
        
        Returns:
            Validation result with 'valid', 'errors', and 'warnings'
        """
        self.errors = []
        self.warnings = []
        
        skill_dir = Path(skill_path)
        
        if not skill_dir.exists():
            return {
                "valid": False,
                "errors": [f"Skill directory does not exist: {skill_path}"],
                "warnings": []
            }
        
        # Check required files
        self._check_required_files(skill_dir)
        
        # Validate SKILL.md
        if (skill_dir / "SKILL.md").exists():
            self._validate_skill_md(skill_dir / "SKILL.md")
        
        # Validate Python files
        if (skill_dir / "src" / "skill.py").exists():
            self._validate_python_files(skill_dir)
        
        # Validate config.yaml
        if (skill_dir / "config.yaml").exists():
            self._validate_config(skill_dir / "config.yaml")
        
        # Check naming conventions
        self._check_naming(skill_dir)
        
        return {
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings
        }
    
    def _check_required_files(self, skill_dir: Path):
        """Check that all required files exist."""
        for file_path in self.REQUIRED_FILES:
            full_path = skill_dir / file_path
            if not full_path.exists():
                self.errors.append(f"Missing required file: {file_path}")
    
    def _validate_skill_md(self, skill_md_path: Path):
        """Validate SKILL.md content."""
        content = skill_md_path.read_text(encoding='utf-8')
        
        # Check frontmatter
        if not content.startswith('---'):
            self.errors.append("SKILL.md must start with YAML frontmatter (---)")
            return
        
        # Extract frontmatter
        parts = content.split('---', 2)
        if len(parts) < 3:
            self.errors.append("SKILL.md frontmatter not properly closed")
            return
        
        try:
            frontmatter = yaml.safe_load(parts[1])
        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML frontmatter: {e}")
            return
        
        if not isinstance(frontmatter, dict):
            self.errors.append("SKILL.md frontmatter must be a dictionary")
            return
        
        # Check required fields
        for field in self.REQUIRED_SKILLMD_FIELDS:
            if field not in frontmatter:
                self.errors.append(f"SKILL.md missing required field: {field}")
        
        # Validate name format
        if 'name' in frontmatter:
            name = frontmatter['name']
            if not re.match(r'^[a-z0-9-]+$', name):
                self.errors.append(f"Invalid skill name '{name}': must be lowercase alphanumeric with hyphens")
        
        # Validate category
        if 'metadata' in frontmatter and 'openclaw' in frontmatter['metadata']:
            category = frontmatter['metadata']['openclaw'].get('category', '')
            if category and category not in self.VALID_CATEGORIES:
                self.warnings.append(f"Unusual category '{category}': consider using one of {self.VALID_CATEGORIES}")
        
        # Check for description in body
        body = parts[2]
        if len(body.strip()) < 50:
            self.warnings.append("SKILL.md body is very short, consider adding more documentation")
        
        # Check for sections
        required_sections = ['## Features', '## Usage']
        for section in required_sections:
            if section not in body:
                self.warnings.append(f"SKILL.md missing recommended section: {section}")
    
    def _validate_python_files(self, skill_dir: Path):
        """Validate Python source files."""
        init_file = skill_dir / "src" / "__init__.py"
        skill_file = skill_dir / "src" / "skill.py"
        
        # Check __init__.py exports
        if init_file.exists():
            init_content = init_file.read_text(encoding='utf-8')
            if 'from .skill import' not in init_content:
                self.warnings.append("src/__init__.py should export from skill module")
        
        # Check skill.py structure
        if skill_file.exists():
            skill_content = skill_file.read_text(encoding='utf-8')
            
            # Check for class definition
            if 'class ' not in skill_content:
                self.errors.append("src/skill.py must contain a class definition")
            
            # Check for execute method
            if 'def execute(' not in skill_content:
                self.warnings.append("src/skill.py should have an execute() method")
            
            # Check for docstrings
            if '"""' not in skill_content and "'''" not in skill_content:
                self.warnings.append("src/skill.py should have module docstring")
            
            # Check for version
            if 'VERSION' not in skill_content:
                self.warnings.append("src/skill.py should define a VERSION")
    
    def _validate_config(self, config_path: Path):
        """Validate config.yaml."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if not isinstance(config, dict):
                self.errors.append("config.yaml must be a dictionary")
                return
            
            # Check for version
            if 'version' not in config:
                self.warnings.append("config.yaml missing 'version' field")
            
            # Check for settings
            if 'settings' not in config:
                self.warnings.append("config.yaml missing 'settings' section")
            
        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML in config.yaml: {e}")
    
    def _check_naming(self, skill_dir: Path):
        """Check naming conventions."""
        skill_name = skill_dir.name
        
        # Check directory name
        if not re.match(r'^[a-z0-9-]+$', skill_name):
            self.errors.append(f"Skill directory name '{skill_name}' should be lowercase alphanumeric with hyphens")
        
        # Check if name matches SKILL.md
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text(encoding='utf-8')
            match = re.search(r'^name:\s*(.+)$', content, re.MULTILINE)
            if match:
                md_name = match.group(1).strip()
                if md_name != skill_name:
                    self.errors.append(f"SKILL.md name '{md_name}' doesn't match directory name '{skill_name}'")
    
    def quick_check(self, skill_path: str) -> bool:
        """Quick validation - only check required files."""
        skill_dir = Path(skill_path)
        
        if not skill_dir.exists():
            return False
        
        for file_path in self.REQUIRED_FILES:
            if not (skill_dir / file_path).exists():
                return False
        
        return True


class BatchValidator:
    """Validates multiple skills at once."""
    
    def __init__(self, skills_dir: str):
        self.skills_dir = Path(skills_dir)
        self.validator = SkillValidator()
    
    def validate_all(self) -> Dict[str, Any]:
        """Validate all skills in directory."""
        results = {
            "total": 0,
            "valid": 0,
            "invalid": 0,
            "details": {}
        }
        
        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                results["total"] += 1
                result = self.validator.validate(str(skill_dir))
                results["details"][skill_dir.name] = result
                
                if result["valid"]:
                    results["valid"] += 1
                else:
                    results["invalid"] += 1
        
        return results
    
    def generate_report(self, results: Dict) -> str:
        """Generate validation report."""
        lines = [
            "# Skill Validation Report",
            "",
            f"**Total Skills**: {results['total']}",
            f"**Valid**: {results['valid']} ✅",
            f"**Invalid**: {results['invalid']} ❌",
            "",
            "## Details",
            ""
        ]
        
        for skill_name, result in results["details"].items():
            status = "✅" if result["valid"] else "❌"
            lines.append(f"### {skill_name} {status}")
            
            if result["errors"]:
                lines.append("**Errors:**")
                for error in result["errors"]:
                    lines.append(f"- ❌ {error}")
            
            if result["warnings"]:
                lines.append("**Warnings:**")
                for warning in result["warnings"]:
                    lines.append(f"- ⚠️ {warning}")
            
            lines.append("")
        
        return "\n".join(lines)


if __name__ == "__main__":
    # Test validator
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python validator.py <skill_path>")
        sys.exit(1)
    
    skill_path = sys.argv[1]
    validator = SkillValidator()
    result = validator.validate(skill_path)
    
    print(f"Validation Result: {'✅ Valid' if result['valid'] else '❌ Invalid'}")
    
    if result["errors"]:
        print("\nErrors:")
        for error in result["errors"]:
            print(f"  ❌ {error}")
    
    if result["warnings"]:
        print("\nWarnings:")
        for warning in result["warnings"]:
            print(f"  ⚠️ {warning}")
