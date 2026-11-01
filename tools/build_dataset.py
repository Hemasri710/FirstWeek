"""Download the FastAPI files listed below, count pages, and write DATASET.md.

Page rule: code = 1 page per 50 lines, docs = 1 page per 500 words.
Run from the repo root:  python tools/build_dataset.py
"""
import datetime
import html
import math
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "sample"
OUT.mkdir(parents=True, exist_ok=True)

GH = "https://github.com/fastapi/fastapi/blob/master/"
CODE = [
    "README.md",
    "fastapi/__init__.py",
    "fastapi/applications.py",
    "fastapi/routing.py",
    "fastapi/params.py",
    "fastapi/param_functions.py",
    "fastapi/dependencies/utils.py",
    "fastapi/dependencies/models.py",
    "fastapi/exceptions.py",
    "fastapi/exception_handlers.py",
    "fastapi/encoders.py",
    "fastapi/utils.py",
    "fastapi/openapi/utils.py",
    "fastapi/responses.py",
    "fastapi/background.py",
    "fastapi/concurrency.py",
    "fastapi/datastructures.py",
]
DOCS = [
    ("First Steps documentation", "https://fastapi.tiangolo.com/tutorial/first-steps/"),
    ("Path Parameters documentation", "https://fastapi.tiangolo.com/tutorial/path-params/"),
    ("Request Body documentation", "https://fastapi.tiangolo.com/tutorial/body/"),
]

today = datetime.date.today().strftime("%d %b %Y")
rows = []


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "firstweek-dataset"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


for path in CODE:
    src = GH + path
    raw = src.replace("https://github.com/", "https://raw.githubusercontent.com/").replace("/blob/", "/")
    try:
        text = get(raw)
    except Exception as e:
        print("FAILED", path, e)
        continue
    (OUT / path.replace("/", "__")).write_text(text, encoding="utf-8")
    pages = max(1, math.ceil(len(text.splitlines()) / 50))
    rows.append((f"`{path}`", src, pages))

for name, url in DOCS:
    try:
        page = get(url)
    except Exception as e:
        print("FAILED", name, e)
        continue
    page = re.sub(r"(?is)<(script|style).*?</\1>", " ", page)
    text = html.unescape(re.sub(r"<[^>]+>", " ", page))
    text = re.sub(r"\s+", " ", text).strip()
    fname = url.rstrip("/").split("/")[-1] + "_doc.txt"
    (OUT / fname).write_text(text, encoding="utf-8")
    pages = max(1, math.ceil(len(text.split()) / 500))
    rows.append((name, url, pages))

lines = [
    "# Dataset",
    "",
    "Source: https://github.com/fastapi/fastapi (MIT licence). Page rule: code = 1 page per 50 lines, docs = 1 page per 500 words.",
    "",
    "| File | Source URL | Pages | Licence / terms | Downloaded on |",
    "|------|------------|-------|-----------------|---------------|",
]
for name, src, pages in rows:
    lines.append(f"| {name} | {src} | {pages} | MIT | {today} |")
total = sum(r[2] for r in rows)
lines += ["", f"**Total: {len(rows)} files, {total} pages.** Samples are saved in `data/sample/`.", ""]

(ROOT / "DATASET.md").write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote DATASET.md: {len(rows)} files, {total} pages")