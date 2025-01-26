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
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMenu,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QAction
from list_builder import ManualListBuilder
from datetime import datetime
from colorama import init, Fore, Style
import qdarktheme
import json
import ctypes
import uuid  # Add this import at the top with other imports

init()


LOG_LEVELS = {"INFO": Fore.GREEN, "WARNING": Fore.YELLOW, "ERROR": Fore.RED, "DEBUG": Fore.CYAN}


def log(msg, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    color = LOG_LEVELS.get(level, Fore.WHITE)
    formatted_msg = f"{timestamp} {color}[{level}]{Style.RESET_ALL} {msg}"
    print(formatted_msg)


class OptionsDialog(QDialog):
    def __init__(self, parent=None, extra_depth=0):
        super().__init__(parent)
        self.setWindowTitle("Category Options")
        self.setWindowIcon(QIcon("img/arathia.ico"))
        self.setFixedWidth(250)
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
        self.setWindowIcon(QIcon("img/arathia.ico"))
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
        self.setWindowIcon(QIcon("img/arathia.ico"))
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
        self.save_data = {}  # Store mapping of display names to file IDs
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
            display_name = current.text()
            save_id = self.save_data.get(display_name)

            reply = QMessageBox.question(
                self,
                "Confirm Removal",
                f'Are you sure you want to remove "{display_name}"?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                file_path = os.path.join("saves", f"{save_id}.json.gz")
                try:
                    os.remove(file_path)
                    self.saves_list.takeItem(self.saves_list.row(current))
                    self.save_data.pop(display_name, None)
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Could not remove file: {e}")

    def load_saves(self):
        """Load saves and display their titles"""
        self.saves_list.clear()
        self.save_data.clear()
        saves_dir = "saves"

        if os.path.exists(saves_dir):
            for file in os.listdir(saves_dir):
                if file.endswith(".json.gz"):
                    try:
                        with gzip.open(os.path.join(saves_dir, file), "rt", encoding="utf-8") as f:
                            data = json.load(f)
                            title = data.get("__title", "Untitled")
                            if isinstance(title, (list, dict)):
                                # Handle complex title structures
                                if isinstance(title, list):
                                    display_title = title[0]["title"] if isinstance(title[0], dict) else title[0]
                                else:
                                    display_title = title["title"]
                            else:
                                display_title = str(title)

                            save_id = file[:-8]  # Remove .json.gz
                            self.save_data[display_title] = save_id
                            self.saves_list.addItem(display_title)
                    except Exception as e:
                        log(f"Error loading save {file}: {e}", "ERROR")

    def create_new(self):
        """Clear selection and create new list"""
        self.saves_list.clearSelection()  # Clear any existing selection
        self.selected_name = None
        self.accept()

    def get_selected(self):
        """Return the save ID for the selected item"""
        if self.saves_list.selectedItems():
            display_name = self.saves_list.currentItem().text()
            return self.save_data.get(display_name)
        return None


# Add Command class below imports and above existing classes
class Command:
    def __init__(self, description):
        self.description = description

    def do(self):
        pass

    def undo(self):
        pass


class TreeCommand(Command):
    def __init__(self, description, tree_widget, action_type, item=None, parent=None, old_data=None, new_data=None):
        super().__init__(description)
        self.tree = tree_widget
        self.action_type = action_type
        self.item = item
        self.parent = parent
        self.old_data = old_data
        self.new_data = new_data
        self.old_index = None if not item else (parent or tree_widget.invisibleRootItem()).indexOfChild(item)

    def do(self):
        if self.action_type == "add":
            if self.parent:
                self.parent.addChild(self.item)
            else:
                self.tree.addTopLevelItem(self.item)
        elif self.action_type == "remove":
            if self.parent:
                self.parent.takeChild(self.parent.indexOfChild(self.item))
            else:
                self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(self.item))
        elif self.action_type == "modify":
            self.item.setText(0, self.new_data.get("text", ""))
            self.item.setData(0, Qt.ItemDataRole.UserRole, self.new_data.get("description", ""))
        elif self.action_type == "move":
            current_parent = self.item.parent() or self.tree.invisibleRootItem()
            current_index = current_parent.indexOfChild(self.item)
            current_parent.takeChild(current_index)
            if self.new_data["index"] >= 0:
                current_parent.insertChild(self.new_data["index"], self.item)

    def undo(self):
        if self.action_type == "add":
            if self.parent:
                self.parent.takeChild(self.parent.indexOfChild(self.item))
            else:
                self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(self.item))
        elif self.action_type == "remove":
            if self.parent:
                self.parent.insertChild(self.old_index, self.item)
            else:
                self.tree.insertTopLevelItem(self.old_index, self.item)
        elif self.action_type == "modify":
            self.item.setText(0, self.old_data.get("text", ""))
            self.item.setData(0, Qt.ItemDataRole.UserRole, self.old_data.get("description", ""))
        elif self.action_type == "move":
            current_parent = self.item.parent() or self.tree.invisibleRootItem()
            current_parent.takeChild(current_parent.indexOfChild(self.item))
            current_parent.insertChild(self.old_data["index"], self.item)


