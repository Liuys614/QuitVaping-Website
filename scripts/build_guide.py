#!/usr/bin/env python3
"""
Static Programmatic SEO Guide Builder for Quit Vaping Website.
Compiles JSON guide definitions in guides/posts/*.json into:
  1. guides/<slug>.html (with JSON-LD Article + FAQPage + ASC Campaign Links)
  2. guides/index.html (Guides Hub page)
  3. index.html (#home-guides-list preview cards)
  4. sitemap.xml (with lastmod dates)
  5. guides/published_manifest.json
"""
import json
import glob
import os
import re
from datetime import datetime
import html

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUIDES_DIR = os.path.join(ROOT_DIR, "guides")
POSTS_DIR = os.path.join(GUIDES_DIR, "posts")
CONFIG_PATH = os.path.join(GUIDES_DIR, "seo_config.json")


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def make_asc_url(app_id: str, pt: str, ct: str) -> str:
    clean_ct = re.sub(r"[^a-zA-Z0-9_-]", "_", ct)[:40]
    return f"https://apps.apple.com/app/apple-store/id{app_id}?pt={pt}&ct={clean_ct}&mt=8"


def render_guide_html(post: dict, cfg: dict, all_posts: list) -> str:
    site_url = cfg["site_url"].rstrip("/")
    app_id = cfg["app_id"]
    pt = cfg["provider_token"]
    slug = post["slug"]
    canonical_url = f"{site_url}/guides/{slug}.html"
    prefix = post.get("campaign_prefix", f"seo_{slug[:24]}")

    url_nav = make_asc_url(app_id, pt, f"{prefix}_nav")
    url_footer = make_asc_url(app_id, pt, f"{prefix}_foot")

    faqs = post.get("faqs", [])
    faq_schema_entities = [
        {
            "@type": "Question",
            "name": item["question"],
            "acceptedAnswer": {
                "@type": "Answer",
                "text": item["answer"]
            }
        }
        for item in faqs
    ]

    schema_graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Article",
                "headline": post["title"],
                "description": post["meta_description"],
                "datePublished": post["published_date"],
                "dateModified": post["published_date"],
                "mainEntityOfPage": canonical_url,
                "image": f"{site_url}/assets/appstore/{post.get('pitch_screen', '04-milestones.webp')}",
                "author": {
                    "@type": "Organization",
                    "name": "Quit Vaping Editorial"
                },
                "publisher": {
                    "@type": "Organization",
                    "name": "Quit Vaping",
                    "logo": {
                        "@type": "ImageObject",
                        "url": f"{site_url}/assets/app-icon.png"
                    }
                }
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{site_url}/"},
                    {"@type": "ListItem", "position": 2, "name": "Guides", "item": f"{site_url}/guides/index.html"},
                    {"@type": "ListItem", "position": 3, "name": post["title"], "item": canonical_url}
                ]
            }
        ]
    }
    if faq_schema_entities:
        schema_graph["@graph"].append({
            "@type": "FAQPage",
            "mainEntity": faq_schema_entities
        })

    faq_html_items = []
    for item in faqs:
        q = html.escape(item["question"])
        a = html.escape(item["answer"])
        faq_html_items.append(f"""
              <details open>
                <summary>{q}</summary>
                <p>{a}</p>
              </details>""")
    faq_section_html = ""
    if faq_html_items:
        faq_section_html = f"""
            <div class="support-card faq" style="margin-top: 42px;">
              <p class="eyebrow">Frequently Asked Questions</p>
              <h2>Common questions about {html.escape(post.get('target_keyword', 'nicotine cessation'))}</h2>
              {''.join(faq_html_items)}
            </div>"""

    # Related guides
    related = [p for p in all_posts if p["slug"] != slug][:3]
    related_links_html = ""
    if related:
        items = "".join(
            f'<li><a href="{p["slug"]}.html">{html.escape(p["title"])}</a></li>'
            for p in related
        )
        related_links_html = f"""
            <div class="sidebar-card">
              <p class="eyebrow">Related Guides</p>
              <h3>Keep reading</h3>
              <ul style="padding-left: 18px; margin: 0; font-size: 0.9rem;">{items}</ul>
            </div>"""

    # Generate Table of Contents from h2 tags and inject anchor IDs
    headings = []

    def inject_h2(match):
        raw_text = match.group(1)
        plain_text = re.sub(r"<[^>]+>", "", raw_text).strip()
        slug_id = re.sub(r"[^a-z0-9]+", "-", plain_text.lower()).strip("-")
        headings.append((slug_id, plain_text))
        return f'<h2 id="{slug_id}">{raw_text}</h2>'

    rendered_body = re.sub(r"<h2>(.*?)</h2>", inject_h2, post["body_html"])

    toc_html = ""
    if headings:
        toc_items = "".join(
            f'<li><a href="#{hid}">{html.escape(htext)}</a></li>'
            for hid, htext in headings
        )
        toc_html = f"""
            <div class="sidebar-card toc-card">
              <p class="eyebrow">On This Page</p>
              <h3>Table of Contents</h3>
              <ul class="toc-list">
                {toc_items}
              </ul>
            </div>"""

    pitch_screen = post.get("pitch_screen", "04-milestones.webp")
    pitch_headline = html.escape(post.get("pitch_headline", "Track your vape-free progress privately"))
    pitch_body = html.escape(post.get("pitch_body", "100% local-first on your iPhone. Zero accounts, zero cloud tracking."))

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="referrer" content="origin-when-cross-origin">
    <meta name="apple-itunes-app" content="app-id={app_id}, affiliate-data=pt={pt}&ct=web_smart_banner, app-argument={canonical_url}">
    <meta name="description" content="{html.escape(post['meta_description'])}">
    <meta name="theme-color" content="#F4F7FA">
    <link rel="canonical" href="{canonical_url}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{canonical_url}">
    <meta property="og:title" content="{html.escape(post['title'])} — Quit Vaping">
    <meta property="og:description" content="{html.escape(post['meta_description'])}">
    <meta property="og:image" content="{site_url}/assets/appstore/{pitch_screen}">
    <title>{html.escape(post['title'])} | Quit Vaping Guides</title>
    <link rel="icon" href="../assets/app-icon.png">
    <link rel="apple-touch-icon" href="../assets/app-icon.png">
    <link rel="stylesheet" href="../styles.css">
    <script type="application/ld+json">
{json.dumps(schema_graph, indent=2)}
    </script>
  </head>
  <body class="guide-page">
    <header class="site-header">
      <nav class="nav container" aria-label="Primary navigation">
        <a class="brand" href="../index.html" aria-label="Quit Vaping home">
          <img src="../assets/app-icon.png" alt="" width="39" height="39">
          <span>Quit Vaping</span>
        </a>
        <div class="nav-links">
          <a href="../index.html#features">Features</a>
          <a href="../index.html#gallery">Screens</a>
          <a href="index.html">Guides</a>
          <a href="../index.html#support">Support</a>
          <a class="nav-download" data-campaign="{prefix}_nav" href="{html.escape(url_nav)}" target="_blank" rel="noopener">Download</a>
        </div>
      </nav>
    </header>

    <main>
      <section class="guide-hero">
        <div class="container">
          <div class="guide-breadcrumb">
            <a href="../index.html">Home</a> &rsaquo; <a href="index.html">Guides</a> &rsaquo; <span>{html.escape(post.get('category', 'Guide'))}</span>
          </div>
          <span class="guide-tag">{html.escape(post.get('category', 'Evidence-Based Guide'))}</span>
          <h1>{html.escape(post['title'])}</h1>
          <div class="guide-meta">
            <span>Published {html.escape(post['published_date'])}</span>
            <span>&middot;</span>
            <span>{html.escape(post.get('reading_time', '5 min read'))}</span>
            <span>&middot;</span>
            <span>100% Private Nicotine Cessation Series</span>
          </div>
        </div>
      </section>

      <div class="container guide-layout">
        <div>
          <article class="guide-article">
            {rendered_body}
          </article>
          {faq_section_html}
        </div>

        <aside class="guide-sidebar" aria-label="Table of contents and related guides">
          {toc_html}
          {related_links_html}
        </aside>
      </div>

      <section class="cta-section">
        <div class="container">
          <div class="cta-card">
            <div>
              <p class="eyebrow">100% Private on iPhone &amp; iPad</p>
              <h2>Track your vape-free days without judgment.</h2>
              <p>Follow your real-time lung and dopamine recovery, surf cravings in 3 minutes, and watch your bank account grow.</p>
            </div>
            <a class="button button-light app-store-button" data-campaign="{prefix}_foot" href="{html.escape(url_footer)}" target="_blank" rel="noopener" aria-label="Download Quit Vaping on the App Store">
              <span class="store-kicker">Download on the</span>
              <span class="store-name">App Store</span>
            </a>
          </div>
        </div>
      </section>
    </main>

    <footer class="site-footer">
      <div class="container footer-content">
        <div class="footer-brand">
          <a class="brand" href="../index.html"><img src="../assets/app-icon.png" alt="" width="32" height="32"><span>Quit Vaping</span></a>
          <p class="footer-copy">A private, local-first tracker for vape-free days, dopamine reset, lung recovery, and mindful living.</p>
        </div>
        <div class="footer-links">
          <a href="index.html">Guides</a>
          <a href="../index.html#support">Support</a>
          <a href="../privacy.html">Privacy</a>
          <a href="../terms.html">Terms</a>
        </div>
        <p class="copyright">&copy; <span data-year>2026</span> Quit Vaping. Educational content only; not medical advice or a substitute for professional care.</p>
      </div>
    </footer>

    <script src="../script.js"></script>
  </body>
