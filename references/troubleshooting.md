# vfs-tracker Troubleshooting Guide

## Architecture

vfs-tracker uses a **two-layer design**:
- **Pure HTTP** (stdlib `urllib`): Core query logic — zero dependencies
- **One-time browser fetch**: Only for discovering new country tracking endpoints (cached to `q_params.json`)

## Common Issues

### 1. First query opens Chrome briefly

**Symptoms**: Chrome window pops up for ~15 seconds when querying a new country
**Explanation**: The script needs to discover the country's tracking endpoint (the `q` parameter)
**Fix**: After the first fetch, the endpoint is cached — all future queries use pure HTTP

### 2. CAPTCHA image doesn't open

**Symptoms**: CAPTCHA image doesn't appear
**Causes**:
- macOS: `open` command may not work in some terminal emulators
- Linux: need `xdg-open`, `feh`, or `eog` installed
- Windows: should work with built-in Photos app
**Workaround**: The CAPTCHA is saved to your system temp directory (`/tmp/vfs-captcha.png` on macOS/Linux, `%TEMP%/vfs-captcha.png` on Windows). Open it manually.

### 2b. CAPTCHA keeps failing / "the captcha stays the same"

**Symptoms**: Every retry shows the same captcha and the query never succeeds
**Cause**: The VFS `DefaultCaptcha` image is one-shot per page render. Re-requesting
the `Generate` endpoint (or clicking the in-page refresh link) returns a *blank*
image, so OCR loops on garbage.
**Fix (built in)**: The tracker no longer clicks the refresh link. After an
incorrect submit the form posts back and the page reloads with a brand-new valid
captcha, which is read directly from the rendered `<img>`. OCR output is also
normalised to 5 uppercase letters (`A-Z`). If a query still fails, simply run it
again — each attempt now uses a genuinely fresh captcha (`MAX_CAPTCHA_RETRIES`
attempts per run).

### 3. No Records Found

**Symptoms**: "No records found" or "Invalid Inputs"
**Check**:
- Reference Number exact match? (case-sensitive, include slashes: `MNLNL/251015/0042/01`)
- Last Name exact match with passport? (spaces, hyphens, etc.)
- Correct country selected?

### 4. Network Error

**Symptoms**: `❌ Network error: ...`
**Causes**: VFS tracking server temporarily unavailable
**Fix**: Wait a few minutes and retry

### 5. Selenium not installed (first-time only)

**Symptoms**: `ModuleNotFoundError: No module named 'selenium'`
**Fix**:
```bash
pip install selenium selenium-stealth
```

### 6. Country endpoint not found

**Symptoms**: `--fetch-q` cannot find the tracking endpoint
**Causes**: Some countries may not use VFS Global in China; they may use TLScontact or other providers
**Fix**: Check the country's embassy website for the correct tracking URL

## Manual Fallback

If the script doesn't work:
1. Open https://visa.vfsglobal.com/
2. Select your departure country
3. Select your destination Schengen country
4. Click "Track Your Application"
5. Enter Reference Number + Last Name + CAPTCHA manually

## Status Values

| Status | Meaning |
|--------|---------|
| Application Received | Materials at VFS, not yet at embassy |
| Application Forwarded | Materials sent to embassy |
| Under Process | Embassy reviewing |
| Decision Made | Decision reached, awaiting passport return |
| Passport Dispatched | Passport returning via courier |
| Passport Delivered | Passport received |
| Ready for Collection | Available for pickup at VFS centre |
| Invalid Inputs | Wrong reference / name |
| No records found | No matching application |

## Cache Management

The cache file is `scripts/q_params.json`:

```json
{
  "_comment": "VFS Global tracking endpoint cache",
  "isl": "shSA0YnE4pLF9Xzwon/x/...=",
  "deu": "..."
}
```

- Delete a country entry → re-fetch on next query
- Delete the whole file → all countries re-fetched
- Share entries with others to save them the browser step
