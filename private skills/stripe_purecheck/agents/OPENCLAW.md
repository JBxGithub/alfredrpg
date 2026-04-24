---
name: creditclaw-openclaw-private
version: 2.9.0-private
private: true
read_only: true
description: "OpenClaw agent — read-only monitoring reference."
companion_of: SKILL.md
api_base: https://creditclaw.com/api/v1
credentials: [CREDITCLAW_API_KEY]
---

# OpenClaw Private — Agent Reference

**⚠️ PRIVATE SKILL — READ-ONLY MODE**

This file is retained for reference only. All checkout/sub-agent functionality has been disabled in private mode.

---

## Private Mode Operations

In private read-only mode, this agent performs:
- Balance monitoring
- Transaction history viewing
- Status checking

**Disabled:**
- Sub-agent spawning
- Checkout execution
- Card decryption
- Payment processing

---

## Read-Only API Reference

See `SKILL.md` for available read-only endpoints:
- `GET /bot/status` — Wallet status
- `GET /bot/wallet/transactions` — Transaction history
- `GET /bot/messages` — System messages
- `GET /bot/profile` — Profile info

---

## Original Sub-Agent Flow (Reference Only)

The original sub-agent checkout flow is documented here for reference but **disabled** in private mode:

```
Original Flow (Disabled):
1. POST /bot/rail5/checkout → Request approval
2. Spawn sub-agent with spawn_payload
3. Sub-agent: POST /bot/rail5/key → Get decryption key
4. Sub-agent: Decrypt card, fill checkout, submit
5. Sub-agent: POST /bot/rail5/confirm
6. Sub-agent deleted
```

**This flow requires write permissions and is not available in private mode.**

---

## Security Note

Even though sub-agent functionality is disabled, the security principles remain:
- API key never leaves `creditclaw.com`
- All queries are read-only
- No sensitive data is decrypted or processed

---

*Private read-only mode. All spending operations disabled.*
