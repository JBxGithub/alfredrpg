"""
檢查數據寫入狀態
"""
import psycopg2
from datetime import datetime, timezone

conn = psycopg2.connect(
    host='localhost', port=5432, database='trading_db',
    user='postgres', password='PostgresqL'
)
cursor = conn.cursor()

# Check Futu data count today
cursor.execute('''
    SELECT COUNT(*), MAX(timestamp), MIN(timestamp)
    FROM raw_market_data 
    WHERE source = 'futu_opend'
    AND timestamp > CURRENT_DATE
''')
count, latest, earliest = cursor.fetchone()

print(f'今日 Futu 數據: {count} 條')
if latest and earliest:
    now = datetime.now(timezone.utc)
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=timezone.utc)
    diff = (now - latest).total_seconds() / 60
    print(f'最新: {latest.strftime("%H:%M:%S")} ({diff:.1f} 分鐘前)')
    print(f'最早: {earliest.strftime("%H:%M:%S")}')

# Check all sources
cursor.execute('''
    SELECT source, COUNT(*) 
    FROM raw_market_data 
    WHERE timestamp > CURRENT_DATE
    GROUP BY source
    ORDER BY COUNT(*) DESC
''')
print('\n今日數據來源統計:')
for r in cursor.fetchall():
    print(f'  {r[0]}: {r[1]} 條')

cursor.close()
conn.close()
