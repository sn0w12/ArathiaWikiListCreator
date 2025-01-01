from src.api import WikiAPI
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from functools import partial


class CategoryMap:
    def __init__(
        self,
        categories: Dict[str, Dict[str, Optional[List[str]]]],
        category_titles: Dict[str, str] = None,
    ):
        self.categories = categories
        self.category_titles = category_titles or {}

    def get_mapped_category(
        self, category: str
    ) -> Tuple[str, Optional[str], Optional[str]]:
        """Returns (parent_category, subcategory, title) tuple. If no mapping exists, returns (category, None, title)"""
        for parent_category, sub_data in self.categories.items():
            for subcategory in sub_data.get("subcategories", []):
                if category == subcategory:
                    return parent_category, category, self.category_titles.get(category)
        return category, None, self.category_titles.get(category)

    def get_all_categories(self) -> Dict[str, Optional[List[str]]]:
        """Returns all categories that should exist in the output"""
        result = {}
        for category, data in self.categories.items():
            result[category] = data.get("subcategories", None)
        return result

    def get_category_title(self, category: str) -> str:
        """Returns the display title for a category, or the category itself if no title is set"""
        return self.category_titles.get(category, category)

    def get_max_subcategories(self) -> int:
        """Returns the maximum number of subcategories for any parent category"""
        if not self.categories:
            return 0
        return max(len(data.get("subcategories", [])) for data in self.categories.values())

    def get_max_category_depth(self) -> int:
        """Returns the maximum depth of nested subcategories"""
        if not self.categories:
            return 0

        def get_depth(category: str, visited: set) -> int:
            if category in visited:  # Prevent cycles
                return 0
            visited.add(category)

            if category not in self.categories or not self.categories[category].get("subcategories"):
                return 1

            subcategory_depths = [
                get_depth(sub, visited.copy())
                for sub in self.categories[category]["subcategories"]
            ]
            return 1 + max(subcategory_depths, default=0)

        depths = [get_depth(cat, set()) for cat in self.categories]
        return max(depths, default=0)

    def __str__(self) -> str:
        """Returns a JSON-like string representation of the category map structure"""
        # Build combined structure
        structure = {}
        for cat, data in self.categories.items():
            title = self.category_titles.get(cat, cat)
            subcats = {
                sub: self.category_titles.get(sub, sub)
                for sub in data.get("subcategories", [])
            }
            structure[cat] = {"title": title, "subcategories": subcats}

        # Format the dictionary as a string with proper indentation
        lines = ["{"]
        entries = []

        for category, data in structure.items():
            category_lines = [f'    "{category}": {{']
            category_lines.append(f'        "title": "{data["title"]}",')

            sub_items = [
                f'            "{sub}": "{title}"'
                for sub, title in data["subcategories"].items()
            ]
            if sub_items:
                category_lines.append('        "subcategories": {')
                category_lines.append(",\n".join(sub_items))
                category_lines.append("        }")

            category_lines.append("    }")
            entries.append("\n".join(category_lines))

        lines.append(",\n".join(entries))
        lines.append("}")

        return "\n".join(lines)


class WikiTemplate:
    def __init__(self, title, category_map: CategoryMap):
        self.title = title
        self.wiki_api = WikiAPI()
        self.rows = []
        self.categories: Dict[str, Dict[str, List[str]] | List[str]] = {}
        self.category_map = category_map

        # Initialize all categories from the map
        for category, subcategories in self.category_map.get_all_categories().items():
            if subcategories is not None:
                self.categories[category] = {sub: [] for sub in subcategories}
            else:
                self.categories[category] = []

    def _get_mapped_category(self, category: str) -> tuple[str, str, str]:
        return self.category_map.get_mapped_category(category)

    def _add_to_categories(self, category: str, subcategory: str | None, member: str):
        if subcategory:
            # Handle mapped category with subcategory
            if category not in self.categories:
                self.categories[category] = {}
            if subcategory not in self.categories[category]:
                self.categories[category][subcategory] = []
            if member not in self.categories[category][subcategory]:
                self.categories[category][subcategory].append(member)
        else:
            # Handle unmapped category
            if category not in self.categories:
                self.categories[category] = []
            if member not in self.categories[category]:
                self.categories[category].append(member)

    def _process_member_categories(self, member: str, base_category: str):
        categories = self.wiki_api.get_page_categories(member)
        result = []
        for category in categories:
            if category != base_category:
                result.append((category, member))
        return result

    def fetch_category(self, category_name: str):
        members, subcategories = self.wiki_api.get_category_members(category_name)
        unCategorized = set(members)

        # Process categories in parallel
        with ThreadPoolExecutor(max_workers=10) as executor:
            process_func = partial(
                self._process_member_categories, base_category=category_name
            )
            results = list(executor.map(process_func, members))

        # Aggregate results
        for member_results in results:
            for category, member in member_results:
                parent_category, subcategory, display_title = self._get_mapped_category(
                    category
                )
                self._add_to_categories(parent_category, subcategory, member)
                unCategorized.discard(member)

        if unCategorized:
            print("Uncategorized members:")
            for member in sorted(unCategorized):
                print(f"https://www.arathia.net/wiki/{member}")

    def generate_header(self):
        return f"""{{| class="mw-collapsible mw-collapsed wikitable custom-button" style="width:100%;"
! colspan="{self.category_map.get_max_category_depth() + 1}" style="text-align:center; font-weight: bold; position: relative;" | {self.title}
|-"""

    def generate_parent_category(self, category: str, member_count: int):
        title = self.category_map.get_category_title(category)
        return f"""|rowspan="{member_count}" class="custom-rowspan"|{title}"""

    def _generate_row(self, title: str, members: list, colspan="", i=1):
        display_title = self.category_map.get_category_title(title)
        row_class = 'class="custom-row"|' if i == 0 else ""
        wrapped_members = [f"[[{member}]]" for member in members]
        return f"|{row_class}{display_title}\n|{colspan}{row_class}{self.generate_member_separator().join(wrapped_members)}"

    def generate_subclass_row(self, title: str, members: list, i: int):
        return self._generate_row(title, members, "", i)

    def generate_row(self, title: str, members: list):
        return self._generate_row(title, members, 'colspan="2"|')

    def generate_row_separator(self):
        return "|-"

    def generate_member_separator(self):
        return r"{{ts}}"

    def generate_footer(self):
        return "|}"
