---
name: creditclaw-my-store-private
version: 2.6.0-private
private: true
read_only: true
description: "View checkout pages and sales only. Creation disabled."
parent: SKILL.md
api_base: https://creditclaw.com/api/v1
credentials: [CREDITCLAW_API_KEY]
---

# CreditClaw Private — Store Monitoring

**⚠️ PRIVATE SKILL — READ-ONLY MODE**

View existing checkout pages and sales history only. Creation of new pages disabled.

---

## List Checkout Pages

```bash
curl https://creditclaw.com/api/v1/bot/checkout-pages \
  -H "Authorization: Bearer $CREDITCLAW_API_KEY"
```

Returns all active checkout pages with view/payment counts.

**Rate limit:** 12 requests per hour.

---

## View Sales

```bash
curl "https://creditclaw.com/api/v1/bot/sales?limit=20" \
  -H "Authorization: Bearer $CREDITCLAW_API_KEY"
```

Optional filters:
- `?status=confirmed|pending|failed`
- `?checkout_page_id=cp_xxx`
- `?limit=N` (default 20, max 100)

**Rate limit:** 12 requests per hour.

---

*Read-only monitoring. Checkout page creation disabled in private mode.*
