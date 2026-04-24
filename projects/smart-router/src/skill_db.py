import sqlite3
import json
import os
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Skill:
    name: str
    description: str
    keywords: List[str]
    category: str
    embedding: Optional[List[float]] = None


class SkillDatabase:
    def __init__(self, db_path: str = "data/skills.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT NOT NULL,
                    keywords TEXT NOT NULL,
                    category TEXT NOT NULL,
                    embedding TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def add_skill(self, skill: Skill) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO skills (name, description, keywords, category, embedding)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    skill.name,
                    skill.description,
                    json.dumps(skill.keywords),
                    skill.category,
                    json.dumps(skill.embedding) if skill.embedding else None
                ))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error adding skill: {e}")
            return False
    
    def get_skill(self, name: str) -> Optional[Skill]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM skills WHERE name = ?", (name,)
            ).fetchone()
            if row:
                return self._row_to_skill(row)
        return None
    
    def get_all_skills(self) -> List[Skill]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM skills").fetchall()
            return [self._row_to_skill(row) for row in rows]
    
    def update_embedding(self, name: str, embedding: List[float]):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE skills SET embedding = ? WHERE name = ?",
                (json.dumps(embedding), name)
            )
            conn.commit()
    
    def delete_skill(self, name: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM skills WHERE name = ?", (name,))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting skill: {e}")
            return False
    
    def _row_to_skill(self, row: sqlite3.Row) -> Skill:
        return Skill(
            name=row["name"],
            description=row["description"],
            keywords=json.loads(row["keywords"]),
            category=row["category"],
            embedding=json.loads(row["embedding"]) if row["embedding"] else None
        )
    
    def get_skill_count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute("SELECT COUNT(*) FROM skills").fetchone()
            return result[0] if result else 0
    
    def clear_all(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM skills")
            conn.commit()


def scan_skills_from_directory(skills_dir: str) -> List[Skill]:
    skills = []
    skill_md_files = []
    
    for root, dirs, files in os.walk(skills_dir):
        for f in files:
            if f.endswith('.md') and f != 'SKILL.md':
                skill_md_files.append(os.path.join(root, f))
            elif f == 'SKILL.md':
                skill_md_files.append(os.path.join(root, f))
    
    for skill_file in skill_md_files:
        try:
            with open(skill_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            skill_name = os.path.basename(os.path.dirname(skill_file))
            if skill_name == 'skills':
                skill_name = os.path.basename(os.path.dirname(os.path.dirname(skill_file)))
            
            description = ""
            keywords = []
            
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('#'):
                    description = line.lstrip('#').strip()
                    for j in range(i+1, min(i+10, len(lines))):
                        next_line = lines[j].strip()
                        if next_line.startswith('#'):
                            break
                        if next_line:
                            description += " " + next_line
                
                line_lower = line.lower()
                if any(k in line_lower for k in ['keyword', '標籤', '標志']):
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        keywords.extend([k.strip().lower() for k in parts[1].split(',')])
            
            if not keywords:
                words = description.lower().split()
                keywords = [w for w in words if len(w) > 3][:5]
            
            category = "general"
            for cat in ['web', 'browser', 'code', 'data', 'system', 'automation', 'search', 'control']:
                if cat in skill_name.lower() or cat in description.lower():
                    category = cat
                    break
            
            skills.append(Skill(
                name=skill_name,
                description=description.strip(),
                keywords=keywords,
                category=category
            ))
        except Exception as e:
            print(f"Error scanning {skill_file}: {e}")
    
    return skills


if __name__ == "__main__":
    db = SkillDatabase()
    print(f"Database initialized at: {db.db_path}")
    print(f"Current skill count: {db.get_skill_count()}")
