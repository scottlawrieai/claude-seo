#!/usr/bin/env python3
"""Turn the quick-check JSON files into a Markdown summary.

Usage: summarize.py <results-dir>   (prints Markdown to stdout)
"""
import json
import sys
from pathlib import Path

ORDER = ["Critical", "High", "Medium", "Low", "Info"]


def load(path):
    try:
        return json.loads(path.read_text())
    except Exception as exc:  # missing or non-JSON output
        return {"error": f"could not read {path.name}: {exc}"}


def cell(value):
    return str(value or "").replace("|", "\\|").replace("\n", " ")


def findings_table(title, data):
    out = [f"### {title}", ""]
    if data.get("error"):
        out += [f"Check failed: `{data['error']}`", ""]
        return out
    findings = data.get("findings") or []
    if not findings:
        return out + ["No findings.", ""]
    findings.sort(key=lambda f: ORDER.index(f.get("severity")) if f.get("severity") in ORDER else 99)
    out += ["| Severity | Check | Detail |", "|---|---|---|"]
    for f in findings:
        out.append(f"| {f.get('severity', '')} | `{f.get('id', '')}` | {cell(f.get('message'))} |")
    return out + [""]


def main():
    d = Path(sys.argv[1])
    lines = ["## SEO quick checks", ""]
    lines += findings_table("On-page (homepage)", load(d / "page.json"))
    lines += findings_table("TLS, security headers and redirects", load(d / "transport.json"))
    sm = load(d / "sitemap.json")
    lines += ["### Sitemaps", ""]
    if sm.get("error"):
        lines.append(f"Check failed: `{sm['error']}`")
    else:
        found = sm.get("found") or []
        lines.append(f"Sitemaps found: {len(found)}")
        for item in found:
            url = item.get("url") if isinstance(item, dict) else item
            lines.append(f"- {url}")
        for w in sm.get("warnings") or []:
            lines.append(f"- Warning: {w}")
    lines.append("")
    ag = load(d / "agentic.json")
    lines += ["### AI agent readiness", ""]
    if ag.get("error"):
        lines.append(f"Check failed: `{ag['error']}`")
    else:
        bad = [c for c in ag.get("checks") or [] if c.get("status") in ("fail", "warn")]
        if not bad:
            lines.append("All checks passed.")
        else:
            lines += ["| Priority | Status | Check | Fix |", "|---|---|---|---|"]
            for c in bad:
                lines.append(f"| {c.get('priority')} | {c.get('status')} | {cell(c.get('title'))} | {cell(c.get('fix'))} |")
    lines.append("")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
