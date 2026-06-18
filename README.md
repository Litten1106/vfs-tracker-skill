# vfs-tracker 🛂

> Headless VFS Global Schengen Visa Status Tracker + EU EES calculator  
> Fully automated — Selenium + ddddocr + number-slider CAPTCHA solver

<p align="center">
  <img src="https://img.shields.io/pypi/v/vfs-tracker" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/vfs-tracker" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="License">
</p>

---

## What is this?

Automatically query your Schengen visa status through **VFS Global** and check your allowed stay duration through the **EU EES** system — all headless, no browser window, no manual CAPTCHA input.

| Tool | What it does | Automated |
|------|-------------|:---:|
| VFS Tracker | Query visa application status via VFS Global | ✅ |
| EES Calculator | Check allowed stay duration via EU EES | ✅ |

---

## Supported Environments

| Platform | Status | Notes |
|----------|:------:|-------|
| macOS (Intel / Apple Silicon) | ✅ | Chrome required |
| Linux (Ubuntu / Debian / CentOS) | ✅ | Chrome or Chromium required |
| Windows 10 / 11 | ✅ | Chrome required |
| WSL2 | ✅ | Needs Chrome installed in WSL |

**Mobile**: Not directly supported (Python runtime required), but works through any AI coding agent that has Python access — see below.

---

## Install in AI Coding Agents

### Claude Code (macOS / Linux / Windows)

```bash
# 1. Install the package
pip install vfs-tracker

# 2. Link the skill
mkdir -p ~/.claude/skills/vfs-tracker
# Create SKILL.md from the repo's SKILL.md in that directory
```

### Codex (OpenAI)

```bash
pip install vfs-tracker
# Add to your Codex workspace skills
```

### Cursor / Windsurf / Other VS Code-based agents

```bash
pip install vfs-tracker
# The CLI entry point will be available:
vfs-tracker isl -r "REF_NUMBER" -l "LAST_NAME"
```

### GitHub Copilot Chat

```bash
pip install vfs-tracker
# Ask Copilot: "Query my Iceland visa status using vfs-tracker"
# It will run: python3 -m vfs_tracker isl -r "..." -l "..."
```

### Terminal / CLI (anywhere Python 3.10+ is available)

```bash
pip install vfs-tracker
vfs-tracker isl -r "ABCD/123456/01" -l "SMITH"
# or:
python3 -m vfs_tracker isl -r "ABCD/123456/01" -l "SMITH"
```

---

## Quick Start

```bash
# 1. Install
pip install vfs-tracker

# 2. Track your visa (Iceland is pre-cached)
vfs-tracker isl -r "ISL/PVG/010101/0001/01" -l "DOE"

# 3. Check EU EES stay duration
python3 -c "
from vfs_tracker import ees_check
r = ees_check(passport_number='E12345678', issuing_country='CHN',
          destination_code='isl', entry_date='23-09-2026', exit_date='04-10-2026')
print(r['message'])
"

# 4. List all countries
vfs-tracker list

# 5. Pre-cache a new country
vfs-tracker deu --fetch-q
```

---

## Usage

```bash
vfs-tracker <country_code> -r <REF> -l <NAME>
```

| Option | Description |
|--------|-------------|
| `-r, --reference` | Application Reference Number (from VFS receipt) |
| `-l, --last-name` | Last Name / Surname (as on passport) |
| `--fetch-q` | Fetch & cache tracking endpoint for a country |
| `list` | Show all 29 supported Schengen countries |

---

## How It Works

```
Headless Chrome (no window)
  └─ stealth.js anti-detection
  └─ ddddocr: CAPTCHA OCR (VFS text-based)
  └─ Custom number-slider solver (EU EES 2-digit puzzle)
  └─ Human-like mouse drag simulation
  └─ POST form → parse result → status card
```

---

## EES CAPTCHA Solver

The EU EES calculator uses a **2-digit number selection CAPTCHA** (two tiny images showing digits, slider to select the target number). Our solver:

1. Extracts both images from the page
2. Uses ddddocr to read the number (digit image or word image like "thirty-seven")
3. Computes the target value (0–50)
4. Drags the slider with human-like mouse movement (variable speed, Y-axis jitter, random pauses)
5. Submits the form — fully automated

---

## VFS ↔ EES Relationship

| VFS Status | Expected EES | What it means |
|-----------|:---:|---------------|
| 📨 Application Received | NOT OK | Visa not yet in EES — normal |
| 📤 Application Forwarded | NOT OK | Embassy hasn't entered data |
| ⏳ Under Process | Varies | Not reliable at this stage |
| 📋 Decision Made | OK (likely) | Visa likely approved |
| 📦 Passport Dispatched | OK | Should be in the system |

---

## Output Example

```
🛂  vfs-tracker — VFS Global 签证状态查询
    目标国家: 冰岛 (Iceland) (ISL)
    申请编号: ISL/PVG/010101/0001/01
    姓氏: DOE
────────────────────────────────────────────────────────────

🌐 正在加载追踪页面...
   ✅ 页面已加载 (17305 bytes)
   ✅ 表单已填写
   🔐 验证码识别: [PFKRG]

── Query Result ──

  目标国家 : 冰岛 (Iceland) (ISL)
  申请编号 : ISL/PVG/010101/0001/01
  姓氏     : DOE
  Embassy  : Iceland Embassy

  📨 申请已送达
  您的签证申请材料已送达 Iceland Embassy。

  进度: ● → ○ → ○ → ○ → ○ → ○
        Recv  Fwd  Review  Decide  Ship  Done
```

---

## Requirements

- **Python** ≥ 3.10
- **Google Chrome** (or Chromium)
- Internet connection

```bash
pip install vfs-tracker  # installs all deps automatically
```

Manual dependencies if installing from source:
```bash
pip install selenium selenium-stealth ddddocr Pillow
```

---

## Project Structure

```
vfs-tracker/
├── pyproject.toml              # Package metadata + build config
├── README.md
├── SKILL.md                    # Claude Code / agent skill definition
├── src/
│   └── vfs_tracker/
│       ├── __init__.py         # Main tracker (VFS + EES)
│       ├── countries.json      # 29 Schengen countries
│       └── q_params.json       # Cached tracking endpoints
└── references/
    └── troubleshooting.md
```

---

## License

MIT

## Acknowledgments

- [VFS-Helper-Bot](https://github.com/kunalyelne/VFS-Helper-Bot) — inspired the Selenium approach
- [ddddocr](https://github.com/sml2h3/ddddocr) — CAPTCHA OCR engine
- [EU EES](https://travel-europe.europa.eu/ees) — official short-stay calculator
