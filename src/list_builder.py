from src.wiki_template import WikiTemplate, CategoryMap


class GenericListBuilder:
    def __init__(self, title, category_name: str, category_map: CategoryMap):
        self.template = WikiTemplate(title, category_map)
        print(category_map)
        self.template.fetch_category(category_name)

    def build(self) -> str:
        return self.template.build()


class CharacterListBuilder:
    def __init__(self):
        categories = {
            "Humanoid Characters": {
                "subcategories": {
                    "Major Races": {
                        "subcategories": {
                            "Human Characters": {},
                            "Draconian Characters": {},
                            "Eldarin Characters": {},
                            "Moros Characters": {},
                        }
                    },
                    "Demonborn Characters": {},
                    "Vampire Characters": {},
                    "Giant Characters": {},
                }
            },
            "God Characters": {},
            "Demigod Characters": {},
            "Dragon Characters": {},
        }

        category_titles = {
            "Humanoid Characters": "[[:Category:Humanoid_Species|Humanoid]] Characters",
            "God Characters": "[[God]] Characters",
            "Demigod Characters": "[[Demigod]] Characters",
            "Dragon Characters": "[[Dragon]] Characters",
            "Human Characters": "[[Homosapien|Human]] Characters",
            "Draconian Characters": "[[Draconian]] Characters",
            "Eldarin Characters": "[[Eldarin]] Characters",
            "Moros Characters": "[[Moros]] Characters",
            "Demonborn Characters": "[[Demonborn]] Characters",
            "Vampire Characters": "[[Vampire]] Characters",
            "Giant Characters": "[[Giants|Giant]] Characters",
        }

        category_map = CategoryMap(categories, category_titles)
        self.generic_builder = GenericListBuilder(
            "List of Characters", "Characters", category_map
        )

    def build(self) -> str:
        return self.generic_builder.build()


class CountryListBuilder:
    def __init__(self):
        categories = {
            "Arathia": {
                "subcategories": {
                    "Major Countries": {},
                    "Minor Countries": {},
                    "Fallen Countries": {},
                }
            },
            "Elysium": {
                "subcategories": {
                    "Major Elysian Countries": {},
                    "Minor Elysian Countries": {},
                    "Fallen Elysian Countries": {},
                }
            },
        }

        category_titles = {
            "Arathia": "[[Arathia]]",
            "Elysium": "[[Elysium]]",
            "Major Elysian Countries": "Major Countries",
            "Minor Elysian Countries": "Minor Countries",
            "Fallen Elysian Countries": "Fallen Countries",
        }

        category_map = CategoryMap(categories, category_titles)
        self.generic_builder = GenericListBuilder(
            "List of Countries", "Countries", category_map
        )

    def build(self) -> str:
        return self.generic_builder.build()


class OathListBuilder:
    def __init__(self):
        categories = {
            "Solar Oaths": {},
            "Void Oaths": {},
            "Arc Oaths": {},
            "Vampiric Oaths": {},
            "Soulseeker Oaths": {},
            "Dragon Oaths": {},
        }

        category_titles = {
            "Solar Oaths": "[[Solar]]",
            "Void Oaths": "[[Void]]",
            "Arc Oaths": "[[Arc]]",
            "Vampiric Oaths": "[[Vampiric]]",
            "Soulseeker Oaths": "[[Soulseeker]]",
            "Dragon Oaths": "[[Dragon (Power)|Dragon]]",
        }

        category_map = CategoryMap(categories, category_titles)
        self.generic_builder = GenericListBuilder(
            "List of [[Oaths]]", "Oaths", category_map
        )

    def build(self) -> str:
        return self.generic_builder.build()
