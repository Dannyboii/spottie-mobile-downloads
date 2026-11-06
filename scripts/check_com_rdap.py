#!/usr/bin/env python3
"""Check .com registration records via Verisign RDAP.

A Verisign 404 means no registry registration was found, NOT a guarantee
that the registrar will allow checkout (reserved/premium/blocked domains).
Non-200/404 responses and network failures are ALWAYS marked unknown.
"""
import argparse
import csv
import datetime as dt
import json
import pathlib
import random
import time
import urllib.error
import urllib.request

SOURCE = pathlib.Path("datasets/expired-com-2026-11-06/expired_com_under_12_chars_53643.csv")
OUTDIR = pathlib.Path("datasets/expired-com-2026-11-06/rdap-results")
COLS = ["domain", "source_date", "registration_status", "checked_at_utc", "rdap_http_status", "detail"]
UA = "DomainRegistrationAudit/1.0 (public RDAP lookup; polite rate limits)"


def check(domain):
    url = "https://rdap.verisign.com/com/v1/domain/" + domain
    last_status, last_detail = "", ""
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/rdap+json, application/json", "User-Agent": UA})
            with urllib.request.urlopen(req, timeout=18) as response:
                status = response.status
                if status == 200:
                    body = json.load(response)
                    found = str(body.get("ldhName") or "").lower()
                    if found == domain.lower():
                        return "registered", "200", "Registry record found"
                    return "unknown", "200", "Response had no matching domain"
                last_status, last_detail = str(status), "Unexpected HTTP status"
        except urllib.error.HTTPError as err:
            last_status = str(err.code)
            if err.code == 404:
                return "unregistered_rdap", "404", "No domain registration found (registrar confirmation required)"
            last_detail = "RDAP server returned HTTP " + str(err.code)
            if err.code not in (429, 500, 502, 503, 504):
                break
            retry = err.headers.get("Retry-After", "")
            try:
                delay = min(30.0, max(1.0, float(retry)))
            except ValueError:
                delay = min(25.0, 2.5 * (attempt + 1))
            if attempt < 3:
                time.sleep(delay + random.random())
        except (TimeoutError, OSError, ValueError, json.JSONDecodeError) as err:
            last_detail = err.__class__.__name__
            if attempt < 3:
                time.sleep(1.5 * (attempt + 1) + random.random())
    return "unknown", last_status, last_detail


def run_shard(shard, total, path):
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        all_rows = list(csv.DictReader(handle))
    current = [row for idx, row in enumerate(all_rows) if idx % total == shard]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLS)
        writer.writeheader()
        for idx, row in enumerate(current, 1):
            domain = row["domain"].lower().strip()
            try:
                status, http, detail = check(domain)
            except Exception as err:
                status, http, detail = "unknown", "", "Unexpected " + err.__class__.__name__
            writer.writerow({
                "domain": domain,
                "source_date": row["source_date"],
                "registration_status": status,
                "checked_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "rdap_http_status": http,
                "detail": detail,
            })
            handle.flush()
            if idx % 100 == 0:
                print(f"shard {shard}: {idx}/{len(current)} checked", flush=True)
            time.sleep(0.15 + random.random() * 0.15)


def merge(folder):
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        expected = {row["domain"].strip().lower() for row in csv.DictReader(handle)}
    rows = {}
    for file in sorted(folder.glob("part-*.csv")):
        with file.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                domain = row["domain"].strip().lower()
                if domain in rows:
                    raise RuntimeError("Duplicate domain found across part files: " + domain)
                rows[domain] = row
    if set(rows) != expected:
        raise RuntimeError(f"Incomplete data: expected {len(expected)} distinct domains, got {len(rows)}, missing {len(expected-set(rows))}")
    OUTDIR.mkdir(parents=True, exist_ok=True)
    sets = [
        ("likely_available_rdap.csv", "unregistered_rdap"),
        ("registered.csv", "registered"),
        ("inconclusive.csv", "unknown"),
    ]
    for filename, selected in sets:
        with (OUTDIR / filename).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=COLS)
            writer.writeheader()
            writer.writerows(rows[d] for d in sorted(rows) if rows[d]["registration_status"] == selected)
    with (OUTDIR / "all_checked.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLS)
        writer.writeheader()
        writer.writerows(rows[d] for d in sorted(rows))
    counts = {key: sum(row["registration_status"] == key for row in rows.values()) for _, key in sets}
    (OUTDIR / "README.txt").write_text(
        "Live Verisign RDAP .com registration check, UTC check timestamps per domain.\n"
        f"Total: {len(rows)}; unregistered in RDAP: {counts['unregistered_rdap']}; registered: {counts['registered']}; inconclusive: {counts['unknown']}\n"
        "An RDAP HTTP 404 indicates no current registration record. It does NOT guarantee a domain can be purchased: reserved, premium, blocked or trademark-restricted names still require registrar confirmation.\n"
        "Unknown includes timeouts and rate limiting; NEVER treat unknown as available.\n",
        encoding="utf-8",
    )
    print(counts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard", type=int)
    parser.add_argument("--shards", type=int, default=16)
    parser.add_argument("--out", type=pathlib.Path)
    parser.add_argument("--merge", type=pathlib.Path)
    args = parser.parse_args()
    if args.merge:
        merge(args.merge)
    else:
        if args.shard is None or args.out is None or not 0 <= args.shard < args.shards:
            parser.error("Valid --shard, --shards and --out required")
        run_shard(args.shard, args.shards, args.out)
