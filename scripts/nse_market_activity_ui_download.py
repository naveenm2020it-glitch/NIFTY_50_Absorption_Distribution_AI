#!/usr/bin/env python3
"""Download NSE F&O Market Activity through the official report-page UI."""
from __future__ import annotations
import argparse, hashlib, json, re, sys, zipfile
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

URL = "https://www.nseindia.com/all-reports-derivatives"
REPORT = "F&O - Market Activity Report"

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="Trading date YYYY-MM-DD")
    ap.add_argument("--out", default="audit-output")
    args = ap.parse_args()
    day = datetime.strptime(args.date, "%Y-%m-%d")
    out = Path(args.out)
    raw = out / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    target = raw / f"fo{day:%d%m%Y}.zip"
    evidence = {
        "report": REPORT, "requested_trade_date": args.date,
        "source_page": URL, "download_method": "official_NSE_report_page_UI",
        "retrieved_at_utc": datetime.utcnow().isoformat() + "Z"
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True, locale="en-IN")
        page = context.new_page()
        page.set_default_timeout(25000)
        try:
            response = page.goto(URL, wait_until="domcontentloaded", timeout=90000)
            if response and response.status >= 400:
                raise RuntimeError(f"NSE report page returned HTTP {response.status}")
            page.locator("body").wait_for()
            page.get_by_text(REPORT, exact=True).first.wait_for(state="visible", timeout=60000)

            # Identify the smallest report-area ancestor containing the report row,
            # a date control, and the Multiple file Download action.
            info = page.evaluate("""(reportName) => {
              const norm = s => (s || '').replace(/\\s+/g, ' ').trim();
              const nodes = [...document.querySelectorAll('body *')].filter(e =>
                e.children.length === 0 && norm(e.textContent) === reportName);
              if (!nodes.length) return {error:'report label not found'};
              let e = nodes[0], chain=[];
              for (let i=0; e && i<12; i++, e=e.parentElement) {
                const text = norm(e.innerText);
                const inputs = [...e.querySelectorAll('input')].map(x => ({
                  type:x.type, name:x.name, id:x.id, placeholder:x.placeholder,
                  aria:x.getAttribute('aria-label'), value:x.value,
                  outer:x.outerHTML.slice(0,300)
                }));
                chain.push({tag:e.tagName, cls:String(e.className||'').slice(0,180),
                  text:text.slice(0,1200), inputs,
                  hasDownload:/Multiple file Download/i.test(text),
                  hasDate:/Date/i.test(text)});
                if (/Multiple file Download/i.test(text) &&
                    /Date/i.test(text) && inputs.length) break;
              }
              return {chain};
            }""", REPORT)
            evidence["dom_probe"] = info
            if info.get("error"):
                raise RuntimeError(info["error"])

            # Find the report's date input by searching inputs whose nearby parent
            # text includes both the report area and the Date label.
            date_candidates = page.locator("input")
            chosen = None
            for i in range(await_count(date_candidates)):
                item = date_candidates.nth(i)
                meta = item.evaluate("""el => {
                  let p=el;
                  for(let i=0;p && i<7;i++,p=p.parentElement){
                    const t=(p.innerText||'').replace(/\\s+/g,' ');
                    if(t.includes('F&O - Market Activity Report') && /Date/.test(t) && /Multiple file Download/i.test(t))
                      return {type:el.type, value:el.value, placeholder:el.placeholder, parentText:t.slice(0,900)};
                  }
                  return null;
                }""")
                if meta:
                    chosen = item
                    evidence["date_input"] = meta
                    break
            if chosen is None:
                raise RuntimeError("Could not uniquely locate the F&O date input; inspect dom_probe in artifact")

            input_type = chosen.get_attribute("type") or "text"
            date_value = day.strftime("%Y-%m-%d") if input_type == "date" else day.strftime("%d-%m-%Y")
            chosen.fill(date_value)
            chosen.dispatch_event("input")
            chosen.dispatch_event("change")
            page.wait_for_timeout(5000)
            expected_heading = f"Reports for {day:%d-%b-%Y}"
            if expected_heading.lower() not in (page.locator('body').inner_text(timeout=20000)).lower():
                raise RuntimeError(f"NSE page did not confirm requested date heading: {expected_heading}")
            evidence["confirmed_date_heading"] = expected_heading

            # Confirm the selected report exists in the requested date's report list.
            report_locator = page.get_by_text(REPORT, exact=True).first
            report_locator.wait_for(state="visible", timeout=30000)
            report_context = report_locator.evaluate("""el => {
              let p=el;
              for(let i=0;p && i<8;i++,p=p.parentElement){
                const t=(p.innerText||'').replace(/\\s+/g,' ');
                if(/Multiple file Download/i.test(t) && t.includes('F&O - Market Activity Report'))
                  return {text:t.slice(0,1500), inputs:[...p.querySelectorAll('input')].map(x=>({type:x.type,checked:x.checked,outer:x.outerHTML.slice(0,250)}))};
              }
              return null;
            }""")
            evidence["report_context"] = report_context
            if not report_context:
                raise RuntimeError("Report row is not in a recognizable F&O download group after date selection")

            # Select only the checkbox associated with the exact report row.
            checkbox = report_locator.locator("xpath=ancestor::*[.//input[@type='checkbox']][1]").locator("input[type='checkbox']").first
            if await_count(checkbox) == 0:
                # Some NSE layouts place the checkbox in the immediately adjacent label container.
                checkbox = report_locator.locator("xpath=..").locator("input[type='checkbox']").first
            if await_count(checkbox) == 0:
                raise RuntimeError("Could not find the report's selection checkbox")
            checkbox.check(force=True)
            page.wait_for_timeout(500)

            # Click the Multiple file Download control in the same report group.
            download_button = page.get_by_text("Multiple file Download", exact=True)
            button_count = await_count(download_button)
            clicked = False
            for i in range(button_count):
                candidate = download_button.nth(i)
                same_group = candidate.evaluate("""el => {
                  let p=el;
                  for(let i=0;p && i<8;i++,p=p.parentElement){
                    const t=(p.innerText||'').replace(/\\s+/g,' ');
                    if(t.includes('F&O - Market Activity Report')) return true;
                  }
                  return false;
                }""")
                if same_group:
                    with page.expect_download(timeout=90000) as download_info:
                        candidate.click()
                    download = download_info.value
                    download.save_as(str(target))
                    evidence["suggested_filename"] = download.suggested_filename
                    evidence["download_url"] = download.url
                    clicked = True
                    break
            if not clicked:
                raise RuntimeError("Could not locate Multiple file Download button for the F&O report group")

            if not target.exists() or target.stat().st_size == 0:
                raise RuntimeError("NSE download event completed but output file is empty")
            if not zipfile.is_zipfile(target):
                raise RuntimeError("Downloaded file is not a ZIP archive")
            with zipfile.ZipFile(target) as zf:
                bad = zf.testzip()
                if bad:
                    raise RuntimeError(f"ZIP integrity failure in member {bad}")
                members = [{"name":x.filename,"size":x.file_size} for x in zf.infolist() if not x.is_dir()]
            evidence.update({
                "status":"DOWNLOADED", "filename":target.name, "bytes":target.stat().st_size,
                "sha256":sha256(target), "zip_integrity":"PASS", "members":members
            })
        except Exception as exc:
            evidence.update({"status":"FAILED","error":str(exc)})
            try:
                page.screenshot(path=str(out / "nse-market-activity-debug.png"), full_page=True)
                (out / "nse-market-activity-debug.html").write_text(page.content(), encoding="utf-8")
            except Exception:
                pass
            (out / "nse-market-activity-ui.json").write_text(json.dumps(evidence,indent=2,ensure_ascii=False),encoding="utf-8")
            print(json.dumps(evidence,indent=2,ensure_ascii=False))
            browser.close()
            return 1
        finally:
            browser.close()

    (out / "nse-market-activity-ui.json").write_text(json.dumps(evidence,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(evidence,indent=2,ensure_ascii=False))
    return 0

def await_count(locator) -> int:
    try:
        return locator.count()
    except Exception:
        return 0

if __name__ == "__main__":
    sys.exit(main())
