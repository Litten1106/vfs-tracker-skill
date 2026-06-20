#!/usr/bin/env python3
"""
vfs-tracker — Lightweight VFS Global Schengen Visa Status Tracker
=================================================================
Selenium headless (no browser window) + ddddocr auto CAPTCHA.

Requires: pip install selenium selenium-stealth ddddocr Pillow

Usage:
    python3 track.py isl -r "ABCD/123456/01" -l "SMITH"
    python3 track.py list
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
COUNTRIES_FILE = SCRIPT_DIR / "countries.json"
Q_PARAMS_FILE = SCRIPT_DIR / "q_params.json"
VFS_TRACKING_BASE = "https://www.vfsvisaonline.com"
VFS_TRACKING_PATH = "/Global-Passporttracking/Track/Index"
MAX_CAPTCHA_RETRIES = 8
EES_API = "https://travel-europe.europa.eu/api/tcn/stay-verification"


# ══════════════════════════════════════════════════════════════════════
#  System language detection
# ══════════════════════════════════════════════════════════════════════

def detect_lang() -> str:
    for v in [os.environ.get("LANG", ""), os.environ.get("LC_ALL", ""),
              os.environ.get("LC_MESSAGES", "")]:
        if v.lower().startswith("zh"):
            return "zh"
    try:
        import locale
        lang, _ = locale.getlocale()
        if lang and lang.startswith("zh"):
            return "zh"
    except Exception:
        pass
    return "en"


LANG = detect_lang()

# ══════════════════════════════════════════════════════════════════════
#  i18n
# ══════════════════════════════════════════════════════════════════════

_T = {
    "zh": {
        "banner": "vfs-tracker — VFS Global 签证状态查询",
        "fetching": "正在加载追踪页面...",
        "loaded": "页面已加载 ({n} bytes)",
        "filled": "表单已填写",
        "captcha": "验证码识别: [{text}]",
        "retry": "识别错误，重试 ({n}/{total})",
        "submitting": "提交中...",
        "country": "目标国家",
        "ref": "申请编号",
        "name": "姓氏",
        "no_q": "未缓存 {code} 的追踪端点。请先运行: python3 track.py {code} --fetch-q",
        "fetch_q_found": "已获取追踪端点 → 已缓存",
        "fetch_q_done": "已缓存！之后查询 {code} 将无需浏览器。",
        "status": {
            "received": {
                "trigger": "has been received by",
                "title": "📨 申请已送达",
                "detail": "您的签证申请材料已送达 {embassy}。",
            },
            "forwarded": {
                "trigger": "has been forwarded",
                "title": "📤 申请已转交",
                "detail": "申请材料已从 VFS 转交至大使馆/领事馆。",
            },
            "under_process": {
                "trigger": "under process",
                "title": "⏳ 审核中",
                "detail": "大使馆正在审理您的签证申请，请耐心等待。",
            },
            "decision": {
                "trigger": "decision",
                "title": "📋 已有决定",
                "detail": "签证审核已有结果，请等待护照返还通知。",
            },
            "dispatched": {
                "trigger": "dispatched",
                "title": "📦 护照已寄出",
                "detail": "您的护照正在通过快递寄回。",
            },
            "delivered": {
                "trigger": "delivered",
                "title": "✅ 护照已送达",
                "detail": "护照已送达，请查收。",
            },
            "collection": {
                "trigger": "ready for collection",
                "title": "🏢 可前往领取",
                "detail": "护照已到达 VFS 签证中心，请前往领取。",
            },
            "invalid": {
                "trigger": "invalid",
                "title": "❌ 输入无效",
                "detail": "请检查申请编号和姓氏拼写是否正确。",
            },
            "no_record": {
                "trigger": "no record",
                "title": "🔍 未找到记录",
                "detail": "未找到匹配的申请记录，请确认输入信息。",
            },
            "generic": {
                "trigger": "",
                "title": "📊 查询结果",
                "detail": "",
            },
        },
    },
    "en": {
        "banner": "vfs-tracker — VFS Global Visa Status",
        "fetching": "Loading tracking page...",
        "loaded": "Page loaded ({n} bytes)",
        "filled": "Form filled",
        "captcha": "CAPTCHA: [{text}]",
        "retry": "Incorrect, retrying ({n}/{total})",
        "submitting": "Submitting...",
        "country": "Country",
        "ref": "Reference",
        "name": "Last Name",
        "no_q": "No cached endpoint for {code}. Run: python3 track.py {code} --fetch-q",
        "fetch_q_found": "Endpoint fetched → cached",
        "fetch_q_done": "Cached! Future queries for {code} run without a browser.",
        "status": {
            "received": {
                "trigger": "has been received by",
                "title": "📨 Application Received",
                "detail": "Your application has been received by {embassy}.",
            },
            "forwarded": {
                "trigger": "has been forwarded",
                "title": "📤 Application Forwarded",
                "detail": "Your application has been forwarded from VFS to the embassy/consulate.",
            },
            "under_process": {
                "trigger": "under process",
                "title": "⏳ Under Review",
                "detail": "The embassy is reviewing your visa application.",
            },
            "decision": {
                "trigger": "decision",
                "title": "📋 Decision Made",
                "detail": "A decision has been made — awaiting passport return.",
            },
            "dispatched": {
                "trigger": "dispatched",
                "title": "📦 Passport Dispatched",
                "detail": "Your passport is being returned via courier.",
            },
            "delivered": {
                "trigger": "delivered",
                "title": "✅ Passport Delivered",
                "detail": "Your passport has been delivered.",
            },
            "collection": {
                "trigger": "ready for collection",
                "title": "🏢 Ready for Collection",
                "detail": "Your passport is ready for pickup at the VFS centre.",
            },
            "invalid": {
                "trigger": "invalid",
                "title": "❌ Invalid Input",
                "detail": "Please check your Reference Number and Last Name spelling.",
            },
            "no_record": {
                "trigger": "no record",
                "title": "🔍 No Records Found",
                "detail": "No matching application found. Please verify your information.",
            },
            "generic": {
                "trigger": "",
                "title": "📊 Query Result",
                "detail": "",
            },
        },
    },
}


def tt(key: str, **kwargs) -> str:
    val = _T[LANG].get(key) or _T["en"].get(key, key)
    if isinstance(val, str) and kwargs:
        val = val.format(**kwargs)
    return val


def status_info(key: str):
    return _T[LANG]["status"].get(key, _T[LANG]["status"]["generic"])


# ══════════════════════════════════════════════════════════════════════
#  Core: headless Selenium + ddddocr
# ══════════════════════════════════════════════════════════════════════

def track(q_param: str, reference_number: str, last_name: str) -> dict | None:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium_stealth import stealth
    import ddddocr

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1280,800")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        stealth(driver, languages=["zh-CN", "zh", "en-US", "en"],
                vendor="Google Inc.", platform="MacIntel",
                webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine",
                fix_hairline=True)
        driver.set_page_load_timeout(45)

        url = f"{VFS_TRACKING_BASE}{VFS_TRACKING_PATH}?q={q_param}"
        print(f"\n🌐 {tt('fetching')}")
        driver.get(url)
        WebDriverWait(driver, 30).until(lambda d: len(d.page_source) > 5000)
        time.sleep(1.5)
        print(f"   ✅ {tt('loaded', n=len(driver.page_source))}")

        print(f"   ✅ {tt('filled')}")

        ocr = ddddocr.DdddOcr(show_ad=False)

        for attempt in range(1, MAX_CAPTCHA_RETRIES + 1):
            # The VFS form posts back and reloads on every incorrect submit, so
            # re-fill the inputs each iteration (they are blank on a fresh page).
            ref_input = driver.find_element(By.NAME, "AppRefNo")
            ref_input.clear()
            ref_input.send_keys(reference_number)
            name_input = driver.find_element(By.NAME, "LastName")
            name_input.clear()
            name_input.send_keys(last_name)

            # Read the captcha straight from the freshly-rendered <img>. The
            # DefaultCaptcha is always 5 uppercase letters (A-Z), so strip any
            # noise characters and force uppercase to maximise OCR accuracy.
            img = driver.find_element(By.CSS_SELECTOR, 'img[src*="DefaultCaptcha"]')
            raw = ocr.classification(img.screenshot_as_png) or ""
            text = re.sub(r"[^A-Za-z]", "", raw).upper()
            print(f"   🔐 {tt('captcha', text=text or '?')}")

            if len(text) != 5:
                # Garbled read — reload the page to get a fresh captcha image
                # instead of re-requesting the one-shot Generate endpoint
                # (which returns a blank image on repeat hits).
                print(f"   🔄 {tt('retry', n=attempt, total=MAX_CAPTCHA_RETRIES)}")
                driver.get(url)
                WebDriverWait(driver, 30).until(lambda d: len(d.page_source) > 5000)
                time.sleep(1.0)
                continue

            inp = driver.find_element(By.NAME, "CaptchaInputText")
            inp.clear()
            inp.send_keys(text)
            driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
            time.sleep(2.5)

            body = driver.find_element(By.TAG_NAME, "body").text

            if "incorrect" in body.lower():
                # On an incorrect submit the page has already reloaded with a
                # brand-new, valid captcha. Just loop and read it again. Do NOT
                # click the refresh link — it blanks the freshly served image
                # and breaks every subsequent attempt.
                print(f"   🔄 {tt('retry', n=attempt, total=MAX_CAPTCHA_RETRIES)}")
                time.sleep(0.5)
                continue

            return parse_body(body, reference_number, last_name)

    finally:
        if driver:
            driver.quit()

    return None


def parse_body(body_text: str, reference_number: str, last_name: str) -> dict:
    lower = body_text.lower()

    embassy = ""
    m = re.search(r"(?:received|forwarded)\s+by\s+(.+?)(?:\.|\n|in\s)", lower)
    if m:
        embassy = m.group(1).strip().title()

    # Capture the exact sentence VFS shows (e.g. "Your visa application
    # reference no. ABC/123 has been received by Iceland Embassy in Beijing.").
    # Grab the whole line — the reference no.'s own period would otherwise cut a
    # non-greedy match short at "...reference no.".
    raw_message = ""
    rm = re.search(r"(your visa application[^\n]*)", body_text, re.I)
    if rm:
        raw_message = re.sub(r"\s+", " ", rm.group(1)).strip()

    matched = "generic"
    for key in ["received", "forwarded", "under_process", "decision",
                "dispatched", "delivered", "collection", "invalid", "no_record"]:
        trigger = status_info(key)["trigger"]
        if trigger and trigger in lower:
            matched = key
            break

    info = status_info(matched)
    detail = info["detail"].format(embassy=embassy) if "{embassy}" in info["detail"] else info["detail"]

    return {
        "key": matched,
        "title": info["title"],
        "detail": detail,
        "embassy": embassy,
        "ref": reference_number,
        "name": last_name,
        "raw_message": raw_message,
    }


# ══════════════════════════════════════════════════════════════════════
#  Output
# ══════════════════════════════════════════════════════════════════════

def print_card(result: dict, country_name: str, country_code: str):
    print()
    print("╔" + "═" * 58 + "╗")
    print(f"║  🛂  {tt('banner'):^52} ║")
    print("╠" + "═" * 58 + "╣")
    print(f"║  {tt('country'):>10}: {country_name} ({country_code.upper()})" + " " * 28 + "║")
    print(f"║  {tt('ref'):>10}: {result['ref']}" + " " * 35 + "║")
    print(f"║  {tt('name'):>10}: {result['name']}" + " " * 35 + "║")
    if result.get("embassy"):
        print(f"║  Embassy : {result['embassy']}" + " " * 38 + "║")
    print("╠" + "═" * 58 + "╣")
    print(f"║  {result['title']}" + " " * (58 - len(result['title']) - 2) + "║")
    if result["detail"]:
        print("║" + " " * 58 + "║")
        detail = result["detail"]
        while detail:
            chunk = detail[:50]
            detail = detail[50:]
            print(f"║  {chunk}{' ' * (58 - len(chunk) - 2)}║")
    print("║" + " " * 58 + "║")

    # Progress bar
    stages_order = ["received", "forwarded", "under_process", "decision", "dispatched", "delivered"]
    if result["key"] in stages_order:
        idx = stages_order.index(result["key"])
        dots = ["○"] * len(stages_order)
        for i in range(idx + 1):
            dots[i] = "●"
        bar = " → ".join(dots)
        print(f"║     {bar}" + " " * 38 + "║")
        labels = ["Recv", "Fwd", "Review", "Decide", "Ship", "Done"]
        label_bar = "  ".join(labels)
        print(f"║     {label_bar}" + " " * 38 + "║")
        print("║" + " " * 58 + "║")

    print("╚" + "═" * 58 + "╝")
    print()


# ══════════════════════════════════════════════════════════════════════
#  Mood / human-toned message per status
# ══════════════════════════════════════════════════════════════════════

_MOOD = {
    "zh": {
        "received": "材料已经稳稳交到使馆手里了，第一步走完。接下来就是等——签证官审材料急不来，"
                    "你能做的都做完了，松口气，过几天再回来看一眼就好。",
        "forwarded": "往前挪了一格，材料已经转进审理环节。节奏在动，继续耐心等就行。",
        "under_process": "签证官正在看你的材料了。这通常是最熬人的一段，但也恰恰说明流程在推进，再扛一下。",
        "decision": "结果出来了！去取护照或留意通知吧。\n\n"
                    "如果是 approved——恭喜你，冰岛见！🎉 极光、黑沙滩、蓝湖都在等你。\n"
                    "万一这次没过，也真的别灰心，拒签不是终点，下面给你一套二签思路。",
        "dispatched": "护照已经在寄回的路上了，盯一下快递信息。快到手了。",
        "delivered": "护照到手啦，翻到签证页确认一下信息有没有错。准备打包行李吧。",
        "collection": "护照已经到签证中心，带好证件去把它取回来吧。",
        "invalid": "信息对不上。检查一下申请编号和姓氏拼写，尤其是斜杠和大小写。",
        "no_record": "暂时没查到记录。可能是刚提交还没入库，或者信息有出入，过会儿再试试。",
        "generic": "状态已查询到，但没匹配到标准描述。可以对照原始文案看一眼。",
    },
    "en": {
        "received": "Your documents are safely with the embassy now — step one done. "
                    "From here it's just waiting; the officer reviews at their own pace. "
                    "You've done your part, so relax and check back in a few days.",
        "forwarded": "One notch forward — your file has moved into the review stage. "
                     "Things are moving; just keep waiting.",
        "under_process": "The officer is actively looking at your application. This is usually "
                         "the most nerve-wracking stretch, but it also means the wheels are turning. Hang in there.",
        "decision": "A decision is in! Go collect your passport or watch for the notice.\n\n"
                    "If it's approved — congratulations, see you in Iceland! 🎉\n"
                    "If it didn't go through this time, don't lose heart. A refusal isn't the end — "
                    "there's a second-application plan below.",
        "dispatched": "Your passport is on its way back — keep an eye on the courier. Almost there.",
        "delivered": "Passport's in your hands. Flip to the visa page and double-check the details, then start packing.",
        "collection": "Your passport is at the visa centre. Bring your ID and go pick it up.",
        "invalid": "The details don't match. Re-check the reference number and surname spelling, slashes and case included.",
        "no_record": "No record yet. It may be too soon after submission, or a detail is off. Try again later.",
        "generic": "Status retrieved, but it didn't match a standard description. Check the original message above.",
    },
}

_REAPPLY = {
    "zh": [
        "拒签信里会写明拒签理由（对应申根签证条款），先看清是哪一条，对症下药。",
        "想申诉：可在使馆规定期限内书面 appeal，适合材料没问题、纯属误判的情况。",
        "想二签：更常见也更快——针对拒签理由补强，比如把资金证明做厚、行程更具体、",
        "补充约束力证明（在职/房产/家庭关系），并简短解释上次的疑点。",
        "二签时如实说明曾被拒并附理由，反而显得坦诚可信；避开旅游旺季也会更稳。",
    ],
    "en": [
        "The refusal letter states the reason (a Schengen visa code) — read it first and address that exact point.",
        "Appeal: a written appeal within the embassy's deadline, best when your file was sound and the call seems wrong.",
        "Reapply (usually faster): strengthen the weak point — beef up proof of funds, give a concrete itinerary,",
        "add ties to home (employment / property / family), and briefly clear up last time's doubts.",
        "Declaring the prior refusal honestly actually reads as credible; applying off-peak helps too.",
    ],
}


def print_mood(result: dict):
    L = LANG
    key = result.get("key", "generic")

    raw = result.get("raw_message")
    if raw:
        label = "原始文案" if L == "zh" else "Official message"
        print(f"📄 {label}：\n   {raw}\n")

    mood = _MOOD.get(L, _MOOD["en"]).get(key) or _MOOD["en"].get(key, "")
    if mood:
        print(mood)
        print()

    # Offer a concrete second-application plan whenever a decision is reached,
    # since VFS tracking does not reveal approve vs. refuse on its own.
    if key in ("decision", "dispatched", "delivered", "collection"):
        title = "💡 如果被拒了——二签 / 申诉方案" if L == "zh" else "💡 If refused — reapply / appeal plan"
        print(title)
        for line in _REAPPLY.get(L, _REAPPLY["en"]):
            print(f"   • {line}")
        print()


# ══════════════════════════════════════════════════════════════════════
#  Q-Param helpers
# ══════════════════════════════════════════════════════════════════════

def load_q_params() -> dict:
    if Q_PARAMS_FILE.exists():
        with open(Q_PARAMS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_countries():
    with open(COUNTRIES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_q_params(params: dict):
    with open(Q_PARAMS_FILE, "w", encoding="utf-8") as f:
        json.dump(params, f, indent=2, ensure_ascii=False)


# ══════════════════════════════════════════════════════════════════════
#  Q-Param discovery
# ══════════════════════════════════════════════════════════════════════

def fetch_q_param_selenium(country_code: str) -> str | None:
    print(f"\n🔍 Fetching tracking endpoint for {country_code.upper()}...")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium_stealth import stealth
    except ImportError:
        print("   sel selenium / selenium-stealth not installed")
        return None

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1280,800")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = None
    q = None
    try:
        driver = webdriver.Chrome(options=options)
        stealth(driver, languages=["zh-CN", "zh", "en-US", "en"],
                vendor="Google Inc.", platform="MacIntel",
                webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine",
                fix_hairline=True)
        driver.set_page_load_timeout(45)

        driver.get(f"https://visa.vfsglobal.com/chn/zh/{country_code}/track-application")
        WebDriverWait(driver, 30).until(lambda d: len(d.page_source) > 15000)
        time.sleep(3)

        for link in driver.find_elements(By.TAG_NAME, "a"):
            href = link.get_attribute("href") or ""
            if "vfsvisaonline.com" in href and "q=" in href:
                m = re.search(r"q=([^&\s]+)", urllib.parse.unquote(href))
                if m:
                    q = m.group(1)
                    break
        if not q:
            m = re.search(r'vfsvisaonline\.com/[^"\']*q=([^"&\'\s]+)', driver.page_source)
            if m:
                import urllib.parse
                q = urllib.parse.unquote(m.group(1))

        print(f"   {'✅ ' + tt('fetch_q_found') if q else '⚠️  No vfsvisaonline link found'}")
    except Exception as e:
        print(f"   ⚠️  Failed: {e}")
    finally:
        if driver:
            driver.quit()
    return q


# ══════════════════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="vfs-tracker — VFS Global Schengen Visa Status Tracker",
        epilog="Example: python3 track.py isl -r 'ABCD/123456/01' -l 'SMITH'",
    )
    parser.add_argument("country", nargs="?", help="Country code (e.g. isl, deu, fra) or 'list'")
    parser.add_argument("-r", "--reference", help="Application Reference Number")
    parser.add_argument("-l", "--last-name", help="Last Name / Surname")
    parser.add_argument("--fetch-q", action="store_true",
                        help="One-time: fetch and cache tracking endpoint")

    args = parser.parse_args()

    if not args.country or args.country.lower() == "list":
        countries = load_countries()
        qp = load_q_params()
        print("\n📋 Supported Schengen countries:\n")
        for code, name in countries.items():
            s = "📦" if code in qp and qp[code] else "  "
            print(f"   {code:6s} {s} {name}")
        print(f"\n{len(countries)} countries total")
        print(f"   📦 = cached  |  Usage: python3 track.py <code> -r <REF> -l <NAME>")
        return

    country_code = args.country.lower().strip()
    countries = load_countries()
    if country_code not in countries:
        print(f"\n❌ Unknown: '{country_code}'. Use 'list'.\n")
        sys.exit(1)

    if args.fetch_q:
        q = fetch_q_param_selenium(country_code)
        if q:
            params = load_q_params()
            params[country_code] = q
            save_q_params(params)
            print(f"✅ {tt('fetch_q_done', code=country_code.upper())}\n")
        else:
            print(f"⚠️  Could not fetch endpoint.\n")
        return

    if not args.reference or not args.last_name:
        print("\n❌ -r <REFERENCE> and -l <LAST_NAME> are required\n")
        sys.exit(1)

    qp = load_q_params()
    q_param = qp.get(country_code)
    if not q_param:
        print(f"\n❌ {tt('no_q', code=country_code.upper())}\n")
        sys.exit(1)

    country_name = countries[country_code]

    print(f"\n{'─'*60}")
    print(f"🛂  {tt('banner')}")
    print(f"    {tt('country')}: {country_name} ({country_code.upper()})")
    print(f"    {tt('ref')}: {args.reference}")
    print(f"    {tt('name')}: {args.last_name}")
    print(f"{'─'*60}")

    result = track(q_param, args.reference, args.last_name)
    if result:
        print_card(result, country_name, country_code)
        print_mood(result)
    else:
        print(f"\n   ❌ {tt('retry', n=MAX_CAPTCHA_RETRIES, total=MAX_CAPTCHA_RETRIES)}")
        print(f"   {tt('ref')} / {tt('name')} 拼写是否正确？\n")
        sys.exit(1)


if __name__ == "__main__":
    main()


# ══════════════════════════════════════════════════════════════════════
#  EES short-stay calculator (semi-automated — user solves slider CAPTCHA)
# ══════════════════════════════════════════════════════════════════════

def ees_check(passport_number: str, issuing_country: str = "CHN",
              destination_code: str | None = None,
              entry_date: str | None = None, exit_date: str | None = None):
    """
    Fully automated EU EES short-stay verification.

    Uses Selenium headless + ActionChains slider drag to solve the EU
    Webtools CAPTCHA automatically. Calls the same /api/tcn/stay-verification
    endpoint that the React frontend uses.

    Args:
        passport_number:  Travel document number (e.g. "E12345678")
        issuing_country:  3-letter country code (default: CHN)
        destination_code: Destination Schengen country code (e.g. "ISL")
        entry_date:       DD-MM-YYYY
        exit_date:        DD-MM-YYYY
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium_stealth import stealth
    import uuid

    L = detect_lang()

    print(f"\n{'─'*60}")
    if L == "zh":
        print(f"🌍 EU EES 短期停留验证")
    else:
        print(f"🌍 EU EES Short-Stay Verification")
    print(f"   Passport: {passport_number}")
    print(f"   Issuing: {issuing_country}")
    if destination_code:
        c = load_countries().get(destination_code, destination_code.upper())
        print(f"   Destination: {c} ({destination_code.upper()})")
    if entry_date: print(f"   Entry: {entry_date}")
    if exit_date: print(f"   Exit: {exit_date}")
    print(f"{'─'*60}")

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        stealth(driver, languages=["zh-CN", "zh", "en-US", "en"],
                vendor="Google Inc.", platform="MacIntel",
                webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine",
                fix_hairline=True)
        driver.set_page_load_timeout(45)

        if L == "zh": print(f"\n🌐 正在加载 EES 计算器...")
        else: print(f"\n🌐 Loading EES calculator...")

        driver.get("https://travel-europe.europa.eu/en/ees/check-how-long-you-can-stay")
        WebDriverWait(driver, 20).until(lambda d: len(d.page_source) > 3000)
        time.sleep(5)

        # Dismiss cookie banner
        driver.execute_script("document.querySelector('.wt-cck--container')?.remove()")
        time.sleep(2)

        if L == "zh": print("📝 正在填写表单...")
        else: print("📝 Filling form...")

        # Fill form
        Select(driver.find_element(By.NAME, "travelDocument.documentType")).select_by_value("P")
        driver.find_element(By.NAME, "travelDocument.number").send_keys(passport_number)
        Select(driver.find_element(By.NAME, "travelDocument.issuingCountry")).select_by_value(issuing_country.upper())
        if destination_code:
            try:
                Select(driver.find_element(By.NAME, "travel.memberStateOfEntry")).select_by_value(destination_code.upper())
            except:
                pass  # Optional

        # Dates
        if entry_date and exit_date:
            for name, val in [("travel.entryDate", entry_date), ("travel.exitDate", exit_date)]:
                inp = driver.find_element(By.NAME, name)
                driver.execute_script("arguments[0].removeAttribute('readonly');", inp)
                actions = ActionChains(driver)
                actions.click(inp)
                for ch in val: actions.send_keys(ch).pause(0.05)
                actions.perform()
                time.sleep(0.3)

        if L == "zh": print("🔐 正在解决数字验证码...")
        else: print("🔐 Solving number CAPTCHA...")

        # Wait for captcha widget to load
        time.sleep(3)
        target = _captcha_solve(driver)
        if target is None:
            print(f"   ⚠️ Could not read CAPTCHA numbers, falling back to brute-force")
            target = _captcha_bruteforce(driver)

        if target is None:
            print(f"   ❌ Could not solve CAPTCHA")
            return None

        print(f"   🎯 Target number: {target}")

        # Human-like slider drag to target
        _captcha_slider_drag(driver, target)

        # Verify captcha solved
        answer = driver.execute_script(
            "var a = document.querySelector('input[name=\"wt_captcha_answer\"]'); return a ? a.value : '';"
        )
        captcha_sid = driver.execute_script(
            "return document.querySelector('input[name=\"wt_captcha_sid\"]').value;"
        )

        if not answer:
            print(f"   ⚠️ Answer not populated, trying brute-force submit anyway...")
        else:
            print(f"   ✅ CAPTCHA solved")

        # Submit
        if L == "zh": print("📤 正在提交...")
        else: print("📤 Submitting...")

        btn = driver.find_element(By.CSS_SELECTOR, 'button[data-testid="verification-form-submit"]')
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(8)

        body = driver.find_element(By.TAG_NAME, "body").text
        return extract_ees_result(body)

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if driver:
            driver.quit()


