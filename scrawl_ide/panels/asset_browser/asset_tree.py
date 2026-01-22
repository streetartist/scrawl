"""
Asset Tree View

File tree browser for project assets.
"""

import os
from PySide6.QtWidgets import (
    QTreeView, QFileSystemModel, QMenu, QMessageBox,
    QInputDialog
)
from PySide6.QtCore import Qt, Signal, QDir, QModelIndex
from PySide6.QtGui import QAction
from typing import Optional

from core.i18n import tr


class AssetTreeView(QTreeView):
    """File tree view for browsing project assets."""

    file_selected = Signal(str)  # file path
    file_double_clicked = Signal(str)  # file path
    file_dropped = Signal(str, str)  # source, destination

    def __init__(self, parent=None):
        super().__init__(parent)

        self._root_path: Optional[str] = None
        self._model = QFileSystemModel(self)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the tree view."""
        # Configure model
        self._model.setRootPath("")

        # Filter for common asset types
        self._model.setNameFilters([
            "*.py", "*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp",
            "*.wav", "*.mp3", "*.ogg", "*.json", "*.txt"
        ])
        self._model.setNameFilterDisables(False)

        self.setModel(self._model)

        # Hide unnecessary columns
        self.setHeaderHidden(False)
        self.hideColumn(1)  # Size
        self.hideColumn(2)  # Type
        self.hideColumn(3)  # Date modified

        # Configure view
        self.setAnimated(True)
        self.setIndentation(20)
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.AscendingOrder)

        # Enable drag and drop
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QTreeView.DragDrop)

        # Context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # Connect signals
        self.clicked.connect(self._on_clicked)
        self.doubleClicked.connect(self._on_double_clicked)

    def set_root_path(self, path: str):
        """Set the root path for the file browser."""
        if os.path.exists(path):
            self._root_path = path
            self._model.setRootPath(path)
            self.setRootIndex(self._model.index(path))

    def get_selected_path(self) -> Optional[str]:
        """Get the currently selected file path."""
        indexes = self.selectedIndexes()
        if indexes:
            return self._model.filePath(indexes[0])
        return None

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

    def _show_context_menu(self, pos):
        """Show context menu."""
        index = self.indexAt(pos)
        menu = QMenu(self)

        if index.isValid():
            path = self._model.filePath(index)
            is_dir = os.path.isdir(path)

            if is_dir:
                # Directory actions
                new_file_action = QAction(tr("asset.new_script"), self)
                new_file_action.triggered.connect(lambda: self._new_file(path, ".py"))
                menu.addAction(new_file_action)

                new_folder_action = QAction(tr("asset.new_folder"), self)
                new_folder_action.triggered.connect(lambda: self._new_folder(path))
                menu.addAction(new_folder_action)

                menu.addSeparator()

            # Common actions
            rename_action = QAction(tr("asset.rename"), self)
            rename_action.triggered.connect(lambda: self._rename(path))
            menu.addAction(rename_action)

            delete_action = QAction(tr("asset.delete"), self)
            delete_action.triggered.connect(lambda: self._delete(path))
            menu.addAction(delete_action)

            menu.addSeparator()

            # Open in explorer
            reveal_action = QAction(tr("asset.reveal"), self)
            reveal_action.triggered.connect(lambda: self._reveal_in_explorer(path))
            menu.addAction(reveal_action)

        else:
            # Root context
            if self._root_path:
                new_file_action = QAction(tr("asset.new_script"), self)
                new_file_action.triggered.connect(
                    lambda: self._new_file(self._root_path, ".py")
                )
                menu.addAction(new_file_action)

                new_folder_action = QAction(tr("asset.new_folder"), self)
                new_folder_action.triggered.connect(
                    lambda: self._new_folder(self._root_path)
                )
                menu.addAction(new_folder_action)

        menu.exec_(self.mapToGlobal(pos))

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
                self.setCurrentIndex(index)
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
