import os
import requests
from dotenv import load_dotenv
from langchain_core.documents import Document


load_dotenv()

github_token = os.getenv("GITHUB_TOKEN")

def fetch_github(owner, repo, endpoint):
    url = f"https://api.github.com/repos/{owner}/{repo}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {github_token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        data = response.json()
        print("Error fetching data from GitHub", response.status_code, data)
        return []


def load_issues(issues):
    docs = []
    print("Issues:", issues)
    for entry in issues:
        print("Entry:", entry)
        metadata = {
            "author": entry["user"]["login"],
            "comments": entry["comments"],
            "body": entry["body"],
            "labels": entry["labels"],
            "created_at": entry["created_at"]
        }
        data = entry["title"]
        if entry["body"]:
            data += entry["body"]
        doc = Document(page_content=data, metadata=metadata)
        docs.append(doc)
    return docs

def fetch_github_issues(owner, repo):
    endpoint = "issues"
    issues = fetch_github(owner, repo, endpoint)
    return load_issues(issues)
owner="techwithtim"
repo="Flask-Web-App-Tutorial"
endpoint="issues"
print(fetch_github(owner, repo, endpoint))