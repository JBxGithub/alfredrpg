"""
技能分析引擎 - 分析技能生態
"""

from typing import List, Dict, Any
from collections import defaultdict


class SkillAnalyzer:
    """分析技能生態系統"""
    
    def __init__(self):
        self.stats = {}
    
    def analyze(self, skills: List[Dict]) -> Dict[str, Any]:
        """分析技能列表"""
        if not skills:
            return {'error': 'No skills found'}
        
        analysis = {
            'total_skills': len(skills),
            'categories': self._analyze_categories(skills),
            'versions': self._analyze_versions(skills),
            'duplicates': self._find_duplicates(skills),
            'size_stats': self._analyze_sizes(skills),
            'recommendations': self._generate_recommendations(skills)
        }
        
        return analysis
    
    def _analyze_categories(self, skills: List[Dict]) -> Dict:
        """分析分類分佈"""
        categories = defaultdict(list)
        
        for skill in skills:
            category = skill.get('category', 'uncategorized')
            categories[category].append(skill['name'])
        
        return dict(categories)
    
    def _analyze_versions(self, skills: List[Dict]) -> Dict:
        """分析版本分佈"""
        version_count = defaultdict(int)
        
        for skill in skills:
            version = skill.get('version', 'unknown')
            version_count[version] += 1
        
        return dict(version_count)
    
    def _find_duplicates(self, skills: List[Dict]) -> List[Dict]:
        """識別可能的重複"""
        duplicates = []
        names = {}
        
        for skill in skills:
            name = skill['name'].lower()
            if name in names:
                duplicates.append({
                    'name': skill['name'],
                    'paths': [names[name], skill['path']]
                })
            else:
                names[name] = skill['path']
        
        return duplicates
    
    def _analyze_sizes(self, skills: List[Dict]) -> Dict:
        """分析大小統計"""
        sizes = [s.get('size', 0) for s in skills]
        
        if not sizes:
            return {}
        
        return {
            'total_size': sum(sizes),
            'average_size': sum(sizes) / len(sizes),
            'max_size': max(sizes),
            'min_size': min(sizes)
        }
    
    def _generate_recommendations(self, skills: List[Dict]) -> List[str]:
        """生成建議"""
        recommendations = []
        
        # 檢查無分類的技能
        uncategorized = [s for s in skills if s.get('category') == 'uncategorized']
        if uncategorized:
            recommendations.append(f"{len(uncategorized)} 個技能未分類，建議添加 category")
        
        # 檢查無版本號的技能
        no_version = [s for s in skills if s.get('version') == 'unknown']
        if no_version:
            recommendations.append(f"{len(no_version)} 個技能無版本號")
        
        return recommendations
