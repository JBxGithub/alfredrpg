"""Skill generator - creates new skill scaffolding."""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional


class SkillGenerator:
    """Generates new OpenClaw skill scaffolding."""
    
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir) if output_dir else Path.home() / "openclaw_workspace" / "skills"
        self.templates_dir = Path(__file__).parent / "templates"
    
    def create(self, name: str, category: str = "automation", 
               description: Optional[str] = None) -> str:
        """
        Create a new skill with standard structure.
        
        Returns:
            Path to created skill directory
        """
        # Validate name
        if not re.match(r'^[a-z0-9-]+$', name):
            raise ValueError("Skill name must be lowercase alphanumeric with hyphens")
        
        # Create directory structure
        skill_dir = self.output_dir / name
        if skill_dir.exists():
            raise FileExistsError(f"Skill '{name}' already exists at {skill_dir}")
        
        skill_dir.mkdir(parents=True)
        (skill_dir / "src").mkdir()
        (skill_dir / "tests").mkdir()
        
        # Generate files
        self._generate_skill_md(skill_dir, name, category, description)
        self._generate_skill_py(skill_dir, name)
        self._generate_config_yaml(skill_dir, name, category)
        self._generate_test_py(skill_dir, name)
        self._generate_readme(skill_dir, name, description)
        
        return str(skill_dir)
    
    def _generate_skill_md(self, skill_dir: Path, name: str, category: str, 
                          description: Optional[str]):
        """Generate SKILL.md"""
        desc = description or f"{name.replace('-', ' ').title()} skill for OpenClaw"
        
        content = f"""---
name: {name}
description: "{desc}"
version: 1.0.0
metadata:
  openclaw:
    tags: [{category}]
    category: {category}
    auto_load: false
---

# {name.replace('-', ' ').title()}

{desc}

## Features

- Feature 1
- Feature 2
- Feature 3

## Usage

```python
# Example usage
from {name.replace('-', '_')} import Skill

skill = Skill()
result = skill.execute()
```

## Configuration

```yaml
# config.yaml
setting1: value1
setting2: value2
```

## Dependencies

- Python 3.8+
- openclaw-core

## Installation

```bash
# Copy to skills directory
cp -r {name} ~/.openclaw/skills/

# Initialize
python -m {name} init
```

## License

MIT
"""
        
        (skill_dir / "SKILL.md").write_text(content, encoding='utf-8')
    
    def _generate_skill_py(self, skill_dir: Path, name: str):
        """Generate skill.py"""
        class_name = ''.join(word.title() for word in name.split('-'))
        
        content = f"""\"\"\"
{name.replace('-', ' ').title()} Skill

Author: 呀鬼 (Alfred)
Version: 1.0.0
\"\"\"

from typing import Dict, Any, Optional
from pathlib import Path
import yaml


class {class_name}Skill:
    \"\"\"
    {name.replace('-', ' ').title()} skill implementation.
    \"\"\"
    
    VERSION = "1.0.0"
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        \"\"\"Load configuration from YAML file.\"\"\"
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {{}}
        return {{}}
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        \"\"\"
        Execute the skill.
        
        Args:
            **kwargs: Execution parameters
            
        Returns:
            Execution result
        \"\"\"
        try:
            # TODO: Implement skill logic
            result = self._run_logic(**kwargs)
            return {{
                "success": True,
                "result": result,
                "message": "Skill executed successfully"
            }}
        except Exception as e:
            return {{
                "success": False,
                "error": str(e),
                "message": f"Skill execution failed: {{e}}"
            }}
    
    def _run_logic(self, **kwargs) -> Any:
        \"\"\"Main skill logic - override this method.\"\"\"
        raise NotImplementedError("Subclasses must implement _run_logic()")
    
    def validate(self) -> bool:
        \"\"\"Validate skill configuration.\"\"\"
        # TODO: Add validation logic
        return True
    
    def get_info(self) -> Dict[str, str]:
        \"\"\"Get skill information.\"\"\"
        return {{
            "name": "{name}",
            "version": self.VERSION,
            "class": "{class_name}Skill"
        }}


# Convenience function
def execute(**kwargs) -> Dict[str, Any]:
    \"\"\"Execute skill with default configuration.\"\"\"
    skill = {class_name}Skill()
    return skill.execute(**kwargs)


if __name__ == "__main__":
    # Test execution
    result = execute()
    print(result)
"""
        
        (skill_dir / "src" / "__init__.py").write_text(
            f"from .skill import {class_name}Skill, execute\n",
            encoding='utf-8'
        )
        (skill_dir / "src" / "skill.py").write_text(content, encoding='utf-8')
    
    def _generate_config_yaml(self, skill_dir: Path, name: str, category: str):
        """Generate config.yaml"""
        content = f"""# {name} configuration
version: "1.0.0"
category: {category}

# Skill settings
settings:
  enabled: true
  debug: false
  
# Default parameters
defaults:
  param1: value1
  param2: value2

# Logging
logging:
  level: INFO
  file: logs/{name}.log
"""
        
        (skill_dir / "config.yaml").write_text(content, encoding='utf-8')
    
    def _generate_test_py(self, skill_dir: Path, name: str):
        """Generate test file"""
        class_name = ''.join(word.title() for word in name.split('-'))
        
        content = f"""\"\"\"
Tests for {name} skill.
\"\"\"

import unittest
from src.skill import {class_name}Skill


class Test{class_name}Skill(unittest.TestCase):
    \"\"\"Test cases for {class_name}Skill.\"\"\"
    
    def setUp(self):
        \"\"\"Set up test fixtures.\"\"\"
        self.skill = {class_name}Skill()
    
    def test_initialization(self):
        \"\"\"Test skill initialization.\"\"\"
        self.assertIsNotNone(self.skill)
        self.assertTrue(self.skill.validate())
    
    def test_get_info(self):
        \"\"\"Test get_info method.\"\"\"
        info = self.skill.get_info()
        self.assertEqual(info["name"], "{name}")
        self.assertEqual(info["version"], "1.0.0")
    
    def test_execute_not_implemented(self):
        \"\"\"Test that execute raises NotImplementedError.\"\"\"
        with self.assertRaises(NotImplementedError):
            self.skill._run_logic()
    
    def test_config_loading(self):
        \"\"\"Test configuration loading.\"\"\"
        config = self.skill.config
        self.assertIsInstance(config, dict)


if __name__ == "__main__":
    unittest.main()
"""
        
        (skill_dir / "tests" / "test_skill.py").write_text(content, encoding='utf-8')
        (skill_dir / "tests" / "__init__.py").write_text("", encoding='utf-8')
    
    def _generate_readme(self, skill_dir: Path, name: str, description: Optional[str]):
        """Generate README.md"""
        desc = description or f"{name.replace('-', ' ').title()} skill for OpenClaw"
        
        content = f"""# {name.replace('-', ' ').title()}

{desc}

## Quick Start

```bash
# Install
cp -r {name} ~/.openclaw/skills/

# Test
python -m pytest tests/

# Run
python -c "from src.skill import execute; print(execute())"
```

## Documentation

See [SKILL.md](SKILL.md) for detailed documentation.

## Development

```bash
# Run tests
python -m pytest tests/ -v

# Check coverage
python -m pytest tests/ --cov=src
```

## License

MIT License - see LICENSE file for details.
"""
        
        (skill_dir / "README.md").write_text(content, encoding='utf-8')


if __name__ == "__main__":
    # Test generator
    gen = SkillGenerator(output_dir="./test-output")
    try:
        path = gen.create("test-skill", "automation", "A test skill")
        print(f"Created skill at: {{path}}")
    except FileExistsError as e:
        print(f"Error: {{e}}")
