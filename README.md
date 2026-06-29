# vfs-tracker 🛂

> VFS Global Schengen Visa Status Tracker + EU EES calculator  
> VFS uses a Chrome-free HTTP mode by default; EES uses Selenium for the slider CAPTCHA.

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
| macOS (Intel / Apple Silicon) | ✅ | VFS works without Chrome; EES needs Chrome |
| Linux (Ubuntu / Debian / CentOS) | ✅ | Use `--mode http` for VFS in no-desktop sandboxes |
| Windows 10 / 11 | ✅ | VFS works without Chrome; EES needs Chrome |
| WSL2 / containers / Claude CLI sandboxes | ✅ | VFS HTTP mode recommended; EES may need a real Chrome runtime |

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

If the official PyPI file host has SSL/network issues in a sandbox, install
from a mirror instead:

```bash
pip install -U vfs-tracker -i https://mirrors.cloud.tencent.com/pypi/simple
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

# Track VFS and also check EES in the same run
vfs-tracker isl -r "ISL/PVG/010101/0001/01" -l "DOE" \
  --ees-passport "E12345678" --ees-entry "23-09-2026" --ees-exit "04-10-2026"

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

# 6. Diagnose local runtime/network only when something fails
vfs-tracker doctor
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
| `--mode` | VFS backend: `auto`, `http`, or `selenium` (default: `auto`; force only for debugging) |
| `--ees-passport` | Also run EES check with this passport number |
| `--ees-entry` | Intended EES entry date (`DD-MM-YYYY`) |
| `--ees-exit` | Intended EES exit date (`DD-MM-YYYY`) |
| `--ees-issuing` | EES issuing country code (default: `CHN`) |
| `--no-ees` | Disable automatic EES check from environment variables |
| `--fetch-q` | Fetch & cache tracking endpoint for a country |
| `list` | Show all 29 supported Schengen countries |

---

## How It Works

```
VFS status
  └─ HTTP mode first: requests + certifi, no Chrome required
  └─ Synchronized form tokens: __RequestVerificationToken + CaptchaDeText
  └─ ddddocr with color-aware CAPTCHA preprocessing
  └─ Selenium fallback when HTTP mode cannot parse a standard result

EES calculator
  └─ Headless Chrome for the EU slider CAPTCHA
  └─ ddddocr reads the CAPTCHA numbers
  └─ Human-like slider selection
  └─ Parses official Authorised stay + remaining-days result
```

---

## EES CAPTCHA Solver

The EU EES calculator uses a **2-digit number selection CAPTCHA** (two tiny images showing digits, slider to select the target number). Our solver:

1. Extracts both images from the page
2. Uses ddddocr to read the number (digit image or word image like "thirty-seven")
3. Reads whether the widget asks for the highest or lowest number
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

  📨 申请已送达
  进度: ● → ○ → ○ → ○ → ○ → ○
        Recv  Fwd  Review  Decide  Ship  Done

📄 原始文案：
   Your visa application reference no. ISL/PVG/010101/0001/01 has been
   received by Iceland Embassy in Beijing.

材料已经稳稳交到使馆手里了，第一步走完。接下来就是等——签证官审材料急不来，
你能做的都做完了，松口气，过几天再回来看一眼就好。
```

> Language auto-follows your system locale (`LANG`). Force Chinese with
> `LANG=zh_CN.UTF-8 vfs-tracker isl -r ... -l ...`.

---

## What's New

- **1.0.5** — Adds Chrome-free VFS HTTP mode for Claude CLI / containers,
  synchronized token handling, improved VFS CAPTCHA preprocessing, `--mode`,
  and `vfs-tracker doctor`.
- **1.0.4** — Fixes EES parsing to trust only the official
  `Authorised stay: OK/NOT OK` result section, extracts
  `Remaining days at the moment of entry`, and can run EES after VFS when
  passport/travel dates are supplied.
- **1.0.3** — Surfaces the full original VFS message verbatim, plus warm,
  per-status encouragement (and a reapply/appeal plan once a decision is made).
- **1.0.2** — Reliable CAPTCHA handling: uppercase normalization, fresh captcha
  on every retry (no more "stuck on the same captcha"), more retries.

---

## Requirements

- **Python** ≥ 3.10
- **Google Chrome** (or Chromium) only for EES / Selenium fallback
- Internet connection

```bash
pip install vfs-tracker  # installs all deps automatically
```

If PyPI SSL fails in a restricted network:

```bash
pip install -U vfs-tracker -i https://mirrors.cloud.tencent.com/pypi/simple
```

Manual dependencies if installing from source:
```bash
pip install requests certifi selenium selenium-stealth ddddocr Pillow
```

Linux no-desktop notes:

- Use `--mode http` for VFS status checks to avoid Chrome/X11/d-bus issues.
- If you force Selenium on Ubuntu, install Chrome/Chromium and common runtime
  libraries such as `libxdamage1`, `libnss3`, `libatk-bridge2.0-0`,
  `libxkbcommon0`, `libgbm1`, and `libasound2`.
- EES currently still needs a working Chrome runtime because the official EU
  page uses an interactive slider CAPTCHA.

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
