"""
Asset Tree View

File tree browser for project assets with custom icons and toolbar.
"""

import os
from PySide6.QtWidgets import (
    QTreeView, QFileSystemModel, QMenu, QMessageBox,
    QInputDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QToolButton, QFrame,
    QStyledItemDelegate, QStyle, QApplication
)
from PySide6.QtCore import Qt, Signal, QDir, QModelIndex, QSize, QFileInfo
from PySide6.QtGui import QAction, QIcon, QPainter, QColor, QPen, QFont, QPixmap
from typing import Optional

from core.i18n import tr


class FileIconProvider:
    """Provides custom icons for different file types."""

    # File type colors
    COLORS = {
        'folder': '#FFB74D',      # Orange
        'python': '#4CAF50',      # Green
        'image': '#E91E63',       # Pink
        'audio': '#9C27B0',       # Purple
        'json': '#FF9800',        # Orange
        'text': '#607D8B',        # Blue Grey
        'default': '#90A4AE',     # Grey
    }

    # File type icons (emoji-style)
    ICONS = {
        'folder': '📁',
        'python': '🐍',
        'image': '🖼️',
        'audio': '🎵',
        'json': '📋',
        'text': '📄',
        'default': '📄',
    }

    @classmethod
    def get_file_type(cls, path: str) -> str:
        """Get the file type category."""
        if os.path.isdir(path):
            return 'folder'

        ext = os.path.splitext(path)[1].lower()

        if ext == '.py':
            return 'python'
        elif ext in ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg'):
            return 'image'
        elif ext in ('.wav', '.mp3', '.ogg'):
            return 'audio'
        elif ext == '.json':
            return 'json'
        elif ext in ('.txt', '.md'):
            return 'text'
        else:
            return 'default'

    @classmethod
    def get_color(cls, path: str) -> str:
        """Get the color for a file type."""
        file_type = cls.get_file_type(path)
        return cls.COLORS.get(file_type, cls.COLORS['default'])

    @classmethod
    def get_icon_text(cls, path: str) -> str:
        """Get the icon emoji for a file type."""
        file_type = cls.get_file_type(path)
        return cls.ICONS.get(file_type, cls.ICONS['default'])


class AssetItemDelegate(QStyledItemDelegate):
    """Custom delegate for rendering asset items with icons and colors."""

    def __init__(self, model: QFileSystemModel, parent=None):
        super().__init__(parent)
        self._model = model

    def paint(self, painter: QPainter, option, index: QModelIndex):
        """Paint the item with custom styling."""
        painter.save()

        # Get file path
        path = self._model.filePath(index)
        file_type = FileIconProvider.get_file_type(path)
        color = FileIconProvider.get_color(path)

        # Draw selection background
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor('#37474F'))
        elif option.state & QStyle.State_MouseOver:
            painter.fillRect(option.rect, QColor('#263238'))

        # Draw icon indicator (colored dot)
        icon_rect = option.rect.adjusted(4, 0, 0, 0)
        icon_rect.setWidth(16)

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(color))
        painter.setPen(Qt.NoPen)

        dot_size = 8
        dot_y = icon_rect.center().y() - dot_size // 2
        painter.drawEllipse(icon_rect.x() + 4, dot_y, dot_size, dot_size)

        # Draw text
        text_rect = option.rect.adjusted(24, 0, 0, 0)
        painter.setPen(QColor('#E0E0E0'))

        font = painter.font()
        if os.path.isdir(path):
            font.setBold(True)
        painter.setFont(font)

        text = index.data(Qt.DisplayRole)
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, text)

        painter.restore()

    def sizeHint(self, option, index):
        """Return the size hint for items."""
        size = super().sizeHint(option, index)
        size.setHeight(max(size.height(), 26))
        return size


