---
name: creditclaw-heartbeat-private
version: 2.8.0-private
private: true
read_only: true
---

# CreditClaw Private — Monitoring Routine

**⚠️ PRIVATE SKILL — READ-ONLY MODE**

Periodic monitoring routine for wallet status and transaction history.

---

## 1. Check Full Status (Every 8 Hours)

```bash
curl https://creditclaw.com/api/v1/bot/status \
  -H "Authorization: Bearer $CREDITCLAW_API_KEY"
```

**Response fields:**
- `status` — overall status (`active`, `pending`, `frozen`, `inactive`)
- `active_rails` — connected payment rails
- `rails` — balance, limits per rail
- `master_guardrails` — cross-rail spending limits

**If `status` is `frozen`:**
> "CreditClaw wallet has been frozen. Check dashboard at https://creditclaw.com/app."

**If balance is low (< $5.00):**
Notify owner to take action at https://creditclaw.com/overview.

---

## 2. Check Messages (Every 30 Minutes)

```bash
curl https://creditclaw.com/api/v1/bot/messages \
  -H "Authorization: Bearer $CREDITCLAW_API_KEY"
```

Poll for system alerts (low balance, status changes).

---

## Summary

| Check | Endpoint | Frequency |
|-------|----------|-----------|
| Full status | `GET /bot/status` | Every 8 hours |
| Messages | `GET /bot/messages` | Every 30 minutes |

*Read-only monitoring. No spending operations.*
