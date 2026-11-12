# NSE F&O download + content audit

This workflow is an experimental downloader for public NSE F&O report files. It does not bypass access controls, CAPTCHA, login, rate limits, or terms. A successful HTTP download does **not** establish permission for redistribution or public hosting.

## Run
1. Open **Actions** in this repository.
2. Select **NSE F&O download and audit**.
3. Choose **Run workflow** and enter a valid NSE trading date (YYYY-MM-DD).
4. Download the run artifact named `nse-audit-YYYY-MM-DD`.

The artifact contains raw downloaded files, extracted ZIP members, and `manifest.json` with source URL, byte size, SHA-256, ZIP CRC result, CSV headers, row counts, sample rows, and duplicate hashes.

## Current limits
- The official NSE report catalogue is queried first; known archive filename patterns are fallback candidates, not guaranteed live links.
- If NSE returns an HTML block page, an empty file, or a non-ZIP payload, the run records failure instead of treating it as data.
- Only Market Activity ZIP, UDiFF F&O Bhavcopy ZIP, Participant OI CSV and Participant Volume CSV are requested.
- A ZIP is integrity-tested before safe extraction. ZIP path traversal entries are rejected.
- This workflow does not publish a GitHub Release. Raw exchange data may be subject to NSE usage/redistribution restrictions; keep artifacts private to repository collaborators until rights are confirmed.
- No AI labels such as “confirmed absorption” are generated from these reports.
