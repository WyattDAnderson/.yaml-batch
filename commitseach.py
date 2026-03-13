import requests
import time
from datetime import datetime, timedelta

# --- CONFIG ---
KEYWORDS = ["cagent", "refactor", "update", "optimize"]
OUTPUT_FILE = "yaml_commit_results.txt"
START_DATE = "2025-01-01"   # inclusive
END_DATE   = "2025-03-01"   # exclusive
DATE_WINDOW_DAYS = 7        # split search into 7-day chunks
GITHUB_TOKEN = ""           # optional, increases rate limit

# Headers for commit search API
HEADERS = {
    "Accept": "application/vnd.github.cloak-preview",
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

# --- FUNCTIONS ---
def daterange(start, end, delta_days):
    current = start
    while current < end:
        next_date = min(current + timedelta(days=delta_days), end)
        yield current, next_date
        current = next_date

def build_query(keywords, start_date, end_date):
    kw_part = "(" + " OR ".join(keywords) + ")"
    date_part = f"committer-date:{start_date}..{end_date}"
    return f"{kw_part} in:message {date_part}"

# --- MAIN ---
start_dt = datetime.strptime(START_DATE, "%Y-%m-%d")
end_dt = datetime.strptime(END_DATE, "%Y-%m-%d")

with open(OUTPUT_FILE, "a", encoding="utf-8") as f:

    for window_start, window_end in daterange(start_dt, end_dt, DATE_WINDOW_DAYS):

        start_str = window_start.strftime("%Y-%m-%d")
        end_str   = window_end.strftime("%Y-%m-%d")
        query = build_query(KEYWORDS, start_str, end_str)

        print(f"\nSearching {start_str} → {end_str}")

        for page in range(1, 11):  # pages 1–10, 100 per page max
            params = {"q": query, "per_page": 100, "page": page}

            resp = requests.get("https://api.github.com/search/commits", headers=HEADERS, params=params)
            if resp.status_code != 200:
                print("Error:", resp.status_code, resp.text)
                break

            data = resp.json()
            items = data.get("items", [])

            if not items:
                break

            print(f" Page {page}, {len(items)} commits")

            for item in items:
                commit_url = item["url"]
                commit_resp = requests.get(commit_url, headers=HEADERS)
                commit_data = commit_resp.json()

                files = commit_data.get("files", [])
                yaml_files = [f["filename"] for f in files if f["filename"].endswith((".yaml", ".yml"))]

                if yaml_files:
                    html_url = commit_data["html_url"]
                    f.write(f"{html_url}\n")
                    f.flush()
                    print(" Saved:", html_url)

                time.sleep(0.2)  # avoid hitting rate limit

            time.sleep(1)