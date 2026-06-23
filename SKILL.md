---
name: vfs-tracker
description: "Track Schengen visa application status through VFS Global. Use this skill whenever the user mentions checking visa status, tracking visa application, Schengen visa, visa result, VFS tracking, or wants to know if their visa is approved. Also supports EU EES short-stay calculator to verify allowed stay duration. Supports all 29 Schengen countries."
---

# vfs-tracker 🛂

Two tools, one purpose: know where your visa stands.

| Tool | What it does | Automated |
|------|-------------|:---:|
| **VFS Tracker** | Query visa application status via VFS Global | ✅ |
| **EES Calculator** | Check allowed stay duration via EU EES | ✅ |

**⚠️ Important**: VFS and EES are related — if VFS shows the visa is still being processed, EES will likely return "NOT OK" because the visa hasn't been entered into the EES system yet. **Always interpret EES results in the context of the VFS status.**

## VFS ↔ EES Relationship

| VFS Status | Expected EES Result | What it means |
|-----------|-------------------|---------------|
| 📨 Application Received | ❌ NOT OK | Visa not yet in EES — normal at this stage |
| 📤 Application Forwarded | ❌ NOT OK | Embassy hasn't entered data yet |
| ⏳ Under Process | ❌ NOT OK or ✅ OK | May vary — not reliable |
| 📋 Decision Made | ✅ OK (likely) | Visa likely approved |
| 📦 Passport Dispatched | ✅ OK | Visa should be in the system |
| ✅ Passport Delivered | ✅ OK | Look at the stamp in your passport |

**Key rule**: If VFS status is **before** "Decision Made", tell the user:
> "EES 显示 NOT OK 是正常的 — 签证还在审理中，尚未录入欧盟出入境系统。等 VFS 状态变为 'Decision Made' 或 'Passport Dispatched' 后再查 EES 才准确。"

## ⚠️ Core Rules

1. **Never guess** — collect inputs conversationally.
2. **Two independent entry points** — user can ask for either tool first. After completing one, ask if they want the other.
3. **Share known info** — if country was already collected, reuse it. Only ask for what's missing.
4. **Always contextualize EES with VFS** — if the user only runs EES, warn them about the relationship.

---

## Tool A: VFS Visa Status Tracker

### Required inputs

| Field | Source |
|-------|--------|
| Departure country | Ask (default: **China 中国**) |
| Destination country | AskUserQuestion |
| Reference Number | Ask ("from your VFS receipt") |
| Last Name | Ask ("as on passport") |

### Run

The user must have installed the package first:
```bash
pip install vfs-tracker
```

Then run the VFS tracker (replace `isl`, `-r`, `-l` with the user's actual values):
```bash
python3 -c "
from vfs_tracker import main
import sys; sys.argv = ['', 'isl', '-r', 'REF_NUMBER', '-l', 'LAST_NAME']
main()
"
```

If the user has already provided passport number and travel dates, run VFS and
EES together:
```bash
vfs-tracker isl -r "REF_NUMBER" -l "LAST_NAME" \
  --ees-passport "PASSPORT" --ees-entry "DD-MM-YYYY" --ees-exit "DD-MM-YYYY"
```

**CRITICAL**: Show upgrade tip so we don't hit stale-cache bugs:
```bash
pip install --upgrade vfs-tracker
```

### How to display the result

**CRITICAL**: After the script runs, always print the result card directly inline. Do NOT hide it inside a `> details` fold / toggle. Also ask the user if they want to also check EES.

---

## Tool B: EU EES Short-Stay Calculator

### Before running

**Check if VFS was already queried.** If VFS status is pre-"Decision Made", warn the user that EES may show NOT OK.

### Required inputs

| Field | Source |
|-------|--------|
| Destination country | Reuse from VFS if known, else AskUserQuestion |
| Passport number | Ask |
| Issuing country | Default: **CHN** |
| Entry date | Ask ("DD-MM-YYYY") |
| Exit date | Ask ("DD-MM-YYYY") |

### Run

```bash
python3 -c "
from vfs_tracker import ees_check
r = ees_check(passport_number='PASSPORT', issuing_country='CHN',
          destination_code='isl', entry_date='DD-MM-YYYY', exit_date='DD-MM-YYYY')
if r:
    print(r.get('official_text') or r.get('message', 'Query failed'))
else:
    print('Query failed')
"
```

### After result

**CRITICAL**: Treat `Authorised stay: OK/NOT OK` as the source of truth, then
report `Remaining days at the moment of entry`. Print the result inline, never
inside a `<details>` fold. Always remind the user of the VFS ↔ EES relationship.

---

## Supported Countries (29 Schengen states)

| Code | Country | Code | Country |
|------|---------|------|---------|
| isl | Iceland 冰岛 | deu | Germany 德国 |
| fra | France 法国 | ita | Italy 意大利 |
| esp | Spain 西班牙 | che | Switzerland 瑞士 |
| nld | Netherlands 荷兰 | aut | Austria 奥地利 |
| ... | (29 total) | | |

## Status Translations (VFS)

| Status | Meaning |
|--------|---------|
| 📨 Application Received | Materials at VFS centre |
| 📤 Application Forwarded | Sent to embassy |
| ⏳ Under Process / In Process | Embassy reviewing |
| 📋 Decision Made | Awaiting passport return |
| 📦 Passport Dispatched | Passport returning |
| ✅ Passport Delivered | Passport received |
| 🏢 Ready for Collection | Pick up at VFS centre |

## Prerequisites

```bash
pip install vfs-tracker
# This installs all dependencies: selenium, selenium-stealth, ddddocr, Pillow
```
