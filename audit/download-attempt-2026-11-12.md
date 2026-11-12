# NSE Raw Report Download Attempt

**Attempt date:** 2026-11-12  
**Requested by user:** Assistant to download and inspect the NSE files directly.

## Reports targeted

For the latest prior trading session requested in this attempt (11-Nov-2026), candidate filenames were tested:

- `fo11112026.zip`
- `BhavCopy_NSE_FO_0_0_0_20261111_F_0000.csv.zip`
- `futidx11112026.csv`
- `optidx11112026.csv`
- `fao_participant_oi_11112026.csv`
- `fao_participant_vol_11112026.csv`

## Result

**No raw file was downloaded.** Direct archive-host requests failed at DNS/network resolution from the execution environment. Opening the candidate ZIP URLs through the web retrieval service also returned inaccessible/internal-error responses.

A web-indexed NSE report-page result was available for 23-Oct-2026 and listed these filenames and approximate sizes:

- `fo23102026.zip` — 779.46 KB
- `BhavCopy_NSE_FO_0_0_0_20261023_F_0000.csv.zip` — 1.30 MB
- `fao_participant_oi_23102026.csv` — 0.96 KB
- `fao_participant_vol_23102026.csv` — 0.98 KB

This is **metadata from an indexed report listing only**, not the file bytes. The listing is older than the requested 11-Nov-2026 session and cannot be substituted as a same-day file.

## Integrity and conclusions

- No ZIP archive was received.
- No archive checksum or exact byte size was verified locally.
- No ZIP members, CSV headers, or data rows were inspected.
- No NIFTY contract-level fields are claimed as verified from these files.
- The attempted direct URL patterns remain unconfirmed.
- Do not build a downloader based solely on these guessed filenames.
- Retry via the official NSE report page in a normal browser session or an approved official download mechanism; verify current NSE terms before automated collection or redistribution.

**Conclusion:** This attempt confirms that the official report listing can be researched, but the execution environment could not retrieve the underlying binary report files. Raw-data audit remains pending.
