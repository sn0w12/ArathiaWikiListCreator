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
        move_layout = QHBoxLayout()  # New layout for movement buttons

        self.add_category_btn = QPushButton("Add Category")
        self.add_subcategory_btn = QPushButton("Add Subcategory")
        self.add_item_btn = QPushButton("Add Item")
        self.remove_btn = QPushButton("Remove")
        self.move_up_btn = QPushButton("↑")  # Up arrow
        self.move_down_btn = QPushButton("↓")  # Down arrow

        self.add_category_btn.clicked.connect(self.add_category)
        self.add_subcategory_btn.clicked.connect(self.add_subcategory)
        self.add_item_btn.clicked.connect(self.add_item)
        self.remove_btn.clicked.connect(self.remove_selected)
        self.move_up_btn.clicked.connect(self.move_item_up)
        self.move_down_btn.clicked.connect(self.move_item_down)

        # Add movement buttons to their own layout
        move_layout.addWidget(self.move_up_btn)
        move_layout.addWidget(self.move_down_btn)

        for btn in (self.add_category_btn, self.add_subcategory_btn, self.add_item_btn, self.remove_btn):
            button_layout.addWidget(btn)

        # Add options button
        self.options_btn = QPushButton("Options")
        self.options_btn.clicked.connect(self.show_options)
        self.options_btn.setEnabled(False)
        button_layout.addWidget(self.options_btn)

        left_layout.addLayout(button_layout)
        left_layout.addLayout(move_layout)  # Add movement buttons layout
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
        # Remove the disconnect line - we'll handle connections in on_selection_changed

        # Preview
        preview_label = QLabel("Preview:")
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)

        # Add copy button
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.clicked.connect(self.copy_preview)

        for widget in (
            self.title_label,
            self.title_input,
            self.desc_label,
            self.desc_input,
            preview_label,
            self.preview,
            self.copy_btn,  # Add the copy button to the layout
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
        # Safe disconnect - check if there are any connections first
        if self.desc_input.receivers(self.desc_input.textChanged) > 0:
            self.desc_input.textChanged.disconnect()

        current = self.tree.currentItem()
        if current:
            self.title_input.setText(current.text(0))
            # Only show and enable description for items (leaves)
            is_leaf = current.childCount() == 0
            self.desc_label.setVisible(is_leaf)
            self.desc_input.setVisible(is_leaf)
            self.desc_input.setEnabled(is_leaf)
            if is_leaf:
                self.desc_input.blockSignals(True)  # Block signals while setting text
                self.desc_input.setText(current.data(0, Qt.ItemDataRole.UserRole) or "")
                self.desc_input.blockSignals(False)  # Re-enable signals
                # Create a unique connection for this item
                self.desc_input.textChanged.connect(lambda: self.update_description(current))
            else:
                self.desc_input.clear()
            options_enabled = current.childCount() > 0
            self.options_btn.setEnabled(options_enabled)
        else:
            self.title_input.clear()
            self.desc_input.clear()
            self.options_btn.setEnabled(False)

        self.update_move_buttons()  # Add this line at the end

    def update_description(self, item):
        """Update description for a specific item"""
        if item and item.childCount() == 0:
            item.setData(0, Qt.ItemDataRole.UserRole, self.desc_input.toPlainText())
            self.update_preview()

    def update_selected_item(self):
        """Only handle title updates now"""
        current = self.tree.currentItem()
        if current:
            current.setText(0, self.title_input.text())
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
                # Only return description for leaf nodes (items)
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

    def copy_preview(self):
        QApplication.clipboard().setText(self.preview.toPlainText())

    def move_item_up(self):
        current = self.tree.currentItem()
        if not current:
            return

        parent = current.parent() or self.tree.invisibleRootItem()
        current_index = parent.indexOfChild(current)

        if current_index > 0:
            # Remove and reinsert the item one position up
            parent.takeChild(current_index)
            parent.insertChild(current_index - 1, current)
            self.tree.setCurrentItem(current)
            self.update_preview()

        self.update_move_buttons()

    def move_item_down(self):
        current = self.tree.currentItem()
        if not current:
            return

        parent = current.parent() or self.tree.invisibleRootItem()
        current_index = parent.indexOfChild(current)

        if current_index < parent.childCount() - 1:
            # Remove and reinsert the item one position down
            parent.takeChild(current_index)
            parent.insertChild(current_index + 1, current)
            self.tree.setCurrentItem(current)
            self.update_preview()

        self.update_move_buttons()

    def update_move_buttons(self):
        current = self.tree.currentItem()
        if not current:
            self.move_up_btn.setEnabled(False)
            self.move_down_btn.setEnabled(False)
            return

        parent = current.parent() or self.tree.invisibleRootItem()
        current_index = parent.indexOfChild(current)

        self.move_up_btn.setEnabled(current_index > 0)
        self.move_down_btn.setEnabled(current_index < parent.childCount() - 1)


if __name__ == "__main__":
    app = QApplication([])
    qdarktheme.setup_theme()
    window = WikiListBuilder()
    window.show()
    app.exec()
