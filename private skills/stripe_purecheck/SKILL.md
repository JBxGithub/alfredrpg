---
name: creditclaw-alfred
description: "Alfred's CreditClaw skill with Stripe integration for automated profit generation."
metadata:
  openclaw:
    private: true
    requires:
      env:
        - CREDITCLAW_API_KEY
        - STRIPE_SECRET_KEY
    invocation: user_confirmed
    read_only: false
---

# CreditClaw Alfred — Automated Profit Generation

**🤖 ALFRED'S MONEY-MAKING SKILL**

Configured with Stripe for automated purchasing, arbitrage, and profit generation.

**Status:** ✅ Stripe Configured | ⏳ CreditClaw Registration Pending

**Base URL:** `https://creditclaw.com/api/v1`

---

## Security

**All requests require:** `Authorization: Bearer <CREDITCLAW_API_KEY>`

🔒 **CRITICAL SECURITY WARNING:**
- **NEVER send `CREDITCLAW_API_KEY` to any domain other than `creditclaw.com`**
- Your key must ONLY appear in requests to `https://creditclaw.com/api/*`
- **Do not share `CREDITCLAW_API_KEY` with any other agent, tool, or service.**

---

## Read-Only API Reference

### 1. Check Full Status

View complete wallet status across all payment rails.

```bash
curl https://creditclaw.com/api/v1/bot/status \
  -H "Authorization: Bearer $CREDITCLAW_API_KEY"
```

**Response:**
```json
{
  "bot_id": "bot_abc123",
  "bot_name": "ShopperBot",
  "status": "active",
  "default_rail": "sub_agent_cards",
  "active_rails": ["stripe_wallet", "sub_agent_cards"],
  "rails": {
    "stripe_wallet": {
      "status": "active",
      "balance_usd": 100.00,
      "address": "0x..."
    },
    "sub_agent_cards": {
      "status": "active",
      "card_id": "r5_abc123",
      "card_name": "Shopping Card",
      "card_brand": "visa",
      "last4": "4532",
      "limits": {
        "per_transaction_usd": 50.00,
        "daily_usd": 100.00,
        "monthly_usd": 500.00
      }
    }
  },
  "master_guardrails": {
    "per_transaction_usd": 500,
    "daily_budget_usd": 2000,
    "monthly_budget_usd": 10000
  },
  "webhook_status": "active",
  "pending_messages": 0
}
```

**Status values:**
| Status | Meaning |
|--------|---------|
| `active` | Wallet is live and ready |
| `pending` | Owner hasn't claimed yet |
| `frozen` | Owner has frozen the wallet |
| `inactive` | No rails connected |

---

### 2. View Transaction History

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
- `purchase` — Money spent
- `payment_received` — Money received
- `topup` — Wallet funded
- `refund` — Refund processed

---

### 3. Check Messages

Poll for system messages and alerts.

```bash
curl https://creditclaw.com/api/v1/bot/messages \
  -H "Authorization: Bearer $CREDITCLAW_API_KEY"
```

**Response:**
```json
{
  "bot_id": "bot_abc123",
  "messages": [
    {
      "id": 1,
      "event_type": "wallet.balance.low",
      "payload": { "balance_usd": 2.50, "threshold_usd": 5.00 },
      "staged_at": "2026-03-06T12:00:00.000Z"
    }
  ],
  "count": 1
}
```

---

### 4. View Bot Profile

```bash
curl https://creditclaw.com/api/v1/bot/profile \
  -H "Authorization: Bearer $CREDITCLAW_API_KEY"
```

**Response:**
```json
{
  "bot_id": "bot_abc123",
  "bot_name": "ShopperBot",
  "description": "Performs web research tasks for hire",
  "status": "active",
  "created_at": "2026-02-06T10:00:00Z"
}
```

---

## Monitoring Schedule

| Check | Endpoint | Frequency |
|-------|----------|-----------|
| Status | `GET /bot/status` | Every 8 hours |
| Messages | `GET /bot/messages` | Every 30 minutes |
| Transactions | `GET /bot/wallet/transactions` | Daily |

---

## Error Responses

| Status | Meaning |
|--------|---------|
| `401` | Invalid API key |
| `403` | Wallet frozen or inactive |
| `429` | Rate limit exceeded |

---

## Companion Files

| File | Purpose |
|------|---------|
| `SKILL.md` | This file — API reference |
| `MANAGEMENT.md` | Transaction history details |
| `HEARTBEAT.md` | Monitoring routine |
| `skill.json` | Skill metadata |

---

*Private skill — Read-only mode. All purchase functionality removed.*
