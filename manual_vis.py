from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTreeWidget,
    QTreeWidgetItem,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLineEdit,
    QTextEdit,
    QLabel,
    QSplitter,
    QSpinBox,
    QDialog,
    QFileDialog,
)
from PyQt6.QtCore import Qt
from src.list_builder import ManualListBuilder
import qdarktheme
import json


class OptionsDialog(QDialog):
    def __init__(self, parent=None, extra_depth=0):
        super().__init__(parent)
        self.setWindowTitle("Category Options")
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Extra depth spinner
        depth_layout = QHBoxLayout()
        depth_label = QLabel("Extra Depth:")
        self.depth_spinner = QSpinBox()
        self.depth_spinner.setRange(0, 10)
        self.depth_spinner.setValue(extra_depth)
        depth_layout.addWidget(depth_label)
        depth_layout.addWidget(self.depth_spinner)
        layout.addLayout(depth_layout)

        # OK button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)


class WikiListBuilder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wiki List Builder")
        self.setGeometry(100, 100, 1200, 800)

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        # Create splitter for resizable sections
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left panel - Tree and controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Add save/load buttons at the top
        file_buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save List")
        self.import_btn = QPushButton("Import List")
        self.save_btn.clicked.connect(self.save_list)
        self.import_btn.clicked.connect(self.import_list)
        file_buttons_layout.addWidget(self.save_btn)
        file_buttons_layout.addWidget(self.import_btn)
        left_layout.addLayout(file_buttons_layout)

        # Add title input
        title_layout = QHBoxLayout()
        title_label = QLabel("List Title:")
        self.list_title_input = QLineEdit("List of Items")  # Default title
        self.list_title_input.textChanged.connect(self.update_preview)
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.list_title_input)
        left_layout.addLayout(title_layout)

        # Tree widget (now after title input)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Items"])
        self.tree.itemSelectionChanged.connect(self.on_selection_changed)
        left_layout.addWidget(self.tree)

        # Buttons
        button_layout = QHBoxLayout()
        self.add_category_btn = QPushButton("Add Category")
        self.add_subcategory_btn = QPushButton("Add Subcategory")
        self.add_item_btn = QPushButton("Add Item")
        self.remove_btn = QPushButton("Remove")

        self.add_category_btn.clicked.connect(self.add_category)
        self.add_subcategory_btn.clicked.connect(self.add_subcategory)
        self.add_item_btn.clicked.connect(self.add_item)
        self.remove_btn.clicked.connect(self.remove_selected)

        for btn in (self.add_category_btn, self.add_subcategory_btn, self.add_item_btn, self.remove_btn):
            button_layout.addWidget(btn)

        # Add options button
        self.options_btn = QPushButton("Options")
        self.options_btn.clicked.connect(self.show_options)
        button_layout.addWidget(self.options_btn)

        left_layout.addLayout(button_layout)
        splitter.addWidget(left_panel)

        # Right panel - Item details and preview
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Item details
        self.title_label = QLabel("Title:")
        self.title_input = QLineEdit()
        self.title_input.textChanged.connect(self.update_selected_item)

        self.desc_label = QLabel("Description:")
        self.desc_input = QTextEdit()
        self.desc_input.textChanged.connect(self.update_selected_item)

        # Preview
        preview_label = QLabel("Preview:")
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)

        for widget in (
            self.title_label,
            self.title_input,
            self.desc_label,
            self.desc_input,
            preview_label,
            self.preview,
        ):
            right_layout.addWidget(widget)

        splitter.addWidget(right_panel)

    def add_category(self):
        item = QTreeWidgetItem(self.tree)
        item.setText(0, "New Category")
        self.tree.setCurrentItem(item)
        self.update_preview()

    def add_subcategory(self):
        current = self.tree.currentItem()
        if current:
            item = QTreeWidgetItem(current)
            item.setText(0, "New Subcategory")
            current.setExpanded(True)
            self.tree.setCurrentItem(item)
            self.update_preview()

    def add_item(self):
        current = self.tree.currentItem()
        if current:
            item = QTreeWidgetItem(current)
            item.setText(0, "New Item")
            item.setData(0, Qt.ItemDataRole.UserRole, "")  # Store description
            current.setExpanded(True)
            self.tree.setCurrentItem(item)
            self.update_preview()

    def remove_selected(self):
        current = self.tree.currentItem()
        if current:
            parent = current.parent()
            if parent:
                parent.removeChild(current)
            else:
                self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(current))
            self.update_preview()

    def on_selection_changed(self):
        current = self.tree.currentItem()
        if current:
            self.title_input.setText(current.text(0))
            self.desc_input.setText(current.data(0, Qt.ItemDataRole.UserRole) or "")
        else:
            self.title_input.clear()
            self.desc_input.clear()

    def update_selected_item(self):
        current = self.tree.currentItem()
        if current:
            current.setText(0, self.title_input.text())
            current.setData(0, Qt.ItemDataRole.UserRole, self.desc_input.toPlainText())
            self.update_preview()

    def show_options(self):
        current = self.tree.currentItem()
        if current:
            # Get current options
            options = current.data(0, Qt.ItemDataRole.UserRole + 1) or {}
            extra_depth = options.get("extra_depth", 0)

            dialog = OptionsDialog(self, extra_depth)
            if dialog.exec():
                # Update options
                options = {"extra_depth": dialog.depth_spinner.value()}
                current.setData(0, Qt.ItemDataRole.UserRole + 1, options)
                self.update_preview()

    def tree_to_dict(self):
        def process_item(item):
            if item.childCount() == 0:
                return item.data(0, Qt.ItemDataRole.UserRole)

            result = {}
            options = item.data(0, Qt.ItemDataRole.UserRole + 1)
            if options:
                result["__options"] = options

            for i in range(item.childCount()):
                child = item.child(i)
                result[child.text(0)] = process_item(child)
            return result

        root_dict = {
            "__title": self.list_title_input.text(),
        }
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            root_dict[item.text(0)] = process_item(item)
        return root_dict

    def update_preview(self):
        data = self.tree_to_dict()
        if data:
            title = data.pop("__title", "List of Items")
            builder = ManualListBuilder(title, data)
            self.preview.setText(builder.build())

    def save_list(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Wiki List",
            "",
            "JSON Files (*.json);;All Files (*)",
        )
        if file_name:
            data = self.tree_to_dict()
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

    def import_list(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Import Wiki List",
            "",
            "JSON Files (*.json);;All Files (*)",
        )
        if file_name:
            with open(file_name, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.load_tree_data(data)
                self.update_preview()

    def load_tree_data(self, data, parent=None):
        # Set title if present
        if "__title" in data:
            self.list_title_input.setText(data["__title"])
            data = {k: v for k, v in data.items() if k != "__title"}

        for key, value in data.items():
            if key == "__options":
                continue
            if isinstance(value, dict):
                if parent is None:
                    item = QTreeWidgetItem(self.tree)
                else:
                    item = QTreeWidgetItem(parent)
                item.setText(0, key)
                if "__options" in value:
                    item.setData(0, Qt.ItemDataRole.UserRole + 1, value["__options"])
                self.load_tree_data(value, item)
            else:
                if parent is None:
                    item = QTreeWidgetItem(self.tree)
                else:
                    item = QTreeWidgetItem(parent)
                item.setText(0, key)
                item.setData(0, Qt.ItemDataRole.UserRole, value)


if __name__ == "__main__":
    app = QApplication([])
    qdarktheme.setup_theme()
    window = WikiListBuilder()
    window.show()
    app.exec()