class AssetTreeView(QWidget):
    """File tree view for browsing project assets with toolbar."""

    file_selected = Signal(str)  # file path
    file_double_clicked = Signal(str)  # file path
    file_dropped = Signal(str, str)  # source, destination

    def __init__(self, parent=None):
        super().__init__(parent)

        self._root_path: Optional[str] = None
        self._model = QFileSystemModel(self)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Path bar
        self._path_bar = self._create_path_bar()
        layout.addWidget(self._path_bar)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Search/filter bar
        self._search_bar = self._create_search_bar()
        layout.addWidget(self._search_bar)

        # Tree view
        self._tree = QTreeView()
        self._setup_tree()
        layout.addWidget(self._tree)

        # Apply styling
        self._apply_styles()

    def _create_toolbar(self) -> QWidget:
        """Create the toolbar with action buttons."""
        toolbar = QFrame()
        toolbar.setObjectName("AssetToolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(4, 4, 4, 4)
        toolbar_layout.setSpacing(2)

        # New file button
        self._new_file_btn = QToolButton()
        self._new_file_btn.setText("📄")
        self._new_file_btn.setToolTip(tr("asset.new_script"))
        self._new_file_btn.clicked.connect(self._on_new_file)
        toolbar_layout.addWidget(self._new_file_btn)

        # New folder button
        self._new_folder_btn = QToolButton()
        self._new_folder_btn.setText("📁")
        self._new_folder_btn.setToolTip(tr("asset.new_folder"))
        self._new_folder_btn.clicked.connect(self._on_new_folder)
        toolbar_layout.addWidget(self._new_folder_btn)

        toolbar_layout.addSpacing(8)

        # Refresh button
        self._refresh_btn = QToolButton()
        self._refresh_btn.setText("🔄")
        self._refresh_btn.setToolTip("Refresh")
        self._refresh_btn.clicked.connect(self._refresh)
        toolbar_layout.addWidget(self._refresh_btn)

        # Reveal in explorer button
        self._reveal_btn = QToolButton()
        self._reveal_btn.setText("📂")
        self._reveal_btn.setToolTip(tr("asset.reveal"))
        self._reveal_btn.clicked.connect(self._on_reveal_selected)
        toolbar_layout.addWidget(self._reveal_btn)

        toolbar_layout.addStretch()

        return toolbar

    def _create_path_bar(self) -> QWidget:
        """Create the path input bar."""
        path_frame = QFrame()
        path_frame.setObjectName("AssetPathBar")
        path_layout = QHBoxLayout(path_frame)
        path_layout.setContentsMargins(4, 2, 4, 2)
        path_layout.setSpacing(4)

        # Path input
        self._path_input = QLineEdit()
        self._path_input.setObjectName("PathInput")
        self._path_input.setPlaceholderText("Project path...")
        self._path_input.returnPressed.connect(self._on_path_entered)
        path_layout.addWidget(self._path_input)

        # Browse button
        browse_btn = QToolButton()
        browse_btn.setText("...")
        browse_btn.setToolTip("Browse folder")
        browse_btn.clicked.connect(self._on_browse_folder)
        path_layout.addWidget(browse_btn)

        return path_frame

    def _create_search_bar(self) -> QWidget:
        """Create the search/filter bar."""
        search_frame = QFrame()
        search_frame.setObjectName("AssetSearchBar")
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(4, 2, 4, 2)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍 Filter...")
        self._search_input.textChanged.connect(self._on_filter_changed)
        self._search_input.setClearButtonEnabled(True)
        search_layout.addWidget(self._search_input)

        return search_frame

    def _setup_tree(self):
        """Set up the tree view."""
        # Configure model
        self._model.setRootPath("")

        # Filter for common asset types
        self._model.setNameFilters([
            "*.py", "*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp", "*.svg",
            "*.wav", "*.mp3", "*.ogg", "*.json", "*.txt", "*.md"
        ])
        self._model.setNameFilterDisables(False)

        self._tree.setModel(self._model)

        # Set custom delegate
        self._delegate = AssetItemDelegate(self._model, self._tree)
        self._tree.setItemDelegate(self._delegate)

        # Hide unnecessary columns
        self._tree.setHeaderHidden(True)
        self._tree.hideColumn(1)  # Size
        self._tree.hideColumn(2)  # Type
        self._tree.hideColumn(3)  # Date modified

        # Configure view
        self._tree.setAnimated(True)
        self._tree.setIndentation(16)
        self._tree.setSortingEnabled(True)
        self._tree.sortByColumn(0, Qt.AscendingOrder)
        self._tree.setUniformRowHeights(True)

        # Enable drag and drop
        self._tree.setDragEnabled(True)
        self._tree.setAcceptDrops(True)
        self._tree.setDropIndicatorShown(True)
        self._tree.setDragDropMode(QTreeView.DragDrop)

        # Context menu
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._show_context_menu)

        # Connect signals
        self._tree.clicked.connect(self._on_clicked)
        self._tree.doubleClicked.connect(self._on_double_clicked)

    def _apply_styles(self):
        """Apply custom styles to the widget."""
        self.setStyleSheet("""
            #AssetPathBar {
                background-color: #263238;
                border-bottom: 1px solid #333;
            }
            #AssetPathBar #PathInput {
                background-color: #1E1E1E;
                border: 1px solid #37474F;
                border-radius: 4px;
                padding: 4px 8px;
                color: #E0E0E0;
                font-size: 11px;
            }
            #AssetPathBar #PathInput:focus {
                border-color: #4FC3F7;
            }
            #AssetPathBar QToolButton {
                background: #37474F;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                color: #E0E0E0;
            }
            #AssetPathBar QToolButton:hover {
                background-color: #455A64;
            }
            #AssetToolbar {
                background-color: #1E1E1E;
                border-bottom: 1px solid #333;
            }
            #AssetToolbar QToolButton {
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 14px;
            }
            #AssetToolbar QToolButton:hover {
                background-color: #37474F;
            }
            #AssetToolbar QToolButton:pressed {
                background-color: #455A64;
            }
            #AssetSearchBar {
                background-color: #1E1E1E;
                border-bottom: 1px solid #333;
            }
            #AssetSearchBar QLineEdit {
                background-color: #263238;
                border: 1px solid #37474F;
                border-radius: 4px;
                padding: 4px 8px;
                color: #E0E0E0;
            }
            #AssetSearchBar QLineEdit:focus {
                border-color: #4FC3F7;
            }
            QTreeView {
                background-color: #1E1E1E;
                border: none;
                outline: none;
            }
            QTreeView::item {
                padding: 2px 0;
            }
            QTreeView::item:hover {
                background-color: #263238;
            }
            QTreeView::item:selected {
                background-color: #37474F;
            }
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings {
                border-image: none;
                image: url(none);
            }
            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings {
                border-image: none;
                image: url(none);
            }
        """)

    def set_root_path(self, path: str):
        """Set the root path for the file browser."""
        if os.path.exists(path):
            self._root_path = path
            self._model.setRootPath(path)
            self._tree.setRootIndex(self._model.index(path))
            # Update path input
            self._path_input.setText(path)

    def get_selected_path(self) -> Optional[str]:
        """Get the currently selected file path."""
        indexes = self._tree.selectedIndexes()
        if indexes:
            return self._model.filePath(indexes[0])
        return None

    def _get_selected_or_root(self) -> str:
        """Get selected directory or root path."""
        path = self.get_selected_path()
        if path:
            if os.path.isfile(path):
                return os.path.dirname(path)
            return path
        return self._root_path or ""

    def _on_clicked(self, index: QModelIndex):
        """Handle item click."""
        path = self._model.filePath(index)
        if os.path.isfile(path):
            self.file_selected.emit(path)

    def _on_double_clicked(self, index: QModelIndex):
        """Handle item double-click."""
        path = self._model.filePath(index)
        if os.path.isfile(path):
            self.file_double_clicked.emit(path)

    def _on_filter_changed(self, text: str):
        """Handle filter text change."""
        if text:
            # Add wildcard pattern
            patterns = [f"*{text}*"]
            self._model.setNameFilters(patterns)
        else:
            # Reset to default filters
            self._model.setNameFilters([
                "*.py", "*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp", "*.svg",
                "*.wav", "*.mp3", "*.ogg", "*.json", "*.txt", "*.md"
            ])

    def _on_new_file(self):
        """Create new file in selected directory."""
        directory = self._get_selected_or_root()
        if directory:
            self._new_file(directory, ".py")

    def _on_new_folder(self):
        """Create new folder in selected directory."""
        directory = self._get_selected_or_root()
        if directory:
            self._new_folder(directory)

    def _on_reveal_selected(self):
        """Reveal selected item in explorer."""
        path = self.get_selected_path() or self._root_path
        if path:
            self._reveal_in_explorer(path)

    def _on_path_entered(self):
        """Handle path input enter pressed."""
        path = self._path_input.text().strip()
        if path and os.path.isdir(path):
            self.set_root_path(path)
        elif path and os.path.isfile(path):
            # If it's a file, navigate to its directory
            self.set_root_path(os.path.dirname(path))
        else:
            # Reset to current root path if invalid
            if self._root_path:
                self._path_input.setText(self._root_path)

    def _on_browse_folder(self):
        """Open folder browser dialog."""
        from PySide6.QtWidgets import QFileDialog
        start_dir = self._root_path or ""
        path = QFileDialog.getExistingDirectory(
            self, "Select Folder", start_dir
        )
        if path:
            self.set_root_path(path)

    def _refresh(self):
        """Refresh the file tree."""
        if self._root_path:
            self._model.setRootPath("")
            self._model.setRootPath(self._root_path)
            self._tree.setRootIndex(self._model.index(self._root_path))

    def _show_context_menu(self, pos):
        """Show context menu."""
        index = self._tree.indexAt(pos)
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2D2D2D;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px 6px 12px;
                border-radius: 2px;
            }
            QMenu::item:selected {
                background-color: #37474F;
            }
            QMenu::separator {
                height: 1px;
                background-color: #404040;
                margin: 4px 8px;
            }
        """)

        if index.isValid():
            path = self._model.filePath(index)
            is_dir = os.path.isdir(path)

            if is_dir:
                # Directory actions
                new_file_action = QAction("📄 " + tr("asset.new_script"), self)
                new_file_action.triggered.connect(lambda: self._new_file(path, ".py"))
                menu.addAction(new_file_action)

                new_folder_action = QAction("📁 " + tr("asset.new_folder"), self)
                new_folder_action.triggered.connect(lambda: self._new_folder(path))
                menu.addAction(new_folder_action)

                menu.addSeparator()

            # Common actions
            rename_action = QAction("✏️ " + tr("asset.rename"), self)
            rename_action.triggered.connect(lambda: self._rename(path))
            menu.addAction(rename_action)

            delete_action = QAction("🗑️ " + tr("asset.delete"), self)
            delete_action.triggered.connect(lambda: self._delete(path))
            menu.addAction(delete_action)

            menu.addSeparator()

            # Open in explorer
            reveal_action = QAction("📂 " + tr("asset.reveal"), self)
            reveal_action.triggered.connect(lambda: self._reveal_in_explorer(path))
            menu.addAction(reveal_action)

        else:
            # Root context
            if self._root_path:
                new_file_action = QAction("📄 " + tr("asset.new_script"), self)
                new_file_action.triggered.connect(
                    lambda: self._new_file(self._root_path, ".py")
                )
                menu.addAction(new_file_action)

                new_folder_action = QAction("📁 " + tr("asset.new_folder"), self)
                new_folder_action.triggered.connect(
                    lambda: self._new_folder(self._root_path)
                )
                menu.addAction(new_folder_action)

        menu.exec_(self._tree.mapToGlobal(pos))

    def _new_file(self, directory: str, extension: str):
        """Create a new file."""
        name, ok = QInputDialog.getText(
            self, tr("asset.new_file_title"), tr("asset.new_file_prompt")
        )

        if ok and name:
            if not name.endswith(extension):
                name += extension

            path = os.path.join(directory, name)
            if os.path.exists(path):
                QMessageBox.warning(
                    self, tr("dialog.error"),
                    tr("asset.exists_error").format(name=name)
                )
                return

            try:
                with open(path, 'w', encoding='utf-8') as f:
                    if extension == ".py":
                        f.write('"""New script."""\n\n')
                    else:
                        f.write('')

                # Select the new file
                index = self._model.index(path)
                self._tree.setCurrentIndex(index)
                self.file_double_clicked.emit(path)

            except IOError as e:
                QMessageBox.warning(
                    self, tr("dialog.error"),
                    f"Could not create file: {e}"
                )

    def _new_folder(self, parent: str):
        """Create a new folder."""
        name, ok = QInputDialog.getText(
            self, tr("asset.new_folder_title"), tr("asset.new_folder_prompt")
        )

        if ok and name:
            path = os.path.join(parent, name)
            if os.path.exists(path):
                QMessageBox.warning(
                    self, tr("dialog.error"),
                    tr("asset.exists_error").format(name=name)
                )
                return

            try:
                os.makedirs(path)
            except OSError as e:
                QMessageBox.warning(
                    self, tr("dialog.error"),
                    f"Could not create folder: {e}"
                )

    def _rename(self, path: str):
        """Rename a file or folder."""
        old_name = os.path.basename(path)
        new_name, ok = QInputDialog.getText(
            self, tr("asset.rename_title"), tr("asset.rename_prompt"),
            text=old_name
        )

        if ok and new_name and new_name != old_name:
            new_path = os.path.join(os.path.dirname(path), new_name)
            if os.path.exists(new_path):
                QMessageBox.warning(
                    self, tr("dialog.error"),
                    tr("asset.exists_error").format(name=new_name)
                )
                return

            try:
                os.rename(path, new_path)
            except OSError as e:
                QMessageBox.warning(
                    self, tr("dialog.error"),
                    f"Could not rename: {e}"
                )

    def _delete(self, path: str):
        """Delete a file or folder."""
        name = os.path.basename(path)
        is_dir = os.path.isdir(path)
        file_type = tr("asset.type_folder") if is_dir else tr("asset.type_file")

        reply = QMessageBox.question(
            self, tr("asset.delete"),
            tr("asset.delete_confirm").format(type=file_type, name=name),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                if is_dir:
                    import shutil
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except OSError as e:
                QMessageBox.warning(
                    self, tr("dialog.error"),
                    f"Could not delete: {e}"
                )

    def _reveal_in_explorer(self, path: str):
        """Open the file location in the system file explorer."""
        import subprocess
        import sys

        if sys.platform == 'win32':
            if os.path.isfile(path):
                subprocess.run(['explorer', '/select,', path])
            else:
                subprocess.run(['explorer', path])
        elif sys.platform == 'darwin':
            subprocess.run(['open', '-R', path])
        else:
            subprocess.run(['xdg-open', os.path.dirname(path)])
