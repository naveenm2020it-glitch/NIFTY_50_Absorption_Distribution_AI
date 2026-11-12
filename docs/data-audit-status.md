# NIFTY 50 Absorption & Distribution AI — Data Audit Status

**Status:** Partial raw-file verification completed for 11-Nov-2026; three report downloads remain unavailable.  
**Audit date:** 2026-11-12  
**Scope:** NIFTY 50 only. This document does not claim that any source is licensed for automated collection, redistribution, or commercial use.

## 1. Verified official NSE report availability

Official NSE report pages list the following F&O reports:

- F&O Market Activity Report (ZIP)
- F&O UDiFF Common Bhavcopy Final (ZIP)
- Participant-wise Open Interest (CSV)
- Participant-wise Trading Volumes (CSV)
- FII Derivatives Statistics (XLS)
- Top 10 Clearing Member Volumes (CSV)
- Daily Settlement Prices (CSV)
- Daily Volatility (CSV)
- Combined Delta Equivalent Open Interest across exchanges (CSV)
- F&O contract files

Official page: https://www.nseindia.com/all-reports-derivatives

The report listing confirms that report types are offered. It does **not** by itself verify the contents, historical coverage, or automated-download permission of each file.

## 2. Market Activity report candidates

The Market Activity ZIP is expected to contain report components such as:

- `futidxDDMMYYYY.csv` — index futures summary
- `optidxDDMMYYYY.csv` — index options summary
- `fo_DDMMYYYY.csv` — F&O product-wise summary

These filename patterns are documented by third-party downloader/catalog material and remain **unverified against an actual downloaded NSE ZIP**. The ZIP must be inspected before relying on these names or their fields.

## 3. Official NIFTY historical data

NSE's Historical Index Data page offers downloadable CSV data with displayed columns:

- Date
- Open
- High
- Low
- Close
- Shares Traded
- Turnover (₹ Cr)

Page: https://www.nseindia.com/reports-indices-historical-index-data

NSE Indices FAQ states that NIFTY 50 historical data is available from 3 July 1990. This is index-level history, not proof of a traded NIFTY spot order book.

FAQ: https://www.nseindia.com/static/products-services/indices-faqs

## 4. Constituent-level data candidates

The NSE NIFTY 50 index page provides a current constituent-list download and a factsheet/methodology link:

https://www.nseindia.com/static/products-services/indices-nifty50-index

Current constituents are not a substitute for historical constituent membership and historical weights. Historical membership/weights must be separately sourced and verified to avoid survivorship and index-reconstitution bias.

## 5. Equity reports useful for constituent analysis

The NSE Capital Market reports page lists:

- Full Bhavcopy and Security Deliverable data
- Security-wise Delivery Positions
- Market Activity Report
- Short Selling
- Bulk Deals
- Block Deals
- CM-UDiFF Common Bhavcopy Final (ZIP)

Page: https://www.nseindia.com/all-reports

These are candidates for analysing the 50 constituent stocks. They must be filtered by the historically valid NIFTY 50 membership for each date. NSE equity volume/delivery data must not be represented as NIFTY spot order flow.

## 6. Important interpretation limits

- NIFTY 50 is an index calculation, not a separately traded central limit order book.
- OHLCV and open interest can support behavioural inference but cannot prove institutional absorption.
- Participant-wise reports are market/category aggregates unless actual file contents prove a narrower scope.
- Futures, options, and constituent-stock evidence must remain separate and be joined only through documented features.
- Use labels such as **Possible Buyer Absorption** and **Possible Seller Distribution** until stronger transaction/order-book evidence is available.
- Do not attribute activity to a named institution without verifiable evidence.

## 7. Legal and access review

NSE website Terms of Use restrict systematic/automated data extraction and impose conditions on copying, storing, displaying, and redistributing website data. Public visibility or manual download availability is not automatic permission for an automated public-facing data service.

Before building a collector or displaying NSE data publicly, review current NSE terms and obtain any required written permission/licence.

Terms page: https://www.nseindia.com/terms-of-use

## 8. Raw-file verification — 11-Nov-2026 (PARTIAL)

### Successfully downloaded and inspected

- Report: F&O UDiFF Common Bhavcopy Final (ZIP)
- Official archive URL: https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_20261111_F_0000.csv.zip
- HTTP status: 200
- ZIP size: 1,359,173 bytes
- ZIP integrity: PASS
- Extracted CSV: 42,331 data rows
- NIFTY rows: 2,245 (instrument types IDF and IDO)
- Trade date in rows: 2026-11-11
- ZIP SHA-256: e7ab0ec53ac7b3bb7bcf36b575ca06ca290b8a0c699deab9231c22b34bd296c2
- Extracted CSV SHA-256: 1104e45784774307e73934320e955bb6e6f94a643f63fbe56e6d83034e73370b

Observed fields include trade date, instrument type, symbol, expiry, strike, option type, OHLC, previous close, underlying price, settlement price, open interest, change in open interest, total traded volume, turnover and number of trades. This is EOD derivatives data, not intraday order-book data.

### Three reports not downloaded

The 11-Nov-2026 pilot attempted these official archive filename patterns; each returned HTTP 404 at the time of the run:

- F&O Market Activity ZIP: `fo11112026.zip`
- Participant-wise Open Interest: `fao_participant_oi_11112026.csv`
- Participant-wise Trading Volumes: `fao_participant_vol_11112026.csv`

The corresponding candidate paths were tested under the NSE F&O archive and did not return files. These reports are marked **NOT DOWNLOADED / UNVERIFIED**, not assumed absent permanently. Re-check the official report catalogue for delayed publication or changed paths before any later attempt.

### Remaining verification checklist

- [ ] Re-check the official catalogue for the three missing 11-Nov reports and obtain their actual download links if published.
- [ ] Download and inspect the Market Activity ZIP; verify its actual member filenames and NIFTY coverage.
- [ ] Download and inspect participant OI and participant volume CSVs; confirm headers, units and category definitions.
- [ ] Compare selected records against official NSE report displays.
- [ ] Record missing dates, duplicates, nulls, schema changes and corrections.
- [ ] Verify terms for automated access, storage and redistribution separately.

**Pilot outcome: PARTIAL — 1 of 4 reports downloaded and validated. No model or public webpage has been created. Automated collection remains paused pending confirmation of NSE terms/permission.**
