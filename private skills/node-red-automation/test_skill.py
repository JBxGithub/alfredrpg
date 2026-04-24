#!/usr/bin/env python3
"""Test Node-RED Automation Skill"""

import sys
sys.path.insert(0, '.')
from client import NodeREDClient

def test_node_red_skill():
    """測試 Node-RED Skill 功能"""
    
    # 測試連接 Node-RED
    client = NodeREDClient('localhost', 1880)
    
    # 測試 1: 檢查 Node-RED 是否運行
    print('=== 測試 1: 檢查 Node-RED 運行狀態 ===')
    try:
        is_running = client.is_running()
        print(f'Node-RED 運行中: {is_running}')
        if not is_running:
            print('錯誤: Node-RED 未運行，請先啟動 node-red')
            return False
    except Exception as e:
        print(f'連接失敗: {e}')
        return False
    
    # 測試 2: 獲取 Node-RED 信息
    print('\n=== 測試 2: 獲取 Node-RED 信息 ===')
    try:
        info = client.get_info()
        print(f'版本: {info.get("version", "未知")}')
        print(f'Node-RED 版本: {info.get("node-red", "未知")}')
    except Exception as e:
        print(f'獲取信息失敗: {e}')
    
    # 測試 3: 獲取所有 flows
    print('\n=== 測試 3: 獲取 Flows ===')
    try:
        flows = client.get_flows()
        print(f'Flows 數量: {len(flows)}')
        if flows:
            print(f'第一個 flow ID: {flows[0].get("id", "N/A")}')
            print(f'第一個 flow 類型: {flows[0].get("type", "N/A")}')
    except Exception as e:
        print(f'獲取 flows 失敗: {e}')
    
    # 測試 4: 獲取已安裝節點
    print('\n=== 測試 4: 獲取已安裝節點 ===')
    try:
        nodes = client.get_nodes()
        print(f'已安裝節點數量: {len(nodes)}')
        if nodes and isinstance(nodes, list):
            print(f'節點類型示例: {[n.get("id", "N/A") for n in nodes[:3]]}')
    except Exception as e:
        print(f'獲取節點失敗: {e}')
    
    # 測試 5: 獲取設置
    print('\n=== 測試 5: 獲取設置 ===')
    try:
        settings = client.get_settings()
        print(f'設置項目數量: {len(settings)}')
    except Exception as e:
        print(f'獲取設置失敗: {e}')
    
    print('\n=== 所有測試完成 ===')
    return True

if __name__ == '__main__':
    success = test_node_red_skill()
    sys.exit(0 if success else 1)
