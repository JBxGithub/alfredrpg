"""
Node-RED 狀態檢查與 Flow 管理
使用 node-red-automation skill
"""

import sys
sys.path.insert(0, 'C:/Users/BurtClaw/openclaw_workspace/private skills/node-red-automation')
from client import NodeREDClient
import json
from datetime import datetime

def check_node_red_status():
    """檢查 Node-RED 狀態"""
    print('=' * 60)
    print('Node-RED 狀態檢查報告')
    print(f'時間: {datetime.now()}')
    print('=' * 60)
    
    # 連接 Node-RED
    client = NodeREDClient('localhost', 1880)
    
    # 檢查狀態
    print('\n=== 基本狀態 ===')
    is_running = client.is_running()
    print(f'運行中: {is_running}')
    
    if not is_running:
        print('錯誤: Node-RED 未運行')
        return False
    
    # 獲取 flows
    flows = client.get_flows()
    print(f'\nFlows 數量: {len(flows)}')
    
    # 分析 flows
    flow_tabs = [f for f in flows if f.get('type') == 'tab']
    print(f'Flow Tabs: {len(flow_tabs)}')
    
    print('\n=== Flow 列表 ===')
    for tab in flow_tabs:
        label = tab.get('label', 'Unnamed')
        flow_id = tab.get('id', 'unknown')
        disabled = tab.get('disabled', False)
        status = '禁用' if disabled else '啟用'
        info = tab.get('info', '')[:50] if tab.get('info') else ''
        print(f'  - {label}')
        print(f'    ID: {flow_id}')
        print(f'    狀態: {status}')
        if info:
            print(f'    說明: {info}...')
        print()
    
    # 統計節點類型
    node_types = {}
    for node in flows:
        node_type = node.get('type', 'unknown')
        if node_type not in ['tab', 'subflow']:
            node_types[node_type] = node_types.get(node_type, 0) + 1
    
    print('\n=== 節點類型統計 ===')
    for node_type, count in sorted(node_types.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f'  {node_type}: {count}')
    
    # 獲取設置
    settings = client.get_settings()
    print(f'\n=== 版本信息 ===')
    print(f'Node-RED 版本: {settings.get("version", "unknown")}')
    
    return True

def export_flows_backup():
    """導出 Flows 備份"""
    print('\n' + '=' * 60)
    print('導出 Flows 備份')
    print('=' * 60)
    
    client = NodeREDClient('localhost', 1880)
    
    # 導出 flows
    flows_json = client.export_flows_json()
    
    # 保存到文件
    backup_file = f'flows_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(flows_json)
    
    print(f'備份已保存: {backup_file}')
    print(f'文件大小: {len(flows_json)} bytes')
    
    return backup_file

def check_flow_health():
    """檢查 Flow 健康狀態"""
    print('\n' + '=' * 60)
    print('Flow 健康檢查')
    print('=' * 60)
    
    client = NodeREDClient('localhost', 1880)
    flows = client.get_flows()
    
    issues = []
    
    # 檢查重複 ID
    ids = [f.get('id') for f in flows if f.get('id')]
    duplicate_ids = [id for id in set(ids) if ids.count(id) > 1]
    if duplicate_ids:
        issues.append(f'發現重複 ID: {len(duplicate_ids)} 個')
    
    # 檢查無效連接
    for node in flows:
        if 'wires' in node:
            wires = node.get('wires', [])
            for wire_group in wires:
                for target_id in wire_group:
                    if target_id not in ids:
                        issues.append(f'無效連接: {node.get("id", "unknown")} -> {target_id}')
    
    # 檢查未使用的節點
    all_targets = set()
    for node in flows:
        if 'wires' in node:
            for wire_group in node.get('wires', []):
                all_targets.update(wire_group)
    
    unused_nodes = []
    for node in flows:
        if node.get('type') not in ['tab', 'subflow', 'comment']:
            node_id = node.get('id')
            if node_id not in all_targets and not node.get('wires'):
                unused_nodes.append(node.get('name', node_id))
    
    if unused_nodes:
        issues.append(f'可能未使用的節點: {len(unused_nodes)} 個')
    
    if issues:
        print('\n發現問題:')
        for issue in issues[:10]:  # 只顯示前10個
            print(f'  ⚠️ {issue}')
    else:
        print('\n✅ 沒有發現明顯問題')
    
    return len(issues) == 0

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'export':
            export_flows_backup()
        elif sys.argv[1] == 'health':
            check_flow_health()
        else:
            check_node_red_status()
    else:
        check_node_red_status()
        check_flow_health()
