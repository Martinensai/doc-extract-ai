"""collect.py
Download PDF documents from target websites and save them to data/raw/.
This is a starter template—adapt selectors, URL sources, and politeness rules.
"""
import requests
from pathlib import Path
from bs4 import BeautifulSoup

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

def download_file(url, dest):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    with open(dest, "wb") as f:
        f.write(r.content)

def find_documents_from_index(index_url):
    # TODO: parse the government site(s) and yield PDF urls
    resp = requests.get(index_url)
    soup = BeautifulSoup(resp.text, "html.parser")
    for a in soup.select("a"):
        href = a.get("href", "")
        if href.lower().endswith(".pdf"):
            yield href

def main():
    index_url = "https://example.gov.bj/decrets"  # replace
    for pdf_url in find_documents_from_index(index_url):
        dest = RAW_DIR / Path(pdf_url).name
        print(f"Downloading {pdf_url} -> {dest}")
        # download_file(pdf_url, dest)  # uncomment when configured

if __name__ == '__main__':
    main()
