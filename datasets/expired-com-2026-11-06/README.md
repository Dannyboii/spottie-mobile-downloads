# Expired .COM domain research dataset — 6 November 2026

## Files
- `expired_com_100000.csv` — exactly 100,000 unique .com domain records with a publisher feed date.
- `expired_com_all_111038.csv` — the complete 111,038 unique .com records extracted.
- `sources_manifest.csv` — the source URL and count for each of 24 daily source files.
- `part-01.csv` through `part-04.csv` — intermediate dated batches before final cross-batch deduplication.

## Provenance
Public daily **expired-domain** files published by WhoisFreaks: https://github.com/WhoisFreaks/daily-expired-and-dropped-domains

24 dated source files from **2026-10-11 to 2026-11-03** were read. Each public file is a sample of domains across multiple TLDs, not a complete snapshot of all expired .com domains. The extraction admitted only valid, single-label ASCII/IDNA-punycode `.com` domain names and normalized to lowercase. Exact duplicates were removed. No generated, invented or guessed names were included. All 111,038 extracted .com names were distinct. The 100,000-row export retains the most recent source dates first, then original order within a file; its oldest contributing date is 2026-10-13.

Columns:
- `domain`: lowercase .com domain name
- `source_date`: date in the publisher's daily source filename. This is **not** a verified individual registration expiration date.

Join `source_date` to `sources_manifest.csv` to find the original URL. `com_records_extracted` counts filtered .com rows per source file. `records_in_100000_file` counts those retained in the 100,000-row export.

## Status and accuracy limitations
**No current registration, auction, redemption, WHOIS, RDAP, purchase availability, ownership, or trademark checks were performed.** Records are publisher-labelled expired / expiry-related, not independently verified as expired today. Some names may have been renewed, re-registered, be on hold, in redemption or pending-delete, or listed at auction. A dropped/expired listing does not prove that a name is available to register.

All source files are free public samples, so the dataset does **not** purport to contain every expired `.com` domain. It is a verifiable 100,000-name research compilation from the specific cited sources.

## Audit
- Dates covered: 2026-10-11 to 2026-11-03
- Source files: 24
- Valid .com rows: 111,038
- Cross-batch duplicate .com names: 0
- Final primary export: 100,000 unique rows
- Full export: 111,038 unique rows
- Collection/compilation date: 2026-11-06
