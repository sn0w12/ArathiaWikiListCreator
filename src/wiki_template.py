from src.api import WikiAPI
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from functools import partial


class CategoryMap:
    def __init__(
        self,
        categories: Dict[str, Dict[str, any]],
        category_titles: Dict[str, str] = None,
    ):
        self.categories = self._normalize_categories(categories)
        self.category_titles = category_titles or {}

    def _normalize_categories(self, categories: Dict[str, Dict]) -> Dict[str, Dict]:
        """Converts simplified category structure to internal format with explicit subcategories"""

        def process_dict(d: Dict) -> Dict:
            result = {}
            if d:  # If the dictionary is not empty
                result["subcategories"] = {k: process_dict(v) for k, v in d.items()}
            return result

        return {k: process_dict(v) if v else {} for k, v in categories.items()}

    def get_mapped_category(
        self, category: str
    ) -> Tuple[str, Optional[str], Optional[str]]:
        """Returns (parent_category, subcategory, title) tuple. If no mapping exists, returns (category, None, title)"""

        def search_subcategories(parent: str, data: dict, path: List[str] = []):
            if "subcategories" not in data:
                return None
            for subcat, subdata in data["subcategories"].items():
                if category == subcat:
                    return (parent, subcat, self.category_titles.get(category))
                result = search_subcategories(parent, subdata, path + [subcat])
                if result:
                    return result
            return None

        for parent_category, data in self.categories.items():
            if category == parent_category:
                return parent_category, None, self.category_titles.get(category)
            result = search_subcategories(parent_category, data)
            if result:
                return result

        return category, None, self.category_titles.get(category)

    def get_all_categories(self) -> Dict[str, Optional[Dict]]:
        """Returns all categories that should exist in the output"""
        return self.categories

    def get_category_title(self, category: str) -> str:
        """Returns the display title for a category, or the category itself if no title is set"""
        return self.category_titles.get(category, category)

    def get_max_subcategories(self) -> int:
        """Returns the maximum number of subcategories for any parent category"""
        if not self.categories:
            return 0
        return max(
            len(data.get("subcategories", [])) for data in self.categories.values()
        )

    def get_max_category_depth(self) -> int:
        """Returns the maximum depth of nested subcategories"""
        if not self.categories:
            return 0

        def get_depth(data: dict) -> int:
            if "subcategories" not in data:
                return 1
            return 1 + max(
                (get_depth(subdata) for subdata in data["subcategories"].values()),
                default=0,
            )

        return max((get_depth(data) for data in self.categories.values()), default=0)

    def get_current_max_subcategories(self, data: dict) -> int:
        """
        Returns the 'row-splitting' count as described:
        1) A node with N subcategories contributes N if N>=2, else 0
        2) For each child that contributes > 0, add (child_contribution - 1)
        """

        def count_splits(node: dict) -> int:
            # Number of immediate subcategories
            n = len(node.get("subcategories", {}))
            # Contribution from this node
            contrib = n if n >= 2 else 0

            # Sum contributions from children
            child_sum = 0
            for subnode in node.get("subcategories", {}).values():
                child_contrib = count_splits(subnode)
                if child_contrib > 0:
                    child_sum += child_contrib - 1
            return contrib + child_sum

        return max(count_splits({"subcategories": data}), 1)

    def __str__(self) -> str:
        """Returns a JSON-like string representation of the category map structure"""

        def format_subcategories(data: dict, indent: int = 8) -> List[str]:
            lines = []
            if "subcategories" not in data:
                return lines

            lines.append(" " * indent + '"subcategories": {')
            subcats = []

            for subcat, subdata in data["subcategories"].items():
                subcat_lines = [f'{" " * (indent + 4)}"{subcat}": {{']
                title = self.category_titles.get(subcat, subcat)
                subcat_lines.append(f'{" " * (indent + 8)}"title": "{title}"')

                sub_lines = format_subcategories(subdata, indent + 8)
                if sub_lines:
                    subcat_lines.extend(sub_lines)

                subcat_lines.append(" " * (indent + 4) + "}")
                subcats.append("\n".join(subcat_lines))

            lines.extend([",\n".join(subcats)])
            lines.append(" " * indent + "}")
            return lines

        # Build the main structure
        lines = ["{"]
        entries = []

        for category, data in self.categories.items():
            category_lines = [f'    "{category}": {{']
            title = self.category_titles.get(category, category)
            category_lines.append(f'        "title": "{title}"')

            subcat_lines = format_subcategories(data)
            if subcat_lines:
                category_lines.extend(subcat_lines)

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
        self.categories = {}
        self.category_map = category_map

        def initialize_category_structure(data: dict) -> dict:
            if "subcategories" not in data:
                return {"members": []}
            return {
                "subcategories": {
                    subcat: initialize_category_structure(subdata)
                    for subcat, subdata in data["subcategories"].items()
                }
            }

        # Initialize all categories from the map
        for category, data in self.category_map.get_all_categories().items():
            self.categories[category] = initialize_category_structure(data)

    def _find_category_dict(
        self, category: str, subcategory: str | None = None
    ) -> dict:
        """Helper method to find the correct category dictionary in the nested structure"""
        if subcategory is None:
            return self.categories.setdefault(category, {"members": []})

        cat_dict = self.categories.setdefault(category, {"subcategories": {}})
        if "subcategories" not in cat_dict:
            cat_dict["subcategories"] = {}

        # Search through nested subcategories
        def find_subcategory(data: dict, target: str) -> dict:
            if "subcategories" in data:
                for subcat, subdata in data["subcategories"].items():
                    if subcat == target:
                        if "members" not in subdata:
                            subdata["members"] = []
                        return subdata
                    result = find_subcategory(subdata, target)
                    if result:
                        return result
            return None

        # First try to find the subcategory in the nested structure
        result = find_subcategory(cat_dict, subcategory)
        if result:
            return result

        # If not found in nested structure, create it at the top level
        if subcategory not in cat_dict["subcategories"]:
            cat_dict["subcategories"][subcategory] = {"members": []}
        return cat_dict["subcategories"][subcategory]

    def _add_to_categories(self, category: str, subcategory: str | None, member: str):
        target_dict = self._find_category_dict(category, subcategory)
        if member not in target_dict["members"]:
            target_dict["members"].append(member)

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
                parent_category, subcategory, display_title = (
                    self.category_map.get_mapped_category(category)
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

    def _generate_row(self, title: str, members: list, i=1, depth: int = 0):
        display_title = self.category_map.get_category_title(title)
        row_class = 'class="custom-row"|' if i == 0 and depth != 0 else ""
        wrapped_members = [f"[[{member}]]" for member in members]

        max_depth = self.category_map.get_max_category_depth()
        colspan = (
            f'colspan="{max_depth - depth} "'
            if row_class
            else f'colspan="{max_depth - depth}"|'
        )

        return f"|{row_class}{display_title}\n|{colspan}{row_class}{self.generate_member_separator().join(wrapped_members)}"

    def generate_subclass_row(self, title: str, members: list, i: int, depth: int = 0):
        return self._generate_row(title, members, i, depth)

    def generate_row(self, title: str, members: list, depth: int = 0):
        return self._generate_row(title, members, 0, depth)

    def generate_row_separator(self):
        return "|-"

    def generate_member_separator(self):
        return r"{{ts}}"

    def generate_footer(self):
        return "|}"

    def build(self) -> str:
        output = []
        output.append(self.generate_header())

        def process_category(category: str, data: dict, depth: int = 0):
            if "subcategories" in data:
                depth += 1
                subcats = data["subcategories"]
                output.append(
                    self.generate_parent_category(
                        category,
                        self.category_map.get_current_max_subcategories(subcats),
                    )
                )

                for idx, (subcat, subdata) in enumerate(subcats.items()):
                    if "subcategories" in subdata:
                        process_category(subcat, subdata, depth)

                    if "members" in subdata:
                        output.append(
                            self.generate_subclass_row(
                                subcat, subdata["members"], idx, depth
                            )
                        )
                        if idx < len(subcats) - 1 or depth != 0:
                            output.append(self.generate_row_separator())
            elif "members" in data:
                output.append(self.generate_row(category, data["members"], depth))
                output.append(self.generate_row_separator())

        for idx, (category, data) in enumerate(self.categories.items()):
            process_category(category, data)

        return "\n".join(output[:-1] + [self.generate_footer()])
