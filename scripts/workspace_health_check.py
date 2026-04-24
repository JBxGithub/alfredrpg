#!/usr/bin/env python3
"""
工作區健康檢查腳本
自動掃描亂建檔案、重複命名等問題
"""

import os
import json
from datetime import datetime
from pathlib import Path

WORKSPACE = "C:/Users/BurtClaw/openclaw_workspace"
REPORT_FILE = f"{WORKSPACE}/memory/workspace-health-check.json"

def check_root_files():
    """檢查根目錄亂建檔案"""
    suspicious = []
    temp_patterns = ['temp', 'test', 'backup', 'draft', 'new', 'copy', '.tmp', '.bak']
    
    for item in os.listdir(WORKSPACE):
        item_lower = item.lower()
        if any(pattern in item_lower for pattern in temp_patterns):
            suspicious.append({
                'type': 'suspicious_root_file',
                'path': item,
                'suggestion': 'Move to appropriate subdirectory'
            })
    
    return suspicious

def check_duplicate_names():
    """檢查重複命名"""
    duplicates = []
    
    # 檢查 skills vs private skills
    skills = set(os.listdir(f"{WORKSPACE}/skills")) if os.path.exists(f"{WORKSPACE}/skills") else set()
    private_skills = set(os.listdir(f"{WORKSPACE}/private skills")) if os.path.exists(f"{WORKSPACE}/private skills") else set()
    
    for s in skills:
        s_clean = s.lower().replace('-', '').replace('_', '').replace(' ', '')
        for ps in private_skills:
            ps_clean = ps.lower().replace('-', '').replace('_', '').replace(' ', '')
            if s_clean == ps_clean and s != ps:
                duplicates.append({
                    'type': 'duplicate_name',
                    'path1': f"skills/{s}",
                    'path2': f"private skills/{ps}",
                    'suggestion': 'Consolidate into one location'
                })
    
    return duplicates

def check_projects_vs_skills():
    """檢查 projects 同 skills 重複"""
    duplicates = []
    
    projects = set(os.listdir(f"{WORKSPACE}/projects")) if os.path.exists(f"{WORKSPACE}/projects") else set()
    all_skills = set()
    
    if os.path.exists(f"{WORKSPACE}/skills"):
        all_skills.update(os.listdir(f"{WORKSPACE}/skills"))
    if os.path.exists(f"{WORKSPACE}/private skills"):
        all_skills.update(os.listdir(f"{WORKSPACE}/private skills"))
    
    for p in projects:
        p_clean = p.lower().replace('-', '').replace('_', '').replace(' ', '').replace('futu', '').replace('trading', '').replace('pro', '').replace('bot', '')
        for s in all_skills:
            s_clean = s.lower().replace('-', '').replace('_', '').replace(' ', '').replace('futu', '').replace('trading', '').replace('pro', '').replace('bot', '')
            if p_clean == s_clean:
                duplicates.append({
                    'type': 'project_skill_duplicate',
                    'project': f"projects/{p}",
                    'skill': s,
                    'suggestion': 'Review if consolidation needed'
                })
    
    return duplicates

def generate_report():
    """生成健康檢查報告"""
    issues = []
    issues.extend(check_root_files())
    issues.extend(check_duplicate_names())
    issues.extend(check_projects_vs_skills())
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_issues': len(issues),
        'issues': issues,
        'summary': {
            'suspicious_root_files': len([i for i in issues if i['type'] == 'suspicious_root_file']),
            'duplicate_names': len([i for i in issues if i['type'] == 'duplicate_name']),
            'project_skill_duplicates': len([i for i in issues if i['type'] == 'project_skill_duplicate'])
        }
    }
    
    # 保存報告
    with open(REPORT_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

if __name__ == '__main__':
    report = generate_report()
    print(f"Workspace Health Check Complete")
    print(f"Total Issues: {report['total_issues']}")
    print(f"Report saved to: {REPORT_FILE}")
