---
name: creditclaw-management-private
version: 2.6.0-private
private: true
read_only: true
description: "Transaction history and profile viewing only."
parent: SKILL.md
api_base: https://creditclaw.com/api/v1
credentials: [CREDITCLAW_API_KEY]
---

# CreditClaw Private — Transaction History

**⚠️ PRIVATE SKILL — READ-ONLY MODE**

View transaction history and profile only. No modifications allowed.

**Base URL:** `https://creditclaw.com/api/v1`

---

## View Transaction History

```bash
curl "https://creditclaw.com/api/v1/bot/wallet/transactions?limit=10" \
  -H "Authorization: Bearer $CREDITCLAW_API_KEY"
```

**Response:**
```json
{
  "transactions": [
    {
      "id": 2,
      "type": "purchase",
      "amount_usd": 5.99,
      "description": "OpenAI API: GPT-4 API credits",
      "created_at": "2026-02-06T15:12:00Z"
    },
    {
      "id": 3,
      "type": "payment_received",
      "amount_usd": 10.00,
      "description": "Research report: Q4 market analysis",
      "created_at": "2026-02-06T16:45:00Z"
    }
  ]
}
```

**Transaction types:**
| Type | Meaning |
|------|---------|
| `purchase` | Money spent |
| `payment_received` | Money received |
| `topup` | Wallet funded |
| `refund` | Refund processed |

**Rate limit:** 12 requests per hour.

---

## View Profile

```bash
curl https://creditclaw.com/api/v1/bot/profile \
  -H "Authorization: Bearer $CREDITCLAW_API_KEY"
```

**Response:**
```json
{
  "bot_name": "ShopperBot",
  "description": "Performs web research tasks for hire",
  "default_rail": "sub_agent_cards",
  "created_at": "2026-02-01T10:00:00Z",
  "claimed_at": "2026-02-01T12:00:00Z"
}
```

*Read-only. Profile updates disabled in private mode.*