class WikiListBuilder(QMainWindow):
    def __init__(self, skip_initial_load=False):
        super().__init__()
        self.auto_save_enabled = True
        self.undo_stack = []
        self.redo_stack = []
        self.current_save_name = None  # Track current save name
        self.loading_list = False  # Add flag to track when we're loading a list
        self.target_save_name = None  # Add new variable to track target save name
        self.save_id = None  # Add save_id to track the unique identifier

        # Create saves directory if it doesn't exist
        os.makedirs("saves", exist_ok=True)

        # Initialize UI first
        self.setWindowTitle("Wiki List Builder")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon("img/arathia.ico"))

        # Setup menu bar
        self.setup_menu_bar()

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

        # Add title input
        title_layout = QHBoxLayout()
        title_label = QLabel("List Title:")
        self.list_title_input = QLineEdit("List of Items")  # Default title
        self.edit_titles_btn = QPushButton("Edit Titles")
        self.edit_titles_btn.clicked.connect(self.edit_titles)
        self.list_title_input.textChanged.connect(self.on_title_changed)  # Track title changes
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
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
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
        self.desc_label.setVisible(False)
        self.desc_input = QTextEdit()
        self.desc_input.setVisible(False)

        screen = QApplication.primaryScreen().geometry()
        desc_height = int(screen.height() * 0.2)
        self.desc_input.setMaximumHeight(desc_height)

        # Create vertical splitter for table and preview
        table_preview_splitter = QSplitter(Qt.Orientation.Vertical)
        screen_height = QApplication.primaryScreen().geometry().height()
        table_height = int(screen_height * 0.7)
        preview_height = int(screen_height * 0.3)

        # Table section
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)

        table_label = QLabel("Data Table:")
        self.table_widget = QTableWidget()
        self.table_widget.setMinimumHeight(100)  # Reduced minimum height

        # Set stretch mode for the header
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)

        table_layout.addWidget(table_label)
        table_layout.addWidget(self.table_widget)
        table_widget.setLayout(table_layout)

        # Preview section
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        preview_label = QLabel("Preview:")
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setMinimumHeight(100)  # Reduced minimum height

        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.clicked.connect(self.copy_preview)

        preview_layout.addWidget(preview_label)
        preview_layout.addWidget(self.preview)
        preview_layout.addWidget(self.copy_btn)
        preview_widget.setLayout(preview_layout)

        # Add widgets to splitter
        table_preview_splitter.addWidget(table_widget)
        table_preview_splitter.addWidget(preview_widget)
        table_preview_splitter.setSizes([table_height, preview_height])

        # Add everything to right panel
        for widget in (
            self.title_label,
            self.title_input,
            self.desc_label,
            self.desc_input,
            table_preview_splitter,
        ):
            right_layout.addWidget(widget)

        splitter.addWidget(right_panel)
        window_width = self.width()
        splitter.setSizes([int(window_width * 0.3), int(window_width * 0.7)])

        # After all UI elements are created, show save selection dialog
        if not skip_initial_load:
            # Use QTimer to show dialog after window is shown
            QTimer.singleShot(0, self.show_initial_save_dialog)

        self.showMaximized()

    def setup_menu_bar(self):
        """Set up the application menu bar"""
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("File")

        new_action = QAction("New List", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(lambda: self.clear_list(add_category=True))

        open_action = QAction("Open List...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.show_list_selection)

        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.auto_save)

        export_action = QAction("Export...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_list)

        import_action = QAction("Import...", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self.import_list)

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)

        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        file_menu.addAction(save_action)
        file_menu.addAction(export_action)
        file_menu.addAction(import_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = menubar.addMenu("Edit")

        self.undo_action = QAction("Undo", self)
        self.undo_action.setShortcut("Ctrl+Z")
        self.undo_action.triggered.connect(self.undo)
        self.undo_action.setEnabled(False)

        self.redo_action = QAction("Redo", self)
        self.redo_action.setShortcut("Ctrl+Y")
        self.redo_action.triggered.connect(self.redo)
        self.redo_action.setEnabled(False)

        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)

        # View Menu
        view_menu = menubar.addMenu("View")

        expand_all_action = QAction("Expand All", self)
        expand_all_action.triggered.connect(lambda: self.expand_collapse_all(True))

        collapse_all_action = QAction("Collapse All", self)
        collapse_all_action.triggered.connect(lambda: self.expand_collapse_all(False))

        collapse_empty_action = QAction("Collapse Empty Categories", self)
        collapse_empty_action.triggered.connect(self.collapse_empty_categories)

        view_menu.addAction(expand_all_action)
        view_menu.addAction(collapse_all_action)
        view_menu.addAction(collapse_empty_action)
        view_menu.addSeparator()

    def show_initial_save_dialog(self):
        """Show save selection dialog for initial load"""
        dialog = SaveSelectionDialog()
        if dialog.exec():
            selected = dialog.get_selected()
            if selected:
                self.load_from_save(selected)
            else:
                # Only add new category if we're creating a new list
                self.clear_list(add_category=True)

    def get_safe_filename(self):
        """Convert title to safe filename"""
        title = self.list_title_input.text().split("|")[0].strip()
        return "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).rstrip()

    def auto_save(self):
        """Automatically save the current state"""
        if not self.auto_save_enabled or self.loading_list:
            log("Skipping auto-save", "DEBUG")
            return

        if not self.save_id:
            self.save_id = str(uuid.uuid4())

        data = self.tree_to_dict()
        if data:
            save_path = os.path.join("saves", f"{self.save_id}.json.gz")
            with gzip.open(save_path, "wt", encoding="utf-8") as f:
                json.dump(data, f)
            log(f"Saved list to {save_path}", "INFO")

    def on_title_changed(self):
        """Handle title changes"""
        if not self.loading_list:
            self.auto_save()

    def load_from_save(self, save_id):
        """Load data from a saved file"""
        try:
            save_path = os.path.join("saves", f"{save_id}.json.gz")
            self.loading_list = True
            self.save_id = save_id  # Store the save ID

            # Clear undo/redo stacks before loading new data
            self.undo_stack.clear()
            self.redo_stack.clear()

            with gzip.open(save_path, "rt", encoding="utf-8") as f:
                data = json.load(f)
                self.clear_list(add_category=False)
                self.load_tree_data(data)
                self.update_preview()

            self.loading_list = False

            # Force complete UI update and resize
            QApplication.processEvents()
            QTimer.singleShot(100, lambda: self._finish_table_resize())

        except Exception as e:
            self.loading_list = False
            log(f"Error loading save: {e}", "ERROR")

    def _finish_table_resize(self):
        """Helper method to finish table resizing"""
        self.table_widget.clearSpans()  # Clear existing spans
        self.update_table(self.tree_to_dict())  # Rebuild table completely
        self.table_widget.resizeRowsToContents()
        self.adjust_table_columns()

    def execute_command(self, command):
        """Execute a command and add it to the undo stack"""
        command.do()
        self.undo_stack.append(command)
        self.redo_stack.clear()
        self.update_preview()
        self.auto_save()
        # Update action states
        self.undo_action.setEnabled(True)
        self.redo_action.setEnabled(False)

    def undo(self):
        """Undo the last command"""
        if self.undo_stack:
            command = self.undo_stack.pop()
            command.undo()
            self.redo_stack.append(command)
            self.update_preview()
            self.auto_save()
            # Update action states
            self.undo_action.setEnabled(bool(self.undo_stack))
            self.redo_action.setEnabled(True)

    def redo(self):
        """Redo the last undone command"""
        if self.redo_stack:
            command = self.redo_stack.pop()
            command.do()
            self.undo_stack.append(command)
            self.update_preview()
            self.auto_save()
            # Update action states
            self.undo_action.setEnabled(True)
            self.redo_action.setEnabled(bool(self.redo_stack))

    def add_category(self):
        item = QTreeWidgetItem()
        item.setText(0, "New Category")
        item.setData(0, Qt.ItemDataRole.UserRole + 2, "category")
        command = TreeCommand("Add Category", self.tree, "add", item)
        self.execute_command(command)
        self.tree.setCurrentItem(item)

    def add_subcategory(self):
        current = self.tree.currentItem()
        if current:
            item = QTreeWidgetItem()
            item.setText(0, "New Subcategory")
            item.setData(0, Qt.ItemDataRole.UserRole + 2, "subcategory")
            command = TreeCommand("Add Subcategory", self.tree, "add", item, current)
            self.execute_command(command)
            current.setExpanded(True)
            self.tree.setCurrentItem(item)

    def add_item(self):
        current = self.tree.currentItem()
        if current:
            item = QTreeWidgetItem()
            item.setText(0, "New Item")
            item.setData(0, Qt.ItemDataRole.UserRole, "")
            item.setData(0, Qt.ItemDataRole.UserRole + 2, "item")
            command = TreeCommand("Add Item", self.tree, "add", item, current)
            self.execute_command(command)
            current.setExpanded(True)
            self.tree.setCurrentItem(item)

    def remove_selected(self):
        current = self.tree.currentItem()
        if current:
            parent = current.parent()
            command = TreeCommand("Remove Item", self.tree, "remove", current, parent)
            self.execute_command(command)

    def update_button_states(self, current):
        """Update button states based on selected item type"""
        if not current:
            # No selection - disable all add buttons
            self.add_category_btn.setEnabled(True)
            self.add_subcategory_btn.setEnabled(True)
            self.add_item_btn.setEnabled(True)
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
            # Only show and enable description for items
            item_type = current.data(0, Qt.ItemDataRole.UserRole + 2)
            is_item = item_type == "item"
            self.desc_label.setVisible(is_item)
            self.desc_input.setVisible(is_item)
            self.desc_input.setEnabled(is_item)
            if is_item:
                self.desc_input.blockSignals(True)
                self.desc_input.setText(current.data(0, Qt.ItemDataRole.UserRole) or "")
                self.desc_input.blockSignals(False)
                self.desc_input.textChanged.connect(lambda: self.update_description(current))
            else:
                self.desc_input.clear()

            # Enable options only for subcategories and categories
            self.options_btn.setEnabled(item_type in ("subcategory", "category"))
        else:
            self.title_input.clear()
            self.desc_input.clear()
            self.options_btn.setEnabled(False)

        self.update_button_states(current)
        self.update_move_buttons()

    def update_description(self, item):
        """Update description and auto-save"""
        if item and item.childCount() == 0:
            old_data = {"text": item.text(0), "description": item.data(0, Qt.ItemDataRole.UserRole)}
            new_data = {"text": item.text(0), "description": self.desc_input.toPlainText()}
            command = TreeCommand("Modify Description", self.tree, "modify", item, old_data=old_data, new_data=new_data)
            self.execute_command(command)

    def update_selected_item(self):
        """Update title and auto-save"""
        current = self.tree.currentItem()
        if current:
            old_data = {"text": current.text(0), "description": current.data(0, Qt.ItemDataRole.UserRole)}
            new_data = {"text": self.title_input.text(), "description": current.data(0, Qt.ItemDataRole.UserRole)}
            command = TreeCommand("Modify Item", self.tree, "modify", current, old_data=old_data, new_data=new_data)
            self.execute_command(command)

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

            # Update table with the organized data
            self.update_table(data)

            builder = ManualListBuilder(title, data, collapsible=collapsible)
            self.preview.setText(builder.build())

    def resizeEvent(self, event):
        """Handle window resize events"""
        super().resizeEvent(event)
        self.adjust_table_columns()

    def adjust_table_columns(self):
        """Adjust table columns to maintain proportions"""
        if self.table_widget.columnCount() == 0:
            return

        total_width = self.table_widget.viewport().width() - 2  # Account for borders
        remaining_width = total_width

        # Set all columns except the last one according to proportions
        for i in range(self.table_widget.columnCount() - 1):
            # Skip if we don't have a proportion defined for this column
            if i >= len(self.column_proportions):
                break

            width = int(total_width * (self.column_proportions[i] / 100.0))
            self.table_widget.setColumnWidth(i, width)
            remaining_width -= width

        # Give remaining width to the last column
        last_col = self.table_widget.columnCount() - 1
        if last_col >= 0:
            self.table_widget.setColumnWidth(last_col, remaining_width)

    def update_table(self, data):
        """Update the table widget with the organized data"""
        self.table_widget.clear()
        rows = []
        max_depth = 0
        category_items = {}
        subcategory_spans = {}

        def count_items(items, category="", subcategory_path=None, depth_options=None, current_depth=0):
            nonlocal max_depth
            if subcategory_path is None:
                subcategory_path = []
            if depth_options is None:
                depth_options = []

            total_items = 0
            total_extra_depth = sum(depth_options)
            effective_depth = current_depth + total_extra_depth
            max_depth = max(max_depth, effective_depth)

            for key, value in items.items():
                if key in ["__metadata", "__options"]:
                    continue

                if isinstance(value, dict):
                    item_type = value.get("__metadata", {}).get("type", "")
                    options = value.get("__options", {})
                    extra_depth = options.get("extra_depth", 0)
                    current_depth_options = depth_options.copy()

                    if item_type == "category":
                        # For categories, start new depth_options list with its extra_depth
                        current_depth_options = [extra_depth]
                        sub_items = count_items(value, key, [], current_depth_options, 1)
                        category_items[key] = sub_items
                        total_items += sub_items
                    elif item_type == "subcategory":
                        # For subcategories, append extra_depth to the existing options
                        current_depth_options.append(extra_depth)
                        new_path = subcategory_path + [key]
                        # Increment depth by 1 plus the sum of all extra depths encountered
                        next_depth = current_depth + 1
                        sub_items = count_items(value, category, new_path, current_depth_options, next_depth)
                        path_tuple = (category, tuple(new_path))
                        subcategory_spans[path_tuple] = sub_items
                        total_items += sub_items
                    elif item_type == "item":
                        total_items += 1
                        description = value.get("description", "")
                        # Store item at current depth
                        rows.append([category, subcategory_path, key, description, depth_options, current_depth])

            return total_items

        # Process the data and count items
        count_items(data)

        # Create headers based on max depth
        headers = ["Category"]
        for i in range(max_depth + 1):
            headers.append(f"Level {i + 1}")

        # Update layout
        subcategory_width = 15 * max_depth  # Allocate 15% for each level
        remaining_width = 100 - subcategory_width
        self.column_proportions = [
            20,  # Category
            *[15] * max_depth,  # All levels
            remaining_width,  # Description
        ]

        # Set up the table
        self.table_widget.setRowCount(len(rows))
        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setHorizontalHeaderLabels(headers)

        # Track processed spans
        processed_categories = set()
        processed_subcategories = {i: set() for i in range(max_depth)}

        # Fill the table
        for i, row in enumerate(rows):
            category, subcategory_path, item, description, depth_options, item_depth = row
            current_col = 1

            # Handle category (always in first column)
            if category and i not in processed_categories:
                span = category_items.get(category, 1)
                if span > 1:
                    self.table_widget.setSpan(i, 0, span, 1)
                cat_item = QTableWidgetItem(category)
                cat_item.setFlags(cat_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table_widget.setItem(i, 0, cat_item)
                processed_categories.add(i)

                # Add empty columns for category extra_depth
                category_extra_depth = depth_options[0] if depth_options else 0
                for _ in range(category_extra_depth):
                    empty_item = QTableWidgetItem("")
                    empty_item.setFlags(empty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.table_widget.setItem(i, current_col, empty_item)
                    current_col += 1

            # Handle subcategories
            depth_used = 0
            for depth, subcat in enumerate(subcategory_path):
                col = current_col
                path_tuple = (category, tuple(subcategory_path[: depth + 1]))
                span_key = (i, depth_used)

                if span_key not in processed_subcategories[depth_used]:
                    span = subcategory_spans.get(path_tuple, 1)
                    if span > 1:
                        self.table_widget.setSpan(i, col, span, 1)
                        for j in range(i, i + span):
                            processed_subcategories[depth_used].add((j, depth_used))

                    subcat_item = QTableWidgetItem(subcat)
                    subcat_item.setFlags(subcat_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.table_widget.setItem(i, col, subcat_item)

                # Add empty columns for subcategory extra_depth
                if depth + 1 < len(depth_options):
                    extra_depth = depth_options[depth + 1]
                    for _ in range(extra_depth):
                        current_col += 1
                        empty_item = QTableWidgetItem("")
                        empty_item.setFlags(empty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        self.table_widget.setItem(i, current_col, empty_item)

                current_col += 1
                depth_used += 1

            # Add item in its designated column and description in the next column
            if item:
                item_widget = QTableWidgetItem(item)
                item_widget.setFlags(item_widget.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table_widget.setItem(i, current_col, item_widget)

                # Place description in the next column
                desc_widget = QTableWidgetItem(description)
                desc_widget.setFlags(desc_widget.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table_widget.setItem(i, current_col + 1, desc_widget)

            # Clear any remaining columns in this row
            for col in range(current_col + 2, self.table_widget.columnCount()):
                empty_item = QTableWidgetItem("")
                empty_item.setFlags(empty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table_widget.setItem(i, col, empty_item)

        # Adjust table appearance
        self.table_widget.resizeRowsToContents()
        self.adjust_table_columns()

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
        self._move_item("up")

    def move_item_down(self):
        self._move_item("down")

    def _move_item(self, direction):
        current = self.tree.currentItem()
        if not current:
            return

        parent = current.parent() or self.tree.invisibleRootItem()
        current_index = parent.indexOfChild(current)
        new_index = current_index - 1 if direction == "up" else current_index + 1

        if 0 <= new_index < parent.childCount():
            command = TreeCommand(
                "Move Item",
                self.tree,
                "move",
                current,
                old_data={"index": current_index},
                new_data={"index": new_index},
            )
            self.execute_command(command)
            self.tree.setCurrentItem(current)
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

    def clear_list(self, add_category=False):
        """Clear all current list data and optionally add empty category"""
        # Temporarily disable auto-save
        self.auto_save_enabled = False

        self.tree.clear()
        self.list_title_input.setText("List of Items")
        self.list_title_input.setProperty("titleData", None)
        self.collapsible_checkbox.setChecked(False)

        if add_category:
            # Generate new unique ID for the list
            self.save_id = str(uuid.uuid4())

            # Add empty category
            item = QTreeWidgetItem(self.tree)
            item.setText(0, "New Category")
            item.setData(0, Qt.ItemDataRole.UserRole + 2, "category")
            self.tree.setCurrentItem(item)

            self.list_title_input.setText("New List")

        # Clear undo/redo stacks
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.undo_action.setEnabled(False)
        self.redo_action.setEnabled(False)

        # Re-enable auto-save after clearing
        self.auto_save_enabled = True

        self.update_preview()

    def show_list_selection(self):
        """Show the list selection dialog"""
        dialog = SaveSelectionDialog(self)
        if dialog.exec():
            selected = dialog.get_selected()
            if selected:
                self.load_from_save(selected)
            else:
                # Disable auto-save before creating new list
                self.auto_save_enabled = False
                self.clear_list(add_category=True)
                self.auto_save_enabled = True

    def show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item:
            background_menu = QMenu()

            # Add new category action
            add_category_action = background_menu.addAction("Add Category")
            add_category_action.triggered.connect(self.add_category)

            # Add expand/collapse all actions
            background_menu.addSeparator()
            expand_all_action = background_menu.addAction("Expand All")
            expand_all_action.triggered.connect(lambda: self.expand_collapse_all(True))
            collapse_all_action = background_menu.addAction("Collapse All")
            collapse_all_action.triggered.connect(lambda: self.expand_collapse_all(False))

            # Add collapse empty categories option
            background_menu.addSeparator()
            collapse_empty_action = background_menu.addAction("Collapse Empty Categories")
            collapse_empty_action.triggered.connect(self.collapse_empty_categories)

            background_menu.exec(self.tree.viewport().mapToGlobal(position))
            return

        menu = QMenu()
        item_type = item.data(0, Qt.ItemDataRole.UserRole + 2)

        # Add type-specific actions
        if item_type in ("category", "subcategory"):
            # Expand/collapse actions
            expand_action = menu.addAction("Expand")
            expand_action.triggered.connect(lambda: item.setExpanded(True))
            collapse_action = menu.addAction("Collapse")
            collapse_action.triggered.connect(lambda: item.setExpanded(False))

            menu.addSeparator()
            expand_all_action = menu.addAction("Expand All")
            expand_all_action.triggered.connect(lambda: self.expand_collapse_recursive(item, True))
            collapse_all_action = menu.addAction("Collapse All")
            collapse_all_action.triggered.connect(lambda: self.expand_collapse_recursive(item, False))

            menu.addSeparator()
            # Add actions
            add_menu = menu.addMenu("Add")
            if item_type == "category":
                add_category_action = add_menu.addAction("Category")
                add_category_action.triggered.connect(self.add_category)
            add_subcategory_action = add_menu.addAction("Subcategory")
            add_subcategory_action.triggered.connect(self.add_subcategory)
            add_item_action = add_menu.addAction("Item")
            add_item_action.triggered.connect(self.add_item)

        # Movement actions for all types based on current position
        menu.addSeparator()
        move_menu = menu.addMenu("Move")

        # Get movement possibilities
        parent = item.parent() or self.tree.invisibleRootItem()
        current_index = parent.indexOfChild(item)
        can_move_up = current_index > 0
        can_move_down = current_index < parent.childCount() - 1

        # Only show enabled move actions if they're possible
        move_up_action = move_menu.addAction("Move Up")
        move_up_action.triggered.connect(self.move_item_up)
        move_up_action.setEnabled(can_move_up)

        move_down_action = move_menu.addAction("Move Down")
        move_down_action.triggered.connect(self.move_item_down)
        move_down_action.setEnabled(can_move_down)

        # Delete action for all types
        menu.addSeparator()
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(self.remove_selected)

        menu.exec(self.tree.viewport().mapToGlobal(position))

    def expand_collapse_all(self, expand=True):
        """Expand or collapse all items in the tree"""
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            self.expand_collapse_recursive(root.child(i), expand)

    def sort_tree(self, ascending=True):
        """Sort the tree items alphabetically"""
        root = self.tree.invisibleRootItem()
        self._sort_items(root, ascending)
        self.update_preview()
        self.auto_save()

    def _sort_items(self, parent, ascending=True):
        """Recursively sort items within a parent item"""
        # Get all children
        items = []
        for i in range(parent.childCount()):
            items.append(parent.child(i))

        # Sort items by text
        items.sort(key=lambda x: x.text(0).lower(), reverse=not ascending)

        # Remove and re-add items in sorted order
        for item in items:
            parent.removeChild(item)
            parent.addChild(item)
            # Recursively sort children
            self._sort_items(item, ascending)

    def collapse_empty_categories(self):
        """Collapse categories and subcategories that have no items"""
        root = self.tree.invisibleRootItem()
        self._collapse_if_empty(root)

    def _collapse_if_empty(self, parent):
        """Recursively check and collapse empty categories"""
        has_items = False

        # Check all children
        for i in range(parent.childCount()):
            child = parent.child(i)
            child_type = child.data(0, Qt.ItemDataRole.UserRole + 2)

            if child_type == "item":
                has_items = True
            else:
                # Recursively check child categories/subcategories
                if self._collapse_if_empty(child):
                    has_items = True

        # Collapse if no items found
        if not has_items and parent != self.tree.invisibleRootItem():
            parent.setExpanded(False)

        return has_items

    def expand_collapse_recursive(self, item, expand=True):
        """Recursively expand or collapse an item and all its children"""
        item.setExpanded(expand)
        for i in range(item.childCount()):
            self.expand_collapse_recursive(item.child(i), expand)


if __name__ == "__main__":
    app = QApplication([])
    myappid = "mycompany.myproduct.subproduct.version"  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    qdarktheme.setup_theme()
    window = WikiListBuilder(skip_initial_load=True)
    window.show()
    QTimer.singleShot(100, window.show_initial_save_dialog)
    app.exec()
