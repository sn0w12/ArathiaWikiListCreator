from api import WikiAPI
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from functools import partial


class CategoryMap:
    """
    A class for managing hierarchical category structures and their mappings.
    This class handles category relationships, titles, and various metrics about the category hierarchy.
    It supports nested subcategories and provides methods to query and manipulate the category structure.
    Attributes:
        categories (Dict[str, Dict]): The normalized category hierarchy structure.
        category_titles (Dict[str, str]): Mapping of category identifiers to their display titles.
    Example:
        categories = {
            "parent": {
                "child1": {},
                "child2": {"grandchild": {}}
            }
        }
        titles = {"parent": "Parent Category", "child1": "First Child"}
        category_map = CategoryMap(categories, titles)
    """

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

    def get_mapped_category(self, category: str) -> Tuple[str, Optional[str], Optional[str]]:
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
        return max(len(data.get("subcategories", [])) for data in self.categories.values())

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
            contrib = n if n >= 2 else 1

            # Sum contributions from children
            child_sum = 0
            for subnode in node.get("subcategories", {}).values():
                child_contrib = count_splits(subnode)
                if child_contrib > 0:
                    child_sum += child_contrib - 1
            return contrib + child_sum

        return count_splits({"subcategories": data})

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
    """
    A template engine for generating MediaWiki tables with hierarchical category structures.
    This class handles the creation of collapsible wiki tables with nested category hierarchies,
    processing wiki categories and their members according to a predefined category mapping system.
    Attributes:
        title (str): The title of the wiki table.
        wiki_api (WikiAPI): Interface for wiki operations.
        rows (list): Storage for table rows.
        categories (dict): Nested dictionary storing category hierarchies and their members.
        category_map (CategoryMap): Mapping system for categories and their relationships.
        ```
    """

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
                    subcat: initialize_category_structure(subdata) for subcat, subdata in data["subcategories"].items()
                }
            }

        # Initialize all categories from the map
        for category, data in self.category_map.get_all_categories().items():
            self.categories[category] = initialize_category_structure(data)

    def _find_category_dict(self, category: str, subcategory: str | None = None) -> dict:
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
        """
        Fetches and processes members of a specified wiki category, organizing them into mapped categories.
        This method retrieves all members and subcategories from a given wiki category, then processes
        each member's categories in parallel to organize them according to the category mapping system.
        Any members that don't fit into mapped categories are identified as uncategorized.
        Args:
            category_name (str): The name of the wiki category to fetch and process.
        Returns:
            None
        """
        members, subcategories = self.wiki_api.get_category_members(category_name)
        unCategorized = set(members)

        # Process categories in parallel
        with ThreadPoolExecutor(max_workers=10) as executor:
            process_func = partial(self._process_member_categories, base_category=category_name)
            results = list(executor.map(process_func, members))

        # Aggregate results
        for member_results in results:
            for category, member in member_results:
                parent_category, subcategory, display_title = self.category_map.get_mapped_category(category)
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
        row_classes = ["dotted-row"]
        if i == 0 and depth != 0:
            row_classes.append("custom-row")
        row_class_1 = f'class="{" ".join(row_classes)}" |' if row_classes else ""
        row_class_2 = (
            f'class="{" ".join([c for c in row_classes if c != "dotted-row"])}" |' if len(row_classes) > 1 else ""
        )
        wrapped_members = [f"[[{member}]]" for member in members]

        max_depth = self.category_map.get_max_category_depth()
        colspan = f'colspan="{max_depth - depth} "' if row_class_2 else f'colspan="{max_depth - depth}"|'

        return f"|{row_class_1}{display_title}\n|{colspan}{row_class_2}{self.generate_member_separator().join(wrapped_members)}"

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
        """
        Builds the complete wiki table with hierarchical category structures.

        Returns:
            str: The generated wiki table as a string.
        """
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
                        output.append(self.generate_subclass_row(subcat, subdata["members"], idx, depth))
                        if idx < len(subcats) - 1 or depth != 0:
                            output.append(self.generate_row_separator())
            elif "members" in data:
                output.append(self.generate_row(category, data["members"], depth))
                output.append(self.generate_row_separator())

        for idx, (category, data) in enumerate(self.categories.items()):
            process_category(category, data)

        return "\n".join(output[:-1] + [self.generate_footer()])


