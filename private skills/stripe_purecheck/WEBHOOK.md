---
name: creditclaw-webhook-private
private: true
read_only: true
parent: SKILL.md
api_base: https://creditclaw.com/api/v1
credentials: [CREDITCLAW_API_KEY]
---

# CreditClaw Private — Webhook Reference

**⚠️ PRIVATE SKILL — READ-ONLY MODE**

Webhook documentation for reference only. Polling via `GET /bot/messages` is the recommended approach for private mode.

---

## Webhook vs Polling

| Method | Recommendation |
|--------|---------------|
| **Polling** | ✅ Recommended for private mode |
| **Webhook** | Optional — requires public endpoint |

---

## Polling (Recommended)

```bash
# Check for messages
curl https://creditclaw.com/api/v1/bot/messages \
  -H "Authorization: Bearer $CREDITCLAW_API_KEY"

# Acknowledge processed messages
curl -X POST https://creditclaw.com/api/v1/bot/messages/ack \
  -H "Authorization: Bearer $CREDITCLAW_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message_ids": [1, 2, 3]}'
```

---

## Webhook Events (Reference)

| Event | Meaning |
|-------|---------|
| `wallet.activated` | Wallet is live |
| `wallet.topup.completed` | Funds added |
| `wallet.balance.low` | Balance below $5.00 |
| `rails.updated` | Payment config changed |

*Webhook setup requires public endpoint and signature verification. See full documentation if needed.*

---

*Private mode — polling recommended over webhooks.*