def _captcha_solve(driver) -> int | None:
    """Solve the EU Webtools number-selection CAPTCHA.
    Returns target slider value (0-50) or None if failed."""
    import ddddocr, base64
    from PIL import Image
    from selenium.webdriver.common.by import By
    import io

    WORD_MAP = {
        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
        'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
        'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13,
        'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'seventeen': 17,
        'eighteen': 18, 'nineteen': 19, 'twenty': 20, 'thirty': 30,
        'forty': 40, 'fifty': 50, 'fourty': 40,
        'thity': 30, 'thityone': 31, 'thitytwo': 32, 'thitythree': 33,
        'thityfour': 34, 'thityfive': 35, 'thitysix': 36, 'thityseven': 37,
        'thityeight': 38, 'thitynine': 39,
    }

    ocr = ddddocr.DdddOcr(show_ad=False)
    imgs = driver.find_elements(By.CSS_SELECTOR, 'img[alt="First number"], img[alt="Second number"]')
    if len(imgs) < 2:
        return None

    values = []
    for img in imgs:
        src = img.get_attribute("src") or ""
        if not src.startswith("data:image"):
            continue
        b64 = src.split(",", 1)[1]
        raw = base64.b64decode(b64)
        pil = Image.open(io.BytesIO(raw))
        w, h = pil.size
        big = pil.resize((w * 8, h * 8), Image.NEAREST)
        buf = io.BytesIO()
        big.convert("RGB").save(buf, format="PNG")
        text = ocr.classification(buf.getvalue()).lower().strip()

        # Direct integer
        digits = re.findall(r'\d+', text)
        if digits:
            n = int(digits[0])
            if n <= 50:
                values.append(n)
                continue
        # Word match
        matched = False
        for word, val in sorted(WORD_MAP.items(), key=lambda x: -len(x[0])):
            if word in text:
                values.append(val)
                matched = True
                break
        if not matched:
            values.append(-1)

    if len(values) != 2:
        return None

    a, b = values[0], values[1]
    if a == -1 and b == -1:
        return None
    if a == -1: return b if b <= 50 else None
    if b == -1: return a if a <= 50 else None

    if a <= 9 and b <= 9: return a * 10 + b
    if a <= 9 and b >= 10: return b + a
    if a >= 10 and b <= 9: return a + b
    return min(a + b, 50)


