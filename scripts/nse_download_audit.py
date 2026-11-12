#!/usr/bin/env python3
"""Download and audit selected public NSE F&O reports. No credentials or data fabrication."""
from __future__ import annotations
import argparse, csv, hashlib, json, os, re, sys, time, zipfile
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests

BASE = "https://www.nseindia.com"
ARCHIVE = "https://nsearchives.nseindia.com/content/fo/"
ARCHIVES_HOSTS = ("https://nsearchives.nseindia.com", "https://archives.nseindia.com")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
REPORT_PAGE = BASE + "/all-reports-derivatives"

class Anchors(HTMLParser):
    def __init__(self):
        super().__init__(); self.href = None; self.text = ""; self.items = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href"); self.text = ""
    def handle_data(self, data):
        if self.href is not None: self.text += data
    def handle_endtag(self, tag):
        if tag == "a" and self.href is not None:
            self.items.append((self.text.strip(), self.href)); self.href = None; self.text = ""

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def safe_name(s): return re.sub(r"[^A-Za-z0-9._-]+","_",s)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="Trading date YYYY-MM-DD")
    ap.add_argument("--out", default="audit-output")
    args=ap.parse_args()
    day=datetime.strptime(args.date,"%Y-%m-%d")
    ddmmyyyy=day.strftime("%d%m%Y"); ymd=day.strftime("%Y%m%d")
    out=Path(args.out); raw=out/"raw"; extracted=out/"extracted"
    raw.mkdir(parents=True,exist_ok=True); extracted.mkdir(parents=True,exist_ok=True)
    s=requests.Session(); s.headers.update({"User-Agent":UA,"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"})
    errors=[]; manifest={"requested_trade_date":args.date,"source_page":REPORT_PAGE,"retrieved_at_utc":datetime.utcnow().isoformat()+"Z","files":[],"errors":errors}
    try:
        s.get(BASE,timeout=30)
        page=s.get(REPORT_PAGE,timeout=45); page.raise_for_status()
        parser=Anchors(); parser.feed(page.text)
        # Official report catalogue links are preferred. The archive patterns are fallback candidates only.
        wanted=[
          ("market_activity",f"fo{ddmmyyyy}.zip",f"fo{ddmmyyyy}.zip"),
          ("udiff_fo_bhavcopy",f"BhavCopy_NSE_FO_0_0_0_{ymd}_F_0000.csv.zip",f"BhavCopy_NSE_FO_0_0_0_{ymd}_F_0000.csv.zip"),
          ("participant_oi",f"fao_participant_oi_{ddmmyyyy}.csv",f"fao_participant_oi_{ddmmyyyy}.csv"),
          ("participant_volume",f"fao_participant_vol_{ddmmyyyy}.csv",f"fao_participant_vol_{ddmmyyyy}.csv"),
        ]
        for key,filename,fallback in wanted:
            matches=[urljoin(REPORT_PAGE,h) for label,h in parser.items if filename.lower() in (label+" "+h).lower()]
            # Participant reports are stored under /content/nsccl/, not /content/fo/.
            if matches:
                candidates = matches
            elif key in ("participant_oi", "participant_volume"):
                candidates = [f"{host}/content/nsccl/{filename}" for host in ARCHIVES_HOSTS]
            elif key == "market_activity":
                candidates = [f"{host}/content/fo/{filename}" for host in ARCHIVES_HOSTS]
            else:
                candidates = [f"{host}/content/fo/{filename}" for host in ARCHIVES_HOSTS]
            saved=None; last_error=None
            for url in candidates:
                try:
                    r=s.get(url,headers={"Referer":REPORT_PAGE},timeout=90,stream=True)
                    if r.status_code != 200: raise RuntimeError(f"HTTP {r.status_code} for {url}")
                    ct=r.headers.get("Content-Type","").lower()
                    first=next(r.iter_content(64*1024),b"")
                    if not first: raise RuntimeError("empty response")
                    if b"<html" in first[:512].lower() or b"access denied" in first[:2048].lower():
                        raise RuntimeError("server returned HTML/block page, not report bytes")
                    dest=raw/safe_name(filename)
                    with open(dest,"wb") as f:
                        f.write(first)
                        for chunk in r.iter_content(1024*1024):
                            if chunk: f.write(chunk)
                    if dest.stat().st_size < 32: raise RuntimeError("suspiciously small file")
                    if filename.endswith(".zip"):
                        if not zipfile.is_zipfile(dest): raise RuntimeError("download is not a valid ZIP")
                        with zipfile.ZipFile(dest) as z:
                            bad=z.testzip()
                            if bad: raise RuntimeError(f"ZIP CRC failure: {bad}")
                            members=[]
                            for info in z.infolist():
                                if info.is_dir(): continue
                                # Prevent path traversal when extracting.
                                target=(extracted/info.filename).resolve()
                                if extracted.resolve() not in target.parents:
                                    raise RuntimeError(f"unsafe ZIP member path: {info.filename}")
                                target.parent.mkdir(parents=True,exist_ok=True)
                                with z.open(info) as src, open(target,"wb") as dst:
                                    while True:
                                        chunk=src.read(1024*1024)
                                        if not chunk: break
                                        dst.write(chunk)
                                members.append({"member":info.filename,"size":info.file_size,"sha256":sha256(target)})
                            zip_members=members
                    else: zip_members=[]
                    saved=dest
                    manifest["files"].append({"key":key,"filename":filename,"url":url,"http_status":r.status_code,"content_type":ct,"bytes":dest.stat().st_size,"sha256":sha256(dest),"zip_integrity":"PASS" if filename.endswith(".zip") else "N/A","members":zip_members})
                    break
                except Exception as e: last_error=str(e)
            if saved is None:
                errors.append({"key":key,"filename":filename,"error":last_error or "No catalogue link or fallback succeeded"})
        # Inspect all extracted CSVs and downloaded CSVs: encoding-safe preview, delimiter/header, row count.
        inspections=[]
        for p in sorted(list(extracted.rglob("*.csv"))+list(raw.glob("*.csv"))):
            try:
                with p.open("r",encoding="utf-8-sig",errors="replace",newline="") as f:
                    sample=f.read(8192); f.seek(0)
                    try: dialect=csv.Sniffer().sniff(sample,delimiters=",;|\\t")
                    except csv.Error: dialect=csv.excel
                    reader=csv.reader(f,dialect); header=next(reader,[])
                    preview=[]; count=0
                    for row in reader:
                        count+=1
                        if len(preview)<5: preview.append(row[:30])
                inspections.append({"file":str(p.relative_to(out)),"header":header,"data_rows":count,"preview_first_5_rows":preview})
            except Exception as e: inspections.append({"file":str(p.relative_to(out)),"inspection_error":str(e)})
        # Duplicate detection by SHA-256 across all raw/extracted files.
        hashes={}
        for p in sorted(x for x in out.rglob("*") if x.is_file()):
            digest=sha256(p); hashes.setdefault(digest,[]).append(str(p.relative_to(out)))
        manifest["duplicate_groups"]=[{"sha256":h,"files":paths} for h,paths in hashes.items() if len(paths)>1]
        manifest["csv_inspections"]=inspections
        manifest["status"]="PASS" if manifest["files"] and not errors else ("PARTIAL" if manifest["files"] else "FAILED")
    except Exception as e:
        errors.append({"stage":"catalogue","error":str(e)})
        manifest["status"]="FAILED"
    out.mkdir(exist_ok=True)
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({"status":manifest["status"],"downloaded":len(manifest["files"]),"failed":len(errors),"manifest":str(out/"manifest.json")},indent=2))
    return 0 if manifest["status"] == "PASS" else (1 if manifest["status"] == "PARTIAL" else 2)

if __name__=="__main__": sys.exit(main())
