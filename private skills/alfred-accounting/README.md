# Alfred Accounting Bot - Private Skill

**PRIVATE & CONFIDENTIAL - For Burt Only**

## Overview

Automated receipt processing and P&L accounting bot for WhatsApp integration with Google Sheets.

## Features

- AI Vision OCR for receipt parsing
- P&L format classification (38 categories)
- Automatic Google Sheets recording
- Cron-based auto-detection
- Manual trigger via @mention

## Installation

```bash
# Copy skill to OpenClaw skills directory
cp -r ~/openclaw_workspace/skills/alfred-accounting ~/.openclaw/skills/

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create `.env` file:
```
GOOGLE_SHEETS_ID=your_sheets_id
GOOGLE_CREDENTIALS_PATH=./credentials.json
```

## Usage

### Commands
- `@Alfred + image` - Process receipt manually
- `enable auto` - Enable auto-processing (pending)
- `disable auto` - Disable auto-processing (pending)

### P&L Categories
See `docs/P&L_CATEGORIES.md` for full list.

## Privacy Notice

This skill is PRIVATE and not for public distribution.
