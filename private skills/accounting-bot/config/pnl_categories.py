"""
P&L 分類配置 - 44項標準損益表分類
來源: Pnl_FY25-26 C14-C53
"""

# P&L 分類對照表
PNL_CATEGORIES = {
    # Revenue
    '收入': 'REVENUE',
    '營收': 'REVENUE',
    'Rent Received': 'REVENUE',
    'Interest (received)': 'REVENUE',
    
    # Cost
    '成本': 'COST',
    '直接成本': 'COST',
    
    # Expenses - Accounting & Legal
    '會計法律': '14 - Accounting & Legal',
    'Accounting & Legal': '14 - Accounting & Legal',
    
    # Expenses - Accounting - Fines
    '罰款': '15 - Accounting - Fines',
    'Accounting - Fines': '15 - Accounting - Fines',
    
    # Expenses - Admin General - Bank Charges
    '銀行手續費': '16 - Admin General - Bank Charges',
    'Admin General - Bank Charges': '16 - Admin General - Bank Charges',
    'bank charge': '16 - Admin General - Bank Charges',
    
    # Expenses - Audit Fees
    '審計': '17 - Audit Fees',
    'Audit Fees': '17 - Audit Fees',
    
    # Expenses - Advertising
    '廣告': '18 - Advertising',
    '行銷': '18 - Advertising',
    'Advertising': '18 - Advertising',
    'marketing': '18 - Advertising',
    
    # Expenses - Bad Debts
    '壞帳': '19 - Bad Debts',
    'Bad Debts': '19 - Bad Debts',
    
    # Expenses - Bad Debts Recovered
    'Bad Debts Recovered': '20 - Bad Debts Recovered',
    
    # Expenses - Claims
    '賠償': '21 - Claims',
    '保險': '21 - Claims',
    'Claims': '21 - Claims',
    'insurance': '21 - Claims',
    
    # Expenses - Computer Costs - Equipment
    '電腦設備': '22 - Computer Costs - Equipment',
    '設備': '22 - Computer Costs - Equipment',
    'Computer Costs - Equipment': '22 - Computer Costs - Equipment',
    
    # Expenses - Computer Costs - Communications
    '通訊': '23 - Computer Costs - Communications, Subcription, API cost',
    '軟件': '23 - Computer Costs - Communications, Subcription, API cost',
    'API': '23 - Computer Costs - Communications, Subcription, API cost',
    'subscription': '23 - Computer Costs - Communications, Subcription, API cost',
    'Computer Costs - Communications, Subcription, API cost': '23 - Computer Costs - Communications, Subcription, API cost',
    
    # Expenses - Depreciation
    '折舊': '24 - Depreciation',
    'Depreciation': '24 - Depreciation',
    
    # Expenses - Diesel, Gasline
    '柴油': '25 - Diesel, Gasline',
    'Diesel, Gasline': '25 - Diesel, Gasline',
    
    # Expenses - Directors Fees
    '董事費': '26 - Directors Fees',
    'Directors Fees': '26 - Directors Fees',
    
    # Expenses - Entertainment
    '餐飲': '27 - Entertainment',
    '交際': '27 - Entertainment',
    'Entertainment': '27 - Entertainment',
    'dining': '27 - Entertainment',
    'restaurant': '27 - Entertainment',
    
    # Expenses - Fork Hoist Hire
    '叉車': '28 - Fork Hoist Hire',
    'Fork Hoist Hire': '28 - Fork Hoist Hire',
    
    # Expenses - Fringe Benefit Tax
    '福利稅': '29 - Fringe Benefit Tax',
    'Fringe Benefit Tax': '29 - Fringe Benefit Tax',
    
    # Expenses - Admin Fee
    '行政費': '30 - Admin Fee',
    'Admin Fee': '30 - Admin Fee',
    'admin fee': '30 - Admin Fee',
    
    # Expenses - Gain on Sale of Assets
    'Gain on Sale of Assets (Taxable)': '31 - Gain on Sale of Assets (Taxable)',
    'Gain on Sale of Assets (Non Taxable)': '32 - Gain on Sale of Assets (Non Taxable)',
    
    # Expenses - Hire & Lease
    '租賃': '33 - Hire & Lease - Equipment Wise',
    'Hire & Lease - Equipment Wise': '33 - Hire & Lease - Equipment Wise',
    'lease': '33 - Hire & Lease - Equipment Wise',
    'rental': '33 - Hire & Lease - Equipment Wise',
    
    # Expenses - Insurance (duplicate with Claims, mapped to Insurance)
    'Insurance': '34 - Insurance',
    
    # Expenses - Operating General
    '一般營運': '35 - Operating General',
    'Operating General': '35 - Operating General',
    
    # Expenses - Operating General - Cleaning
    '清潔': '36 - Operating General - Cleaning',
    'Operating General - Cleaning': '36 - Operating General - Cleaning',
    'cleaning': '36 - Operating General - Cleaning',
    
    # Expenses - Operating General - Electricity, Water
    '水電': '37 - Operating General - Electricity, Water Supply',
    'Operating General - Electricity, Water Supply': '37 - Operating General - Electricity, Water Supply',
    'electricity': '37 - Operating General - Electricity, Water Supply',
    'water': '37 - Operating General - Electricity, Water Supply',
    
    # Expenses - Petrol & Oil
    '汽油': '38 - Petrol & Oil',
    '交通': '38 - Petrol & Oil',
    'Petrol & Oil': '38 - Petrol & Oil',
    'petrol': '38 - Petrol & Oil',
    'fuel': '38 - Petrol & Oil',
    
    # Expenses - Postage & Courier
    '郵寄': '39 - Postage & Courier Costs',
    '快遞': '39 - Postage & Courier Costs',
    'Postage & Courier Costs': '39 - Postage & Courier Costs',
    'courier': '39 - Postage & Courier Costs',
    'postage': '39 - Postage & Courier Costs',
    
    # Expenses - Printing & Stationery
    '文具': '40 - Printing & Stationery',
    '印刷': '40 - Printing & Stationery',
    '辦公': '40 - Printing & Stationery',
    'Printing & Stationery': '40 - Printing & Stationery',
    'stationery': '40 - Printing & Stationery',
    
    # Expenses - Rates
    '稅費': '41 - Rates',
    'Rates': '41 - Rates',
    'tax': '41 - Rates',
    
    # Expenses - Rent
    '租金': '42 - Rent',
    'Rent': '42 - Rent',
    
    # Expenses - R & M
    '維修': '43 - R & M',
    'R & M': '43 - R & M',
    'repair': '43 - R & M',
    'maintenance': '43 - R & M',
    
    # Expenses - Road User Distance Tax
    '道路稅': '44 - Road User Distance Tax',
    'Road User Distance Tax': '44 - Road User Distance Tax',
    
    # Expenses - Stowage Aids
    '裝載輔助': '45 - Stowage Aids',
    'Stowage Aids': '45 - Stowage Aids',
    
    # Expenses - Telephones, Mobile
    '電話': '46 - Telephones, Mobile',
    '手機': '46 - Telephones, Mobile',
    'Telephones, Mobile': '46 - Telephones, Mobile',
    'phone': '46 - Telephones, Mobile',
    'mobile': '46 - Telephones, Mobile',
    
    # Expenses - Travelling & Accommodation - Overseas
    '海外差旅': '47 - Travelling & Accommodation - Overseas',
    'Travelling & Accommodation - Overseas': '47 - Travelling & Accommodation - Overseas',
    'overseas travel': '47 - Travelling & Accommodation - Overseas',
    
    # Expenses - Travelling & Accommodation Local
    '本地差旅': '48 - Travelling & Accommodation Local',
    '差旅': '48 - Travelling & Accommodation Local',
    'Travelling & Accommodation Local': '48 - Travelling & Accommodation Local',
    'travel': '48 - Travelling & Accommodation Local',
    'accommodation': '48 - Travelling & Accommodation Local',
    
    # Expenses - Wages & Salaries
    '薪資': '49 - Wages & Salaries',
    'Wages & Salaries': '49 - Wages & Salaries',
    'salary': '49 - Wages & Salaries',
    'wage': '49 - Wages & Salaries',
    
    # Expenses - Wages & Salaries - Allowances
    '津貼': '50 - Wages & Salaries - Allowances',
    'Wages & Salaries - Allowances': '50 - Wages & Salaries - Allowances',
    'allowance': '50 - Wages & Salaries - Allowances',
    
    # Expenses - Annual Bonus
    '年終獎金': '51 - Annual Bonus',
    'Annual Bonus': '51 - Annual Bonus',
    'bonus': '51 - Annual Bonus',
}

