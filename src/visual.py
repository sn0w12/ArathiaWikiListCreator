import os
import gzip
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
    QCheckBox,
    QListWidget,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from list_builder import ManualListBuilder
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


class TitleEditor(QDialog):
    def __init__(self, parent=None, titles=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Titles")
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Title list widget
        self.titles_widget = QTreeWidget()
        self.titles_widget.setHeaderLabels(["Title", "Columns"])
        self.titles_widget.setRootIsDecorated(False)
        layout.addWidget(self.titles_widget)

        # Buttons for managing titles
        button_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Title")
        self.remove_btn = QPushButton("Remove Title")
        self.add_btn.clicked.connect(self.add_title)
        self.remove_btn.clicked.connect(self.remove_title)
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.remove_btn)
        layout.addLayout(button_layout)

        # OK/Cancel buttons
        dialog_buttons = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        dialog_buttons.addWidget(ok_button)
        dialog_buttons.addWidget(cancel_button)
        layout.addLayout(dialog_buttons)

        # Load existing titles
        if titles:
            self.load_titles(titles)
        else:
            self.add_title()

    def update_column_editability(self):
        """Update which columns fields are editable"""
        for i in range(self.titles_widget.topLevelItemCount()):
            item = self.titles_widget.topLevelItem(i)
            # Only allow editing columns for non-last items
            if i == self.titles_widget.topLevelItemCount() - 1:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setText(1, "")  # Clear columns for last item
            else:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)

    def add_title(self):
        item = QTreeWidgetItem(self.titles_widget)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        item.setText(0, "New Title")
        item.setText(1, "1")
        self.titles_widget.setCurrentItem(item)
        self.update_column_editability()

    def remove_title(self):
        current = self.titles_widget.currentItem()
        if current:
            self.titles_widget.takeTopLevelItem(self.titles_widget.indexOfTopLevelItem(current))
            self.update_column_editability()

    def load_titles(self, titles):
        if isinstance(titles, str):
            item = QTreeWidgetItem(self.titles_widget)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            item.setText(0, titles)
            item.setText(1, "")
        else:
            for title_data in titles:
                item = QTreeWidgetItem(self.titles_widget)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                if isinstance(title_data, dict):
                    item.setText(0, title_data["title"])
                    item.setText(1, str(title_data.get("cols", 1)))
                else:
                    item.setText(0, title_data)
                    item.setText(1, "")
        self.update_column_editability()

    def get_titles(self):
        titles = []
        for i in range(self.titles_widget.topLevelItemCount()):
            item = self.titles_widget.topLevelItem(i)
            title = item.text(0)
            cols = item.text(1)

            if cols and i < self.titles_widget.topLevelItemCount() - 1:
                titles.append({"title": title, "cols": int(cols)})
            else:
                titles.append({"title": title})

        # If there's only one title without columns, return just the string
        if len(titles) == 1 and "cols" not in titles[0]:
            return titles[0]["title"]

        return titles


class SaveSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select or Create List")
        self.setModal(True)
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout(self)

        # List of saves
        self.saves_list = QListWidget()
        layout.addWidget(self.saves_list)

        # Buttons
        button_layout = QHBoxLayout()
        self.new_btn = QPushButton("New List")
        self.open_btn = QPushButton("Open Selected")
        self.remove_btn = QPushButton("Remove Selected")  # New remove button

        self.new_btn.clicked.connect(self.create_new)
        self.open_btn.clicked.connect(self.accept)
        self.remove_btn.clicked.connect(self.remove_selected)  # New remove handler

        button_layout.addWidget(self.new_btn)
        button_layout.addWidget(self.open_btn)
        button_layout.addWidget(self.remove_btn)
        layout.addLayout(button_layout)

        # Load existing saves
        self.load_saves()

        # Enable buttons only when item selected
        self.open_btn.setEnabled(False)
        self.remove_btn.setEnabled(False)
        self.saves_list.itemSelectionChanged.connect(self.update_button_states)

    def update_button_states(self):
        has_selection = bool(self.saves_list.selectedItems())
        self.open_btn.setEnabled(has_selection)
        self.remove_btn.setEnabled(has_selection)

    def remove_selected(self):
        current = self.saves_list.currentItem()
        if current:
            reply = QMessageBox.question(
                self,
                "Confirm Removal",
                f'Are you sure you want to remove "{current.text()}"?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                file_path = os.path.join("saves", f"{current.text()}.json.gz")
                try:
                    os.remove(file_path)
                    self.saves_list.takeItem(self.saves_list.row(current))
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Could not remove file: {e}")

    def load_saves(self):
        saves_dir = "saves"
        if os.path.exists(saves_dir):
            for file in os.listdir(saves_dir):
                if file.endswith(".json.gz"):
                    self.saves_list.addItem(file[:-8])  # Remove .json.gz

    def create_new(self):
        """Clear selection and create new list"""
        self.saves_list.clearSelection()  # Clear any existing selection
        self.selected_name = None
        self.accept()

    def get_selected(self):
        if self.saves_list.selectedItems():
            return self.saves_list.currentItem().text()
        return None


class WikiListBuilder(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create saves directory if it doesn't exist
        os.makedirs("saves", exist_ok=True)

        # Initialize UI first
        self.setWindowTitle("Wiki List Builder")
        self.setGeometry(100, 100, 1200, 800)

        self.setWindowIcon(QIcon("img/arathia.ico"))

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

        # Modify file buttons at the top
        file_buttons_layout = QHBoxLayout()
        self.open_list_btn = QPushButton("Open List")  # New button
        self.save_btn = QPushButton("Save")  # New auto-save button
        self.export_btn = QPushButton("Export")  # Renamed from "Save List"
        self.import_btn = QPushButton("Import List")

        self.open_list_btn.clicked.connect(self.show_list_selection)
        self.save_btn.clicked.connect(self.auto_save)
        self.export_btn.clicked.connect(self.export_list)  # Renamed from save_list
        self.import_btn.clicked.connect(self.import_list)

        for btn in (self.open_list_btn, self.save_btn, self.export_btn, self.import_btn):
            file_buttons_layout.addWidget(btn)
        left_layout.addLayout(file_buttons_layout)

        # Add title input
        title_layout = QHBoxLayout()
        title_label = QLabel("List Title:")
        self.list_title_input = QLineEdit("List of Items")  # Default title
        self.edit_titles_btn = QPushButton("Edit Titles")
        self.edit_titles_btn.clicked.connect(self.edit_titles)
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.list_title_input)
        title_layout.addWidget(self.edit_titles_btn)
        left_layout.addLayout(title_layout)

        # Add collapsible checkbox after title input
        collapsible_layout = QHBoxLayout()
        self.collapsible_checkbox = QCheckBox("Collapsible")
        self.collapsible_checkbox.stateChanged.connect(self.update_preview)
        collapsible_layout.addWidget(self.collapsible_checkbox)
        left_layout.addLayout(collapsible_layout)

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

        # After all UI elements are created, show save selection dialog
        dialog = SaveSelectionDialog()
        if dialog.exec():
            selected = dialog.get_selected()
            if selected:
                self.load_from_save(selected)

    def get_safe_filename(self):
        """Convert title to safe filename"""
        title = self.list_title_input.text().split("|")[0].strip()
        return "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).rstrip()

    def auto_save(self):
        """Automatically save the current state"""
        data = self.tree_to_dict()
        if data:
            filename = self.get_safe_filename()
            if filename:
                save_path = os.path.join("saves", f"{filename}.json.gz")
                with gzip.open(save_path, "wt", encoding="utf-8") as f:
                    json.dump(data, f)

    def load_from_save(self, name):
        """Load data from a saved file"""
        try:
            save_path = os.path.join("saves", f"{name}.json.gz")
            with gzip.open(save_path, "rt", encoding="utf-8") as f:
                data = json.load(f)
                self.load_tree_data(data)
                self.update_preview()
                self.auto_save()
        except Exception as e:
            print(f"Error loading save: {e}")

    def add_category(self):
        item = QTreeWidgetItem(self.tree)
        item.setText(0, "New Category")
        item.setData(0, Qt.ItemDataRole.UserRole + 2, "category")  # Store item type
        self.tree.setCurrentItem(item)
        self.update_preview()
        self.auto_save()

    def add_subcategory(self):
        current = self.tree.currentItem()
        if current:
            item = QTreeWidgetItem(current)
            item.setText(0, "New Subcategory")
            item.setData(0, Qt.ItemDataRole.UserRole + 2, "subcategory")  # Store item type
            current.setExpanded(True)
            self.tree.setCurrentItem(item)
            self.update_preview()
            self.auto_save()

    def add_item(self):
        current = self.tree.currentItem()
        if current:
            item = QTreeWidgetItem(current)
            item.setText(0, "New Item")
            item.setData(0, Qt.ItemDataRole.UserRole, "")  # Store description
            item.setData(0, Qt.ItemDataRole.UserRole + 2, "item")  # Store item type
            current.setExpanded(True)
            self.tree.setCurrentItem(item)
            self.update_preview()
            self.auto_save()

    def remove_selected(self):
        current = self.tree.currentItem()
        if current:
            parent = current.parent()
            if parent:
                parent.removeChild(current)
            else:
                self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(current))
            self.update_preview()
            self.auto_save()

    def update_button_states(self, current):
        """Update button states based on selected item type"""
        if not current:
            # No selection - disable all add buttons
            self.add_category_btn.setEnabled(False)
            self.add_subcategory_btn.setEnabled(False)
            self.add_item_btn.setEnabled(False)
            return

        item_type = current.data(0, Qt.ItemDataRole.UserRole + 2)

        if item_type == "category":
            # Categories can contain anything
            self.add_category_btn.setEnabled(True)
            self.add_subcategory_btn.setEnabled(True)
            self.add_item_btn.setEnabled(True)
        elif item_type == "subcategory":
            # Subcategories can contain subcategories and items
            self.add_category_btn.setEnabled(False)
            self.add_subcategory_btn.setEnabled(True)
            self.add_item_btn.setEnabled(True)
        else:  # item type
            # Items can't contain anything
            self.add_category_btn.setEnabled(False)
            self.add_subcategory_btn.setEnabled(False)
            self.add_item_btn.setEnabled(False)

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
                self.desc_input.blockSignals(True)
                self.desc_input.setText(current.data(0, Qt.ItemDataRole.UserRole) or "")
                self.desc_input.blockSignals(False)
                self.desc_input.textChanged.connect(lambda: self.update_description(current))
            else:
                self.desc_input.clear()

            # Enable options only for subcategories
            item_type = current.data(0, Qt.ItemDataRole.UserRole + 2)
            self.options_btn.setEnabled(item_type == "subcategory" or item_type == "category")
        else:
            self.title_input.clear()
            self.desc_input.clear()
            self.options_btn.setEnabled(False)

        self.update_button_states(current)
        self.update_move_buttons()

    def update_description(self, item):
        """Update description and auto-save"""
        if item and item.childCount() == 0:
            item.setData(0, Qt.ItemDataRole.UserRole, self.desc_input.toPlainText())
            self.update_preview()
            self.auto_save()

    def update_selected_item(self):
        """Update title and auto-save"""
        current = self.tree.currentItem()
        if current:
            current.setText(0, self.title_input.text())
            self.update_preview()
            self.auto_save()

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
                self.auto_save()

    def edit_titles(self):
        # Get the stored title data if it exists, otherwise use the display text
        current_titles = self.list_title_input.property("titleData") or self.list_title_input.text()
        dialog = TitleEditor(self, current_titles)
        if dialog.exec():
            titles = dialog.get_titles()
            if isinstance(titles, str):
                self.list_title_input.setText(titles)
                self.list_title_input.setProperty("titleData", None)  # Clear stored data if it's a simple title
            else:
                # Store the full title data and show first title in input
                self.list_title_input.setProperty("titleData", titles)
                self.list_title_input.setText(" | ".join(t["title"] if isinstance(t, dict) else t for t in titles))
            self.update_preview()
            self.auto_save()

    def tree_to_dict(self):
        def process_item(item):
            item_type = item.data(0, Qt.ItemDataRole.UserRole + 2)

            if item.childCount() == 0:
                # For leaf nodes (items)
                return {"__metadata": {"type": item_type}, "description": item.data(0, Qt.ItemDataRole.UserRole)}

            result = {"__metadata": {"type": item_type}}

            options = item.data(0, Qt.ItemDataRole.UserRole + 1)
            if options:
                result["__options"] = options

            for i in range(item.childCount()):
                child = item.child(i)
                result[child.text(0)] = process_item(child)
            return result

        root_dict = {}

        # Add collapsible state to the data
        root_dict["__collapsible"] = self.collapsible_checkbox.isChecked()

        # Handle title data
        title_data = self.list_title_input.property("titleData")
        if title_data:
            root_dict["__title"] = title_data
        else:
            root_dict["__title"] = self.list_title_input.text()

        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            root_dict[item.text(0)] = process_item(item)
        return root_dict

    def update_preview(self):
        data = self.tree_to_dict()
        if data:
            title = data.pop("__title", "List of Items")
            collapsible = data.pop("__collapsible", False)
            builder = ManualListBuilder(title, data, collapsible=collapsible)
            self.preview.setText(builder.build())

    def export_list(self):
        """Renamed from save_list - exports to external file"""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Export Wiki List",
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
            title_data = data["__title"]
            if isinstance(title_data, (list, dict)):
                self.list_title_input.setProperty("titleData", title_data)
                self.list_title_input.setText(
                    " | ".join(
                        t["title"] if isinstance(t, dict) else t
                        for t in (title_data if isinstance(title_data, list) else [title_data])
                    )
                )
            else:
                self.list_title_input.setText(str(title_data))
            data = {k: v for k, v in data.items() if k != "__title"}

        # Set collapsible state if present
        if "__collapsible" in data:
            self.collapsible_checkbox.setChecked(data["__collapsible"])
            data = {k: v for k, v in data.items() if k != "__collapsible"}

        for key, value in data.items():
            if key in ["__options", "__metadata"]:
                continue

            if isinstance(value, dict):
                if parent is None:
                    item = QTreeWidgetItem(self.tree)
                else:
                    item = QTreeWidgetItem(parent)
                item.setText(0, key)

                # Set metadata (item type)
                if "__metadata" in value:
                    item.setData(0, Qt.ItemDataRole.UserRole + 2, value["__metadata"].get("type", "category"))

                # Set options if present
                if "__options" in value:
                    item.setData(0, Qt.ItemDataRole.UserRole + 1, value["__options"])

                # Set description for items
                if "description" in value:
                    item.setData(0, Qt.ItemDataRole.UserRole, value["description"])

                # Recursively process children (excluding metadata and options)
                child_data = {k: v for k, v in value.items() if k not in ["__metadata", "__options", "description"]}
                self.load_tree_data(child_data, item)

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
            self.auto_save()

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
            self.auto_save()

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

    def clear_list(self):
        """Clear all current list data and add empty category"""
        self.tree.clear()
        self.list_title_input.setText("List of Items")
        self.list_title_input.setProperty("titleData", None)
        self.collapsible_checkbox.setChecked(False)

        # Add empty category
        item = QTreeWidgetItem(self.tree)
        item.setText(0, "New Category")
        item.setData(0, Qt.ItemDataRole.UserRole + 2, "category")
        self.tree.setCurrentItem(item)

        self.update_preview()

    def show_list_selection(self):
        """Show the list selection dialog"""
        dialog = SaveSelectionDialog(self)
        if dialog.exec():
            selected = dialog.get_selected()
            if selected:
                self.load_from_save(selected)
            else:
                # Clear the current list when creating a new one
                self.clear_list()


if __name__ == "__main__":
    app = QApplication([])
    qdarktheme.setup_theme()
    window = WikiListBuilder()
    window.show()
    app.exec()