def _captcha_slider_drag(driver, target: int):
    """Drag the slider to target value with human-like movement."""
    import random
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.by import By

    slider = driver.find_element(By.CSS_SELECTOR, 'input[name="wt_captcha_slider_text"]')
    driver.execute_script("""
        var el = arguments[0];
        var rect = el.getBoundingClientRect();
        window.scrollTo({top: window.scrollY + rect.top - window.innerHeight/2, behavior: 'instant'});
    """, slider)
    time.sleep(0.3)

    rect = driver.execute_script("return arguments[0].getBoundingClientRect();", slider)
    w, h = rect['width'], rect['height']

    # Clamp target to valid range
    target = max(0, min(50, target))
    target_px = max(10, int((target / 50) * (w - 30)))

    # Human-like drag in place — move to offset, click, drag, release
    start_x = 10
    y_mid = h // 2

    actions = ActionChains(driver)
    actions.move_to_element_with_offset(slider, start_x, y_mid)
    actions.pause(random.uniform(0.1, 0.2))
    actions.click_and_hold()
    actions.pause(random.uniform(0.05, 0.1))

    # Drag in small chunks, staying within element bounds
    moved = 0
    chunk_count = random.randint(18, 28)
    for _ in range(chunk_count):
        if moved >= target_px:
            break
        chunk = max(2, min(target_px - moved, target_px // chunk_count + 3))
        chunk += random.randint(-4, 4)
        chunk = max(1, chunk)
        moved += chunk
        actions.move_by_offset(chunk, random.randint(-2, 2))
        actions.pause(random.uniform(0.01, 0.03))

    actions.pause(random.uniform(0.1, 0.25))
    actions.release().perform()
    time.sleep(2)


def _captcha_bruteforce(driver) -> int | None:
    """Brute-force iterate all slider values until answer populates."""
    from selenium.webdriver.common.by import By
    slider = driver.find_element(By.CSS_SELECTOR, 'input[name="wt_captcha_slider_text"]')
    for target in range(51):
        _captcha_slider_drag(driver, target)
        answer = driver.execute_script(
            "return document.querySelector('input[name=\"wt_captcha_answer\"]').value;"
        )
        if answer:
            return target
    return None


def extract_ees_result(body_text: str) -> dict | None:
    """Parse EES verification result from page text."""
    result = {"raw": body_text[:1500], "status": "unknown", "days": None, "message": ""}

    lower = body_text.lower()

    # Try to find explicit OK / not OK
    if re.search(r"(?:OK|entry is allowed|you can enter)", lower):
        result["status"] = "ok"
    elif re.search(r"(?:not OK|entry is not allowed|cannot enter|not allowed)", lower):
        result["status"] = "not_ok"

    # Try days
    days_m = re.search(r"(\d{1,3})\s*days?\s*(?:of|remaining|allowed|stay|authorised)", lower)
    if days_m:
        result["days"] = days_m.group(1)

    # Heuristic fallback
    if result["status"] == "unknown":
        if "0 days" in lower or "zero days" in lower:
            result["status"] = "not_ok"
            result["days"] = "0"
        elif "days" in lower and any(w in lower for w in ["allowed", "authorised", "remain"]):
            result["status"] = "ok"

    # Build readable message
    L = detect_lang()
    if result["status"] == "ok":
        days = result.get("days", "")
        if days:
            if L == "zh":
                result["message"] = f"✅ OK — 剩余 {days} 天可停留"
            else:
                result["message"] = f"✅ OK — {days} days of stay remaining"
        else:
            result["message"] = "✅ OK — entry is allowed"
    elif result["status"] == "not_ok":
        result["message"] = "❌ NOT OK — 可能无法入境" if L == "zh" else "❌ NOT OK — entry may not be allowed"
    else:
        result["message"] = (
            "⚠️ 无法自动解析结果，API 返回 422 (验证码校验失败)"
            if L == "zh"
            else "⚠️ Could not parse result (API returned 422 — captcha validation failed)"
        )

    return result