# 預設分類
DEFAULT_CATEGORY = '33 - Admin General'
DEFAULT_TYPE = 'EXPENSES'

def get_pnl_category(category: str) -> str:
    """
    取得 P&L 分類
    
    Args:
        category: 消費類別 (中文或英文)
    
    Returns:
        P&L 分類編號與名稱
    """
    if not category:
        return DEFAULT_CATEGORY
    
    # 直接匹配
    if category in PNL_CATEGORIES:
        return PNL_CATEGORIES[category]
    
    # 模糊匹配 - 關鍵字包含
    for key, value in PNL_CATEGORIES.items():
        if key.lower() in category.lower() or category.lower() in key.lower():
            return value
    
    return DEFAULT_CATEGORY


def get_pnl_type(category: str) -> str:
    """
    判斷 P&L 類型 (REVENUE/COST/EXPENSES)
    
    Args:
        category: 消費類別
    
    Returns:
        'REVENUE', 'COST', 或 'EXPENSES'
    """
    pnl_category = get_pnl_category(category)
    
    if 'REVENUE' in pnl_category:
        return 'REVENUE'
    elif 'COST' in pnl_category and pnl_category != 'COST':
        return 'COST'
    elif category in ['成本', '直接成本', 'Cost', 'COST']:
        return 'COST'
    else:
        return 'EXPENSES'


def simplify_merchant(merchant: str) -> str:
    """
    簡化商家名稱
    
    Args:
        merchant: 原始商家名稱
    
    Returns:
        簡化後的商家名稱 (最多30字元)
    """
    if not merchant:
        return '未知商家'
    
    merchant_str = str(merchant)
    
    # 淘寶相關簡化
    if '淘宝' in merchant_str or '淘寶' in merchant_str or 'taobao' in merchant_str.lower():
        return '淘寶'
    
    # 支付寶簡化
    if '支付宝' in merchant_str or '支付寶' in merchant_str or 'alipay' in merchant_str.lower():
        return '支付寶'
    
    # 微信簡化
    if '微信' in merchant_str or 'wechat' in merchant_str.lower() or 'weixin' in merchant_str.lower():
        return '微信支付'
    
    # 限制長度
    return merchant_str[:30]


def format_date_for_sheets(date_str: str) -> str:
    """
    格式化日期為 Google Sheets 文字格式
    避免 Excel 自動轉換為序列號
    
    Args:
        date_str: 日期字串
    
    Returns:
        帶前導符號的日期字串
    """
    if not date_str:
        from datetime import datetime
        date_str = datetime.now().strftime('%Y/%m/%d')
    
    # 確保有前導符號防止 Excel 日期轉換
    if not str(date_str).startswith("'"):
        return "'" + str(date_str)
    return str(date_str)