</html>
"""


def render_guides_index_html(posts: list, cfg: dict) -> str:
    site_url = cfg["site_url"].rstrip("/")
    app_id = cfg["app_id"]
    pt = cfg["provider_token"]
    canonical_url = f"{site_url}/guides/index.html"
    url_nav = make_asc_url(app_id, pt, "web_guides_nav")

    cards_html = []
    for p in posts:
        cards_html.append(f"""
            <article class="guide-card">
              <span class="guide-tag">{html.escape(p.get('category', 'Guide'))}</span>
              <h3><a href="{p['slug']}.html">{html.escape(p['title'])}</a></h3>
              <p>{html.escape(p.get('summary_excerpt', p['meta_description']))}</p>
              <a class="guide-read-link" href="{p['slug']}.html">Read full guide ({html.escape(p.get('reading_time', '5 min'))}) &rarr;</a>
            </article>""")

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="referrer" content="origin-when-cross-origin">
    <meta name="apple-itunes-app" content="app-id={app_id}, affiliate-data=pt={pt}&ct=web_smart_banner, app-argument={canonical_url}">
    <meta name="description" content="Evidence-based guides on nicotine withdrawal timelines, 3-minute urge surfing for vape cravings, dopamine recovery, and kicking disposables.">
    <meta name="theme-color" content="#F4F7FA">
    <link rel="canonical" href="{canonical_url}">
    <title>Nicotine Cessation, Lung Healing &amp; Dopamine Reset Guides | Quit Vaping</title>
    <link rel="icon" href="../assets/app-icon.png">
    <link rel="apple-touch-icon" href="../assets/app-icon.png">
    <link rel="stylesheet" href="../styles.css">
  </head>
  <body class="guides-index-page">
    <header class="site-header">
      <nav class="nav container" aria-label="Primary navigation">
        <a class="brand" href="../index.html" aria-label="Quit Vaping home">
          <img src="../assets/app-icon.png" alt="" width="39" height="39">
          <span>Quit Vaping</span>
        </a>
        <div class="nav-links">
          <a href="../index.html#features">Features</a>
          <a href="../index.html#gallery">Screens</a>
          <a href="index.html" aria-current="page">Guides</a>
          <a href="../index.html#support">Support</a>
          <a class="nav-download" data-campaign="web_guides_nav" href="{html.escape(url_nav)}" target="_blank" rel="noopener">Download</a>
        </div>
      </nav>
    </header>

    <main>
      <section class="guide-hero">
        <div class="container">
          <p class="eyebrow">Evidence-Based Resource Library</p>
          <h1>Guides for quitting vaping &amp; nicotine recovery.</h1>
          <p class="hero-lede">Practical physiological timelines, neuroscience-backed craving protocols, and judgment-free strategies for quitting disposables and pods.</p>
        </div>
      </section>

      <section class="section" style="padding-top: 56px;">
        <div class="container">
          <div class="guides-preview-grid">
            {''.join(cards_html)}
          </div>
        </div>
      </section>
    </main>

    <footer class="site-footer">
      <div class="container footer-content">
        <div class="footer-brand">
          <a class="brand" href="../index.html"><img src="../assets/app-icon.png" alt="" width="32" height="32"><span>Quit Vaping</span></a>
          <p class="footer-copy">A private, local-first tracker for vape-free days, dopamine reset, lung recovery, and mindful living.</p>
        </div>
        <div class="footer-links">
          <a href="../index.html">Home</a>
          <a href="../index.html#support">Support</a>
          <a href="../privacy.html">Privacy</a>
          <a href="../terms.html">Terms</a>
        </div>
        <p class="copyright">&copy; <span data-year>2026</span> Quit Vaping. Not medical advice or a substitute for professional care.</p>
      </div>
    </footer>

    <script src="../script.js"></script>
  </body>
</html>
"""


