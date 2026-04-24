# Alfred Accounting Bot - System Architecture & Rules

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User (WhatsApp)                           │
│              Send receipt image + commands                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              OpenClaw Gateway (Port 18789)                   │
│         - Receive WhatsApp messages                          │
│         - Trigger automation workflow                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Core Processing Engine                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Cron Job   │  │  AI Vision  │  │  P&L Classifier     │ │
│  │(30s check)  │  │  (OCR)      │  │ (Auto/Manual)       │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Google Sheets (P&L Format)                      │
│  Columns: Date | P&L Type | P&L Category | Merchant | Amount │
│           | Note | Receipt No | Timestamp                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎮 Control Commands

| Command | Function | Status |
|---------|----------|--------|
| `enable auto` | Enable Cron Job auto-processing | ⏳ Pending |
| `disable auto` | Disable Cron Job | ⏳ Pending |
| `@Alfred + image` | Manual trigger | ✅ Available |

---

## 📋 P&L Classification Rules

### Three-Tier Structure
```
REVENUE
    └── Rent Received
    └── Interest (received)
    └── ...

COST
    └── Items not fitting EXPENSES categories

EXPENSES (38 categories)
    ├── Accounting & Legal
    ├── Accounting - Fines
    ├── Admin General - Bank Charges
    ├── Audit Fees
    ├── Advertising
    ├── Bad Debts
    ├── Claims
    ├── Computer Costs - Equipment
    ├── Computer Costs - Communications, Subscription, API cost
    ├── Depreciation
    ├── Diesel, Gasline
    ├── Directors Fees
    ├── Entertainment
    ├── Fork Hoist Hire
    ├── Fringe Benefit Tax
    ├── Admin Fee
    ├── Hire & Lease - Equipment Wise
    ├── Insurance
    ├── Operating General
    ├── Operating General - Cleaning
    ├── Operating General - Electricity, Water Supply
    ├── Petrol & Oil
    ├── Postage & Courier Costs
    ├── Printing & Stationery
    ├── Rates
    ├── Rent
    ├── R & M
    ├── Road User Distance Tax
    ├── Stowage Aids
    ├── Telephones, Mobile
    ├── Travelling & Accommodation - Overseas
    ├── Travelling & Accommodation Local
    ├── Wages & Salaries
    ├── Wages & Salaries - Allowances
    └── Annual Bonus
```

---

## 🔄 Operation Workflows

### Auto Mode (Cron)
```
Every 30 seconds check group
    ↓
New image found?
    ├── YES → AI Vision OCR → Extract info → Ask category → Write to Sheets
    └── NO → Silent (no notification)
```

### Manual Mode (@)
```
@Alfred + Send image
    ↓
Trigger OCR immediately
    ↓
Extract info
    ↓
Ask category (if uncertain)
    ↓
Write to Sheets
    ↓
Reply confirmation
```

---

## 📝 Data Format Standards

### Google Sheets Columns
| Column | Format | Example |
|--------|--------|---------|
| Date | `'YYYY/MM/DD` | `'2026/03/19` |
| P&L Type | TEXT | EXPENSES |
| P&L Category | TEXT | Operating General - Cleaning |
| Merchant | TEXT | 淘寶 |
| Amount | NUMBER | 66.14 |
| Note | TEXT | Full Lin Dehumidifier |
| Receipt No | TEXT | 2701752998070116791 |
| Timestamp | TIMESTAMP | 2026-03-21 23:45:00 |

### Date Format Handling
- Leading apostrophe `'` prevents Excel serial number conversion
- Unified format: `YYYY/MM/DD`

### Merchant Name Simplification
- Taobao orders → Display as "淘寶"
- Other merchants → First 30 characters

---

## ⚠️ Rules & Constraints

### Classification Confirmation Mechanism
1. **Clear classification** → Auto-assign
2. **Unclear classification** → Ask user
3. **Unknown item** → Suggest category and confirm

### Token Saving Strategy
- Cron Job default silent (no notification if no new images)
- Only notify when new image found or processing complete
- User can toggle auto mode anytime

### Error Handling
- OCR failure → Notify user for manual input
- Sheets write failure → Retry 3 times then notify
- Classification doubt → Ask immediately, no guessing

---

## 🔧 Tech Stack

| Component | Technology |
|-----------|------------|
| Message Reception | OpenClaw Gateway |
| OCR Parsing | Kimi Vision AI |
| Data Storage | Google Sheets API |
| Auto Scheduling | OpenClaw Cron |
| Programming | Python 3.11 |

---

## 📊 Status Monitoring

- **Cron Job ID**: `92883bd4-5721-40d3-89f7-bdb58609b163`
- **Check Frequency**: Every 30 seconds
- **Sheets ID**: `1BQXOvBoovN27N5nwUC_qtNqc7hgcw05WUB89yVpo1yk`
- **Supported Currencies**: HKD, CNY, USD (auto-detect)

---

## 🔐 Private Skill Notice

**This skill is PRIVATE and CONFIDENTIAL**
- For exclusive use by: Burt (+85263931048)
- Not for public distribution
- Not for ClawHub publication
- Internal use only

---

*Last Updated: 2026-03-21*  
*Version: P&L Format v1.0*  
*Classification: PRIVATE*