class ManualWikiTemplate:
    def __init__(self, title, categories, collapsible=False):
        # Title can be either a string or a list of dicts with 'title' and 'cols' keys
        # The last title in the list doesn't need 'cols' specified
        self.title = title
        self.categories = categories
        self.collapsible = collapsible

    def get_max_category_depth(self) -> int:
        """Returns the maximum depth of nested subcategories"""
        if not self.categories:
            return 0

        def get_depth(d: dict) -> int:
            if not isinstance(d, dict):
                return 1
            if not d:
                return 1
            return 1 + max(get_depth(v) for v in d.values())

        return get_depth(self.categories)

    def get_current_max_subcategories(self, data: dict) -> int:
        """Returns the maximum number of leaf nodes under any category"""

        def count_leaves(d: dict) -> int:
            if not isinstance(d, dict):
                return 1
            if not d:
                return 0
            # If it's a leaf node (has description)
            if "description" in d:
                return 1
            # Filter out metadata and options
            filtered_dict = {k: v for k, v in d.items() if k not in ["__metadata", "__options"]}
            return sum(count_leaves(v) for v in filtered_dict.values())

        def get_max_at_level(d: dict) -> int:
            if not isinstance(d, dict):
                return 1
            if not d:
                return 0
            if "description" in d:
                return 1

            # Filter out metadata and options
            filtered_dict = {k: v for k, v in d.items() if k not in ["__metadata", "__options"]}

            # Count leaves under current node
            current = count_leaves(filtered_dict)

            # Recursively get max from children
            child_maxes = [get_max_at_level(v) for v in filtered_dict.values() if isinstance(v, dict)]

            return max([current] + child_maxes)

        return get_max_at_level(data)

    def get_category_options(self, category_data):
        """Extract options from category data"""
        if isinstance(category_data, dict):
            return category_data.get("__options", {})
        return {}

    def get_extra_depth(self, category_data):
        """Get extra depth from category options"""
        options = self.get_category_options(category_data)
        return options.get("extra_depth", 0)

    def process_data_without_options(self, data):
        """Get category data without the options and metadata fields"""
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if k not in ["__options", "__metadata"]}
        return data

    def generate_parent_category(self, category: str, member_count: int, depth: int = 1):
        colspan = f' colspan="{depth}"' if depth > 1 else ""
        return f"""|rowspan="{member_count}"{colspan} class="custom-rowspan"|{category}"""

    def generate_header(self):
        base = f"""{{| class="{"mw-collapsible mw-collapsed " if self.collapsible else ""}wikitable custom-button" style="width:100%;\n"""

        if isinstance(self.title, str):
            # Original behavior for single string title
            return (
                base
                + f"""! colspan="{self.get_max_category_depth() + 1}" style="text-align:center; font-weight: bold; position: relative;" | {self.title}\n|-"""
            )
        else:
            # Handle multiple titles
            titles = []
            total_cols = self.get_max_category_depth() + 1
            remaining_cols = total_cols

            for i, title_data in enumerate(self.title):
                if isinstance(title_data, dict):
                    class_name = ""
                    if i == len(self.title) - 1:
                        # Last title gets all remaining columns
                        cols = remaining_cols
                    else:
                        cols = title_data.get("cols", 1)
                        class_name = ' class="dotted-row"'
                        remaining_cols -= cols
                    titles.append(
                        f"""! colspan="{cols}"{class_name} style="text-align:center; font-weight: bold; position: relative;" | {title_data["title"]}"""
                    )
                else:
                    # Handle string title (should only be used if it's the only title)
                    titles.append(
                        f"""! colspan="{total_cols}" style="text-align:center; font-weight: bold; position: relative;" | {title_data}"""
                    )

            return base + "\n".join(titles) + "\n|-"

    def generate_row_separator(self):
        return "|-"

    def generate_member_separator(self):
        return r"{{ts}}"

    def generate_footer(self):
        return "|}"

    def build(self) -> str:
        output = []
        output.append(self.generate_header())

        def process_category(items, current_depth=0):
            for idx, (title, content) in enumerate(items.items()):
                if isinstance(content, dict):
                    if title == "__metadata":
                        continue

                    if "description" in content:
                        # For items with descriptions
                        max_depth = self.get_max_category_depth()
                        colspan = max_depth - current_depth
                        output.append(
                            f"""|class="dotted-row{" custom-row" if idx == 0 else ""}" colspan="{colspan}"|{title}\n|{' class="custom-row"|' if idx == 0 else ""}{self.generate_member_separator().join([f"{content['description']}"])}"""
                        )
                        output.append(self.generate_row_separator())
                    else:
                        # For categories
                        data = self.process_data_without_options(content)
                        extra_depth = self.get_extra_depth(content)

                        # Calculate colspan based on nesting level and extra depth
                        remaining_depth = self.get_max_category_depth() - current_depth
                        base_colspan = min(remaining_depth, extra_depth + 1)

                        output.append(
                            self.generate_parent_category(title, self.get_current_max_subcategories(data), base_colspan)
                        )
                        # Pass extra_depth to next level
                        process_category(data, current_depth + 1 + extra_depth)

        process_category(self.categories)
        return "\n".join(output + [self.generate_footer()])