def update_homepage_guides_preview(posts: list):
    index_path = os.path.join(ROOT_DIR, "index.html")
    if not os.path.exists(index_path):
        return
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    cards = []
    for p in posts[:3]:
        cards.append(f"""            <article class="guide-card">
              <span class="guide-tag">{html.escape(p.get('category', 'Guide'))}</span>
              <h3><a href="guides/{p['slug']}.html">{html.escape(p['title'])}</a></h3>
              <p>{html.escape(p.get('summary_excerpt', p['meta_description']))}</p>
              <a class="guide-read-link" href="guides/{p['slug']}.html">Read full guide &rarr;</a>
            </article>""")

    replacement = '<div class="guides-preview-grid" id="home-guides-list">\n' + "\n".join(cards) + "\n          </div>"
    pattern = r'<div class="guides-preview-grid" id="home-guides-list">.*?</div>'
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(new_content)


def update_sitemap(posts: list, cfg: dict):
    site_url = cfg["site_url"].rstrip("/")
    today = datetime.now().strftime("%Y-%m-%d")
    urls = [
        (f"{site_url}/", today),
        (f"{site_url}/guides/index.html", today),
        (f"{site_url}/support.html", "2026-10-21"),
        (f"{site_url}/privacy.html", "2026-10-21"),
        (f"{site_url}/terms.html", "2026-10-21"),
    ]
    for p in posts:
        urls.append((f"{site_url}/guides/{p['slug']}.html", p.get("published_date", today)))

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    for loc, lastmod in urls:
        xml_lines.append(f"  <url><loc>{loc}</loc><lastmod>{lastmod}</lastmod></url>")
    xml_lines.append("</urlset>\n")

    with open(os.path.join(ROOT_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(xml_lines))


def main():
    cfg = load_config()
    post_files = sorted(glob.glob(os.path.join(POSTS_DIR, "*.json")))
    posts = []
    for pf in post_files:
        with open(pf, "r", encoding="utf-8") as f:
            posts.append(json.load(f))

    # Sort newest first
    posts.sort(key=lambda x: x.get("published_date", ""), reverse=True)

    for post in posts:
        out_path = os.path.join(GUIDES_DIR, f"{post['slug']}.html")
        html_str = render_guide_html(post, cfg, posts)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_str)
        print(f"Built guide: guides/{post['slug']}.html")

    # Build guides/index.html
    index_html = render_guides_index_html(posts, cfg)
    with open(os.path.join(GUIDES_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)
    print("Built guides/index.html")

    # Update homepage preview & sitemap
    update_homepage_guides_preview(posts)
    update_sitemap(posts, cfg)

    # Save manifest
    manifest = [
        {
            "slug": p["slug"],
            "title": p["title"],
            "target_keyword": p.get("target_keyword", ""),
            "published_date": p.get("published_date", ""),
            "category": p.get("category", "")
        }
        for p in posts
    ]
    with open(os.path.join(GUIDES_DIR, "published_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Updated published_manifest.json ({len(manifest)} published guides)")


if __name__ == "__main__":
    main()
