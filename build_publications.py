#!/usr/bin/env python3
"""Generate cv/publications.tex from the website's publications.json.

The website (publications.json) is the single source of truth. This script
writes the CV's publication lists in the same order the site shows them:
newest year first, and within a year the order of the JSON file.

Usage:  python cv/build_publications.py [path/to/publications.json] [path/to/publications.tex]

Optional per-entry fields the website ignores but this script uses:
  "me": 1        index (0-based) of your name in "authors", for entries where
                 the name is ambiguous (e.g. two "Y. Wang" authors)
  "cv_award": "" overrides "award" in the CV only (e.g. a longer label)
  "cv_skip": 1   leaves the entry out of the CV
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / "publications.json"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "publications.tex"

FULL_NAME = "Yue Wang"          # always you
SHORT_NAME = "Y. Wang"          # you only if it is the sole "Y. Wang" on the paper
SECTIONS = [("Conference", "Conference"), ("Journal", "Journal"), ("Preprint", "Preprint")]

_ESC = {"&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
        "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
        "\\": r"\textbackslash{}"}


def tex(s: str) -> str:
    return "".join(_ESC.get(c, c) for c in s)


def year(p) -> int:
    m = re.search(r"20\d{2}", p.get("venue", ""))
    return int(m.group()) if m else 0


def find_me(p, warnings):
    """Return the index of the PI in the author list, or None."""
    if isinstance(p.get("me"), int):
        return p["me"]
    names = [a.replace("*", "").strip() for a in p["authors"]]
    if FULL_NAME in names:
        return names.index(FULL_NAME)
    short = [i for i, n in enumerate(names) if n == SHORT_NAME]
    if len(short) == 1:
        return short[0]
    if len(short) > 1:
        warnings.append(f'ambiguous author "{SHORT_NAME}" in "{p["title"]}"; add "me": <index> to its JSON entry')
    else:
        warnings.append(f'your name not found in "{p["title"]}"')
    return None


def authors_tex(p, warnings):
    me = find_me(p, warnings)
    out = []
    for i, a in enumerate(p["authors"]):
        a = tex(a.strip())
        out.append(rf"\myname{{{a}}}" if i == me else a)
    if len(out) <= 2:
        return " and ".join(out)
    return ", ".join(out[:-1]) + ", and " + out[-1]


def entry_tex(p, warnings):
    award = p.get("cv_award", p.get("award", "")).strip()
    parts = [authors_tex(p, warnings) + ".", tex(p["title"].strip()) + ".",
             r"\textit{" + tex(p["venue"].strip()) + "}."]
    if award:
        parts.append(r"(\textbf{" + tex(award[0].upper() + award[1:]) + "})")
    pdf = (p.get("links") or {}).get("pdf", "")
    if pdf and pdf != "#":
        parts.append(r"\href{" + pdf.replace("%", r"\%").replace("#", r"\#") + "}{[PDF]}")
    return "  \\item " + " ".join(parts)


def main():
    pubs = json.loads(SRC.read_text(encoding="utf-8"))["publications"]
    pubs = [p for p in pubs if not p.get("cv_skip")]
    pubs = sorted(pubs, key=year, reverse=True)           # stable, like the website
    warnings, lines = [], [
        "% AUTO-GENERATED from publications.json by cv/build_publications.py.",
        "% Do not edit by hand: edit publications.json on the website instead.",
    ]
    counts = {}
    for topic, heading in SECTIONS:
        items = [p for p in pubs if p.get("topic") == topic]
        counts[topic] = len(items)
        if not items:
            continue
        lines += ["", rf"\textbf{{{heading}}}", r"\begin{enumerate}[leftmargin=*,itemsep=1pt]"]
        lines += [entry_tex(p, warnings) for p in items]
        lines.append(r"\end{enumerate}")
    unknown = [p["title"] for p in pubs if p.get("topic") not in dict(SECTIONS)]
    for t in unknown:
        warnings.append(f'unknown "topic" for "{t}"; it was left out')
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT}: " + ", ".join(f"{k} {v}" for k, v in counts.items()))
    for w in warnings:
        print("WARNING:", w)


if __name__ == "__main__":
    main()
