import sys
import os
from typing import Optional, List, Dict

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor, QTextCharFormat, QSyntaxHighlighter, QPalette
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QListWidget, QListWidgetItem, QPushButton, QComboBox,
    QLabel, QLineEdit, QTextEdit, QSplitter, QMessageBox, QFileDialog,
    QFrame, QStatusBar, QGroupBox
)

import git_service


class DiffHighlighter(QSyntaxHighlighter):
    """Sintaxis de colores y negritas para el visor de Diff."""
    def __init__(self, document):
        super().__init__(document)

        # Formatos
        self.fmt_bold_header = QTextCharFormat()
        self.fmt_bold_header.setForeground(QColor("#e0a800"))  # Amarillo
        self.fmt_bold_header.setFontWeight(QFont.Bold)
        self.fmt_bold_header.setFontPointSize(11)

        self.fmt_add = QTextCharFormat()
        self.fmt_add.setForeground(QColor("#28a745"))  # Verde

        self.fmt_remove = QTextCharFormat()
        self.fmt_remove.setForeground(QColor("#dc3545"))  # Rojo

        self.fmt_hunk = QTextCharFormat()
        self.fmt_hunk.setForeground(QColor("#17a2b8"))  # Cyan

        self.fmt_meta = QTextCharFormat()
        self.fmt_meta.setForeground(QColor("#888888"))  # Gris

    def highlightBlock(self, text: str):
        if (text.startswith("Commit ") or text.startswith("Autor:") or
            text.startswith("Fecha:") or text.startswith("Mensaje:") or
            text.startswith("Descripción:") or text.startswith("Cambios no preparados:") or
            text.startswith("Cambios preparados")):
            self.setFormat(0, len(text), self.fmt_bold_header)
        elif text.startswith("+") and not text.startswith("+++"):
            self.setFormat(0, len(text), self.fmt_add)
        elif text.startswith("-") and not text.startswith("---"):
            self.setFormat(0, len(text), self.fmt_remove)
        elif text.startswith("@@"):
            self.setFormat(0, len(text), self.fmt_hunk)
        elif (text.startswith("diff --git") or text.startswith("index ") or
              text.startswith("---") or text.startswith("+++")):
            self.setFormat(0, len(text), self.fmt_meta)


class GitGuiPySideApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gestor de Repositorio Git (PySide6 + PyGit2)")
        self.resize(1150, 720)
        self.setMinimumSize(950, 600)

        self.current_repo: Optional[str] = None
        self.recent_repos: List[str] = git_service.load_recent_repos()

        self._apply_dark_theme()
        self._init_ui()

        # Cargar directorio por defecto
        default_dir = os.getcwd()
        if git_service.is_git_repo(default_dir):
            self.set_repository(default_dir)
        elif self.recent_repos:
            self.set_repository(self.recent_repos[0])
        else:
            self.statusBar().showMessage("Por favor, selecciona un repositorio Git para comenzar.")

    def _apply_dark_theme(self):
        """Aplica un tema oscuro moderno con tipografía clara y legible."""
        app = QApplication.instance()
        app.setStyle("Fusion")

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#1e1e1e"))
        palette.setColor(QPalette.WindowText, QColor("#ffffff"))
        palette.setColor(QPalette.Base, QColor("#252526"))
        palette.setColor(QPalette.AlternateBase, QColor("#2d2d30"))
        palette.setColor(QPalette.ToolTipBase, QColor("#ffffff"))
        palette.setColor(QPalette.ToolTipText, QColor("#ffffff"))
        palette.setColor(QPalette.Text, QColor("#f1f1f1"))
        palette.setColor(QPalette.Button, QColor("#333333"))
        palette.setColor(QPalette.ButtonText, QColor("#ffffff"))
        palette.setColor(QPalette.BrightText, QColor("#ff0000"))
        palette.setColor(QPalette.Link, QColor("#007acc"))
        palette.setColor(QPalette.Highlight, QColor("#0e639c"))
        palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))

        app.setPalette(palette)

        # Hoja de estilos global (CSS)
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QTabWidget::pane { border: 1px solid #3c3c3c; background-color: #252526; }
            QTabBar::tab { background: #2d2d30; color: #cccccc; padding: 8px 16px; font-size: 13px; font-weight: bold; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #1e1e1e; color: #ffffff; border-bottom: 2px solid #007acc; }
            QListWidget { font-family: 'Segoe UI', 'Helvetica', sans-serif; font-size: 14pt; border: 1px solid #3c3c3c; border-radius: 4px; padding: 4px; }
            QListWidget::item { padding: 6px; border-bottom: 1px solid #2d2d30; }
            QListWidget::item:hover { background-color: #2a2d2e; }
            QListWidget::item:selected { background-color: #0e639c; color: white; }
            QPushButton { background-color: #0e639c; color: white; font-size: 13px; font-weight: bold; border-radius: 4px; padding: 6px 14px; }
            QPushButton:hover { background-color: #1177bb; }
            QPushButton:pressed { background-color: #094771; }
            QPushButton#btnDiscard { background-color: #a83232; }
            QPushButton#btnDiscard:hover { background-color: #c93b3b; }
            QPushButton#btnCommit { background-color: #28a745; font-size: 14px; }
            QPushButton#btnCommit:hover { background-color: #34ce57; }
            QLineEdit, QTextEdit, QComboBox { background-color: #252526; color: #ffffff; border: 1px solid #3c3c3c; border-radius: 4px; padding: 6px; font-size: 13px; }
            QGroupBox { font-weight: bold; font-size: 13px; border: 1px solid #3c3c3c; border-radius: 6px; margin-top: 6px; padding-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #007acc; }
        """)

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # 1. Barra Superior (Top Bar)
        top_layout = QHBoxLayout()

        btn_open = QPushButton("Abrir Repositorio")
        btn_open.clicked.connect(self.on_select_repository)
        top_layout.addWidget(btn_open)

        lbl_recent = QLabel("Recientes:")
        lbl_recent.setFont(QFont("Segoe UI", 10, QFont.Bold))
        top_layout.addWidget(lbl_recent)

        self.combo_recent = QComboBox()
        self.combo_recent.addItems(self.recent_repos if self.recent_repos else ["Ninguno"])
        self.combo_recent.currentTextChanged.connect(self.on_recent_selected)
        top_layout.addWidget(self.combo_recent, stretch=1)

        btn_refresh = QPushButton("Actualizar")
        btn_refresh.clicked.connect(self.refresh_all)
        top_layout.addWidget(btn_refresh)

        main_layout.addLayout(top_layout)

        # 2. Layout Central con Splitter (Izquierda: Pestañas, Derecha: Diff Viewer)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter, stretch=1)

        # Contenedor Izquierdo (Pestañas)
        self.tabs_widget = QTabWidget()
        splitter.addWidget(self.tabs_widget)

        # Pestaña 1: Área de Trabajo
        workspace_tab = QWidget()
        ws_layout = QVBoxLayout(workspace_tab)

        lists_layout = QHBoxLayout()

        # Modificados / No seguidos
        group_unstaged = QGroupBox("Archivos Modificados / No seguidos")
        layout_u = QVBoxLayout(group_unstaged)
        self.list_unstaged = QListWidget()
        self.list_unstaged.setSelectionMode(QListWidget.ExtendedSelection)
        self.list_unstaged.itemSelectionChanged.connect(self.on_unstaged_select)
        layout_u.addWidget(self.list_unstaged)

        u_btn_layout = QHBoxLayout()
        btn_stage = QPushButton("Preparar (Stage)")
        btn_stage.clicked.connect(self.on_stage_selected)
        u_btn_layout.addWidget(btn_stage)

        btn_discard = QPushButton("Descartar")
        btn_discard.setObjectName("btnDiscard")
        btn_discard.clicked.connect(self.on_discard_selected)
        u_btn_layout.addWidget(btn_discard)

        btn_ignore = QPushButton("+ .gitignore")
        btn_ignore.setStyleSheet("background-color: #555555;")
        btn_ignore.clicked.connect(self.on_add_to_gitignore_selected)
        u_btn_layout.addWidget(btn_ignore)

        layout_u.addLayout(u_btn_layout)
        lists_layout.addWidget(group_unstaged)

        # Staged
        group_staged = QGroupBox("Archivos Preparados (Staged)")
        layout_s = QVBoxLayout(group_staged)
        self.list_staged = QListWidget()
        self.list_staged.setSelectionMode(QListWidget.ExtendedSelection)
        self.list_staged.itemSelectionChanged.connect(self.on_staged_select)
        layout_s.addWidget(self.list_staged)

        s_btn_layout = QHBoxLayout()
        btn_unstage = QPushButton("Despreparar (Unstage)")
        btn_unstage.clicked.connect(self.on_unstage_selected)
        s_btn_layout.addWidget(btn_unstage)

        layout_s.addLayout(s_btn_layout)
        lists_layout.addWidget(group_staged)

        ws_layout.addLayout(lists_layout, stretch=1)

        # Sección para Crear Commit
        group_commit = QGroupBox("Crear Commit")
        commit_layout = QVBoxLayout(group_commit)

        lbl_c_msg = QLabel("Mensaje / Título (1ª línea):")
        commit_layout.addWidget(lbl_c_msg)
        self.input_commit_msg = QLineEdit()
        self.input_commit_msg.setPlaceholder_text = "Escribe el título corto del commit..."
        commit_layout.addWidget(self.input_commit_msg)

        lbl_c_desc = QLabel("Descripción detallada (a partir de la 3ª línea):")
        commit_layout.addWidget(lbl_c_desc)
        self.input_commit_desc = QTextEdit()
        self.input_commit_desc.setMaximumHeight(70)
        commit_layout.addWidget(self.input_commit_desc)

        btn_commit = QPushButton("Crear Commit")
        btn_commit.setObjectName("btnCommit")
        btn_commit.clicked.connect(self.on_create_commit)
        commit_layout.addWidget(btn_commit, alignment=Qt.AlignRight)

        ws_layout.addWidget(group_commit)

        self.tabs_widget.addTab(workspace_tab, "Área de Trabajo")

        # Pestaña 2: Historial de Commits
        history_tab = QWidget()
        hist_layout = QVBoxLayout(history_tab)

        group_commits = QGroupBox("Últimos Commits")
        c_layout = QVBoxLayout(group_commits)
        self.list_commits = QListWidget()
        self.list_commits.itemSelectionChanged.connect(self.on_commit_select)
        c_layout.addWidget(self.list_commits)
        hist_layout.addWidget(group_commits, stretch=1)

        group_commit_files = QGroupBox("Programas / Archivos Afectados")
        f_layout = QVBoxLayout(group_commit_files)
        self.list_commit_files = QListWidget()
        self.list_commit_files.itemSelectionChanged.connect(self.on_commit_file_select)
        f_layout.addWidget(self.list_commit_files)
        hist_layout.addWidget(group_commit_files, stretch=1)

        self.tabs_widget.addTab(history_tab, "Historial de Commits")

        # Pestaña 3: .gitignore
        gitignore_tab = QWidget()
        gi_layout = QVBoxLayout(gitignore_tab)
        gi_layout.addWidget(QLabel("Editar .gitignore:"))
        self.input_gitignore = QTextEdit()
        self.input_gitignore.setFont(QFont("Consolas", 11))
        gi_layout.addWidget(self.input_gitignore)
        btn_save_gi = QPushButton("Guardar .gitignore")
        btn_save_gi.clicked.connect(self.on_save_gitignore)
        gi_layout.addWidget(btn_save_gi, alignment=Qt.AlignRight)

        self.tabs_widget.addTab(gitignore_tab, ".gitignore")

        # Contenedor Derecho (Diff Preview Panel)
        diff_group = QGroupBox("Vista Previa de Cambios (Diff)")
        diff_layout = QVBoxLayout(diff_group)
        self.txt_diff = QTextEdit()
        self.txt_diff.setReadOnly(True)
        self.txt_diff.setFont(QFont("Consolas", 11))
        self.txt_diff.setLineWrapMode(QTextEdit.NoWrap)
        self.diff_highlighter = DiffHighlighter(self.txt_diff.document())
        diff_layout.addWidget(self.txt_diff)

        splitter.addWidget(diff_group)
        splitter.setSizes([600, 500])

        # Status Bar
        self.setStatusBar(QStatusBar())

    def set_repository(self, repo_path: str):
        if not git_service.is_git_repo(repo_path):
            QMessageBox.critical(self, "Error", f"La carpeta '{repo_path}' no es un repositorio Git válido.")
            return

        self.current_repo = repo_path
        self.setWindowTitle(f"Gestor de Repositorio Git - {os.path.basename(repo_path)} ({repo_path})")
        self.recent_repos = git_service.save_recent_repo(repo_path)

        self.combo_recent.blockSignals(True)
        self.combo_recent.clear()
        self.combo_recent.addItems(self.recent_repos)
        self.combo_recent.setCurrentText(repo_path)
        self.combo_recent.blockSignals(False)

        self.refresh_all()
        self.statusBar().showMessage(f"Repositorio cargado: {repo_path}")

    def on_select_repository(self):
        selected_dir = QFileDialog.getExistingDirectory(self, "Seleccionar Repositorio Git")
        if selected_dir:
            self.set_repository(selected_dir)

    def on_recent_selected(self, choice: str):
        if choice and choice != "Ninguno" and choice != self.current_repo:
            self.set_repository(choice)

    def refresh_all(self):
        if not self.current_repo:
            return
        self.refresh_status()
        self.refresh_history()
        self.refresh_gitignore()

    def refresh_status(self):
        self.list_unstaged.clear()
        self.list_staged.clear()

        status = git_service.get_status(self.current_repo)
        self._unstaged_data = status["unstaged"] + status["untracked"]
        for item in self._unstaged_data:
            self.list_unstaged.addItem(f"[{item['status']}] {item['path']}")

        self._staged_data = status["staged"]
        for item in self._staged_data:
            self.list_staged.addItem(f"[{item['status']}] {item['path']}")

    def refresh_history(self):
        self.list_commits.clear()
        self.list_commit_files.clear()

        self._commits_data = git_service.get_commit_history(self.current_repo)
        for commit in self._commits_data:
            line = f"{commit['short_hash']} - {commit['date']} | {commit['message']} ({commit['author']})"
            self.list_commits.addItem(line)

    def refresh_gitignore(self):
        content = git_service.get_gitignore_content(self.current_repo)
        self.input_gitignore.setPlainText(content)

    def on_unstaged_select(self):
        indexes = [item.row() for item in self.list_unstaged.selectedIndexes()]
        if not indexes or not self.current_repo:
            return
        idx = indexes[0]
        if idx < len(self._unstaged_data):
            filepath = self._unstaged_data[idx]["path"]
            diff = git_service.get_file_diff(self.current_repo, filepath, staged=False)
            self.txt_diff.setPlainText(f"Cambios no preparados: {filepath}\n\n" + diff)

    def on_staged_select(self):
        indexes = [item.row() for item in self.list_staged.selectedIndexes()]
        if not indexes or not self.current_repo:
            return
        idx = indexes[0]
        if idx < len(self._staged_data):
            filepath = self._staged_data[idx]["path"]
            diff = git_service.get_file_diff(self.current_repo, filepath, staged=True)
            self.txt_diff.setPlainText(f"Cambios preparados: {filepath}\n\n" + diff)

    def on_stage_selected(self):
        indexes = [item.row() for item in self.list_unstaged.selectedIndexes()]
        if not indexes or not self.current_repo:
            return
        files_to_stage = [self._unstaged_data[i]["path"] for i in indexes]
        if git_service.stage_files(self.current_repo, files_to_stage):
            self.refresh_status()
            self.statusBar().showMessage(f"Archivos añadidos a Stage: {len(files_to_stage)}")

    def on_unstage_selected(self):
        indexes = [item.row() for item in self.list_staged.selectedIndexes()]
        if not indexes or not self.current_repo:
            return
        files_to_unstage = [self._staged_data[i]["path"] for i in indexes]
        if git_service.unstage_files(self.current_repo, files_to_unstage):
            self.refresh_status()
            self.statusBar().showMessage(f"Archivos removidos de Stage: {len(files_to_unstage)}")

    def on_discard_selected(self):
        indexes = [item.row() for item in self.list_unstaged.selectedIndexes()]
        if not indexes or not self.current_repo:
            return
        files_to_discard = [self._unstaged_data[i]["path"] for i in indexes]
        res = QMessageBox.question(
            self, "Confirmar",
            f"¿Descartar cambios en {len(files_to_discard)} archivo(s)? Esta acción es irreversible.",
            QMessageBox.Yes | QMessageBox.No
        )
        if res == QMessageBox.Yes:
            if git_service.discard_changes(self.current_repo, files_to_discard):
                self.refresh_status()
                self.statusBar().showMessage("Cambios descartados.")

    def on_add_to_gitignore_selected(self):
        indexes = [item.row() for item in self.list_unstaged.selectedIndexes()]
        if not indexes or not self.current_repo:
            return
        for i in indexes:
            pattern = self._unstaged_data[i]["path"]
            git_service.add_to_gitignore(self.current_repo, pattern)
        self.refresh_status()
        self.refresh_gitignore()
        self.statusBar().showMessage("Añadido a .gitignore.")

    def on_create_commit(self):
        if not self.current_repo:
            return
        msg = self.input_commit_msg.text().strip()
        desc = self.input_commit_desc.toPlainText().strip()

        if not msg:
            QMessageBox.warning(self, "Atención", "Por favor ingresa un título para el commit.")
            return

        success, err_or_id = git_service.create_commit(self.current_repo, msg, desc)
        if success:
            self.input_commit_msg.clear()
            self.input_commit_desc.clear()
            self.refresh_all()
            self.statusBar().showMessage("Commit creado con éxito.")
            QMessageBox.information(self, "Éxito", f"Commit creado exitosamente.\nID: {err_or_id[:7]}")
        else:
            QMessageBox.critical(self, "Error de Commit", f"No se pudo crear el commit:\n{err_or_id}")

    def on_commit_select(self):
        indexes = [item.row() for item in self.list_commits.selectedIndexes()]
        if not indexes or not self.current_repo:
            return
        idx = indexes[0]
        self._selected_commit = self._commits_data[idx]
        commit_hash = self._selected_commit["hash"]

        # Cargar archivos afectados de forma ultra rápida
        self._current_commit_files = git_service.get_commit_files(self.current_repo, commit_hash)
        self.list_commit_files.clear()
        for f in self._current_commit_files:
            self.list_commit_files.addItem(f"[{f['status']}] {f['path']}")

        # Formatear la consulta sin duplicación de información
        diff = git_service.get_commit_diff(self.current_repo, commit_hash)
        header_text = f"Commit {commit_hash}\n" \
                      f"Autor: {self._selected_commit['author']}\n" \
                      f"Fecha: {self._selected_commit['date']}\n" \
                      f"Mensaje: {self._selected_commit['message']}\n"

        if self._selected_commit.get('description'):
            header_text += f"Descripción: {self._selected_commit['description']}\n"

        self.txt_diff.setPlainText(header_text + "\n" + diff)

    def on_commit_file_select(self):
        indexes = [item.row() for item in self.list_commit_files.selectedIndexes()]
        if not indexes or not self.current_repo or not hasattr(self, "_selected_commit"):
            return
        idx = indexes[0]
        filepath = self._current_commit_files[idx]["path"]
        commit_hash = self._selected_commit["hash"]

        diff = git_service.get_commit_diff(self.current_repo, commit_hash, filepath)
        self.txt_diff.setPlainText(
            f"Commit {self._selected_commit['short_hash']} - Archivo: {filepath}\n\n" + diff
        )

    def on_save_gitignore(self):
        if not self.current_repo:
            return
        content = self.input_gitignore.toPlainText()
        if git_service.save_gitignore_content(self.current_repo, content):
            self.refresh_status()
            self.statusBar().showMessage(".gitignore actualizado.")
            QMessageBox.information(self, "Guardado", "El archivo .gitignore se guardó correctamente.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GitGuiPySideApp()
    window.show()
    sys.exit(app.exec())
