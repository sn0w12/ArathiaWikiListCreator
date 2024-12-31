class Category:
    def __init__(self, name, subcategories=None):
        self.name = name
        self.subcategories = subcategories or {}
        self.entries = []

    def add_entry(self, entry):
        self.entries.append(entry)
