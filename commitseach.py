import requests
import time

KEYWORDS = ["cagent", "refactor", "update", "optimize"]
query = "(" + " OR ".join(KEYWORDS) + ") in:message"

search_url = "https://api.github.com/search/commits"

headers = {
    "Accept": "application/vnd.github.cloak-preview"
}

params = {
    "q": query,
    "per_page": 1000,
    "page": 1
}

output_file = "yaml_commit_results.txt"

with open(output_file, "w", encoding="utf-8") as f:

    search_resp = requests.get(search_url, headers=headers, params=params)
    search_data = search_resp.json()

    for item in search_data.get("items", []):

        commit_url = item["url"]
        commit_resp = requests.get(commit_url)
        commit_data = commit_resp.json()

        files = commit_data.get("files", [])

        yaml_files = [
            file["filename"]
            for file in files
            if file["filename"].endswith((".yaml", ".yml"))
        ]

        if yaml_files:

            message = commit_data["commit"]["message"]
            html_url = commit_data["html_url"]

            matches = sum(k in message.lower() for k in KEYWORDS)

            f.write(f"Matches: {matches}\n")
            f.write(f"Commit: {html_url}\n")
            f.write(f"YAML files: {', '.join(yaml_files)}\n")
            f.write(f"Message: {message}\n")
            f.write("-"*60 + "\n")

        time.sleep(0.5)