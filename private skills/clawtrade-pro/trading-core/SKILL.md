# Trading Core Skill

> Futu API 和 Investing.com 數據獲取核心模塊

## 功能

- Futu OpenD API 連接和數據獲取
- Investing.com 網頁數據抓取
- 實時價格數據同步
- 歷史 K 線數據獲取
- 賬戶資訊查詢

## 使用方法

```python
from trading_core import FutuClient, InvestingClient

# Futu API
futu = FutuClient(host="127.0.0.1", port=11111)
quote = futu.get_quote("US.TQQQ")

# Investing.com
investing = InvestingClient()
data = investing.get_technical_summary("TQQQ")
```

## CLI 命令

```bash
# 獲取實時報價
python -m trading_core --action quote --symbol TQQQ

# 獲取歷史數據
python -m trading_core --action history --symbol TQQQ --days 60

# 同步賬戶資訊
python -m trading_core --action account
```

## 配置

編輯 `config.yaml`:
```yaml
futu:
  host: "127.0.0.1"
  port: 11111
  
investing:
  base_url: "https://www.investing.com"
  timeout: 30
```
