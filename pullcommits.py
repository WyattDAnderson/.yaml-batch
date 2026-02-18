import os
import requests
import time
import base64
from pathlib import Path

SEARCH_TERM = "cagent"
PER_PAGE = 50
MAX_PAGES = 5

TOKEN = os.getenv("GITHUB_TOKEN")
if not TOKEN:
    raise ValueError("Set GITHUB_TOKEN environment variable")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github.cloak-preview+json"
}

BASE_SEARCH_URL = "https://api.github.com/search/commits"

OUTPUT_DIR = Path("downloaded_yaml")
OUTPUT_DIR.mkdir(exist_ok=True)

def search_commits():
    commits = []

    for page in range(1, MAX_PAGES + 1):
        print(f"Searching page {page}")
        params = {
            "q": SEARCH_TERM,
            "per_page": PER_PAGE,
            "page": page
        }

        r = requests.get(BASE_SEARCH_URL, headers=HEADERS, params=params)

        if r.status_code != 200:
            print("Search error:", r.text)
            break

        data = r.json()
        items = data.get("items", [])
        if not items:
            break

        commits.extend(items)

    return commits

def fetch_commit_files(commit):
    url = commit["url"]  # API URL for commit
    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        return []

    data = r.json()
    return data.get("files", [])

def download_yaml_file(file_info, repo_full_name, sha):
    raw_url = file_info.get("raw_url")
    filename = file_info.get("filename")

    if not raw_url:
        return

    r = requests.get(raw_url)

    if r.status_code != 200:
        return

    # Create structured path:
    # downloaded_yaml/{repo}/{sha}/path/to/file.yaml
    save_path = OUTPUT_DIR / repo_full_name / sha / filename
    save_path.parent.mkdir(parents=True, exist_ok=True)

    with open(save_path, "wb") as f:
        f.write(r.content)

    print(f"Saved {save_path}")

def main():
    commits = search_commits()

    for commit in commits:
        repo_name = commit["repository"]["full_name"]
        sha = commit["sha"]

        print(f"\nChecking commit {repo_name}@{sha}")

        files = fetch_commit_files(commit)

        for file_info in files:
            filename = file_info.get("filename", "").lower()

            if filename.endswith(".yaml") or filename.endswith(".yml"):
                download_yaml_file(file_info, repo_name, sha)

        time.sleep(0.5)  # be nice to API

if __name__ == "__main__":
    main()
