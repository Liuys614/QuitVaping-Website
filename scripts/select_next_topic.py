#!/usr/bin/env python3
"""
Hybrid Keyword Discovery Selector for Quit Vaping Programmatic SEO.
1. Checks Google Search Console (via REST API / gcloud ADC / gum) for Strike Zone queries:
   Position 15..55, sorted by Impressions DESC, excluding already-published topics.
2. Falls back to the next pending high-intent topic in `guides/topic_queue.json` during cold start.
"""
import json
import os
import shutil
import subprocess
from datetime import datetime, timedelta

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUIDES_DIR = os.path.join(ROOT_DIR, "guides")
QUEUE_PATH = os.path.join(GUIDES_DIR, "topic_queue.json")
MANIFEST_PATH = os.path.join(GUIDES_DIR, "published_manifest.json")
CONFIG_PATH = os.path.join(GUIDES_DIR, "seo_config.json")


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def try_gsc_strike_zone(cfg: dict, published_keywords: set):
    end_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    site_prop = cfg.get("gsc_property", "https://liuys614.github.io/QuitVaping-Website/")
    last_reason = "GSC not queried"

    # 1. Try Direct GSC REST API with gcloud ADC
    try:
        token_proc = subprocess.run(
            ["gcloud", "auth", "application-default", "print-access-token"],
            capture_output=True, text=True, timeout=10
        )
        if token_proc.returncode == 0 and token_proc.stdout.strip():
            token = token_proc.stdout.strip().splitlines()[-1]
            import urllib.request
            import urllib.parse
            import urllib.error
            encoded_site = urllib.parse.quote(site_prop, safe="")
            url = f"https://searchconsole.googleapis.com/webmasters/v3/sites/{encoded_site}/searchAnalytics/query"
            payload = json.dumps({
                "startDate": start_date,
                "endDate": end_date,
                "dimensions": ["query"],
                "rowLimit": 100
            }).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-Goog-User-Project": "kahoot-lite-2608"
            })
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    rows = data.get("rows", [])
                    candidates = []
                    for r in rows:
                        q = r.get("keys", [""])[0].strip().lower()
                        pos = float(r.get("position", 0))
                        impr = int(r.get("impressions", 0))
                        clicks = int(r.get("clicks", 0))
                        if 15.0 <= pos <= 55.0 and impr >= 10 and q not in published_keywords:
                            candidates.append((impr, pos, clicks, q))
                    if candidates:
                        candidates.sort(key=lambda x: x[0], reverse=True)
                        best = candidates[0]
                        slug = best[3].replace(" ", "-")[:55]
                        return {
                            "source": "gsc_strike_zone",
                            "slug": slug,
                            "target_keyword": best[3],
                            "gsc_impressions": best[0],
                            "gsc_position": round(best[1], 1),
                            "gsc_clicks": best[2],
                            "category": "Search Console · Guide",
                            "campaign_prefix": f"seo_{slug[:24].replace('-', '_')}",
                            "pitch_screen": "04-milestones.webp",
                            "pitch_headline": "Track your vape-free recovery privately on iPhone",
                            "pitch_body": "100% local-first tracking for vape-free days, dopamine milestones, 3-minute urge surfing, and pod savings."
                        }, None
                    last_reason = f"GSC returned {len(rows)} queries, but none matched Strike Zone criteria (pos 15..55, impr >= 10)."
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="replace")
                try:
                    err_json = json.loads(err_body)
                    msg = err_json.get("error", {}).get("message", err_body)
                except Exception:
                    msg = err_body
                last_reason = f"GSC HTTP {e.code}: {msg}"
    except Exception as e:
        last_reason = f"GSC query exception: {str(e)}"

    return None, last_reason


def main():
    cfg = load_json(CONFIG_PATH, {})
    manifest = load_json(MANIFEST_PATH, [])
    queue = load_json(QUEUE_PATH, [])

    published_slugs = {m["slug"] for m in manifest}
    published_keywords = {m.get("target_keyword", "").lower() for m in manifest}

    gsc_topic, gsc_reason = try_gsc_strike_zone(cfg, published_keywords)
    if gsc_topic and gsc_topic["slug"] not in published_slugs:
        print(json.dumps(gsc_topic, indent=2))
        return

    for item in queue:
        if item["slug"] not in published_slugs and item.get("status") != "published":
            out = dict(item)
            out["source"] = "seed_topic_queue"
            out["fallback_reason"] = gsc_reason
            print(json.dumps(out, indent=2))
            return

    print(json.dumps({"source": "exhausted", "message": "All queued seed topics published; generate a new high-intent quit vaping topic."}, indent=2))


if __name__ == "__main__":
    main()
