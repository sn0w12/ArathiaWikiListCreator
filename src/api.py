import requests
from typing import List


class WikiAPI:
    def __init__(self, logging=False):
        self.base_url = "https://www.arathia.net/w/api.php"
        self.ignore_categories = ["Pages with broken file links"]
        self.logging = logging

    def get_category_members(self, category: str) -> tuple[List[str], List[str]]:
        if self.logging:
            print(f"Fetching members of category: {category}")

        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "format": "json",
            "cmlimit": "500",
        }

        response = requests.get(self.base_url, params=params)
        data = response.json()

        members = []
        subcategories = []

        for page in data["query"]["categorymembers"]:
            if page["title"] in self.ignore_categories:
                continue
            if page["title"].startswith("Category:"):
                subcategories.append(page["title"].replace("Category:", ""))
            else:
                members.append(page["title"])

        return members, subcategories

    def get_page_categories(self, page_title: str) -> List[str]:
        if self.logging:
            print(f"Fetching categories for page: {page_title}")

        params = {
            "action": "query",
            "titles": page_title,
            "prop": "categories",
            "format": "json",
        }

        response = requests.get(self.base_url, params=params)
        data = response.json()

        pages = data["query"]["pages"]
        page = next(iter(pages.values()))

        if "categories" not in page:
            return []

        return [
            cat["title"].replace("Category:", "")
            for cat in page["categories"]
            if cat["title"].replace("Category:", "") not in self.ignore_categories
        ]
