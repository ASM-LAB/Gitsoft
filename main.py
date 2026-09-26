import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import customtkinter as ctk
from typing import Optional, List, Dict

import git_service

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class GitGuiApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gestor de Repositorio Git")
        self.geometry("1100x700")
        self.minsize(900, 600)

        self.current_repo: Optional[str] = None
        self.recent_repos: List[str] = git_service.load_recent_repos()

        # Configurar grid principal (Header, Main view, Statusbar)
        self.grid_rowconfigure(0, weight=0)  # Top Bar
        self.grid_rowconfigure(1, weight=1)  # Main Content
        self.grid_rowconfigure(2, weight=0)  # Status Bar
        self.grid_columnconfigure(0, weight=1)

        self._create_top_bar()
        self._create_main_content()
        self._create_status_bar()

        # Seleccionar por defecto el repo actual o el primero de la lista reciente si existe
        default_dir = os.getcwd()
        if git_service.is_git_repo(default_dir):
            self.set_repository(default_dir)
        elif self.recent_repos:
            self.set_repository(self.recent_repos[0])
        else:
            self.update_status("Por favor, selecciona un repositorio Git para comenzar.")

    def _create_top_bar(self):
        self.top_frame = ctk.CTkFrame(self, corner_radius=0)
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        self.top_frame.grid_columnconfigure(2, weight=1)

        btn_select = ctk.CTkButton(
            self.top_frame, text="Abrir Repositorio", command=self.on_select_repository
        )
        btn_select.grid(row=0, column=0, padx=10, pady=10)

        label_recent = ctk.CTkLabel(self.top_frame, text="Recientes:")
        label_recent.grid(row=0, column=1, padx=(5, 5), pady=10)

        self.combo_recent = ctk.CTkOptionMenu(
            self.top_frame,
            values=self.recent_repos if self.recent_repos else ["Ninguno"],
            command=self.on_recent_selected
        )
        self.combo_recent.grid(row=0, column=2, sticky="ew", padx=5, pady=10)

        btn_refresh = ctk.CTkButton(
            self.top_frame, text="Actualizar", width=100, command=self.refresh_all
        )
        btn_refresh.grid(row=0, column=3, padx=10, pady=10)

    def _create_main_content(self):
        # Frame contenedor central con PanedWindow para dividir la vista principal y el panel lateral de diff
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=3)
        self.main_container.grid_columnconfigure(1, weight=2)

        # Tabs a la izquierda
        self.tabview = ctk.CTkTabview(self.main_container)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        self.tab_workspace = self.tabview.add("Área de Trabajo")
        self.tab_history = self.tabview.add("Historial de Commits")
        self.tab_gitignore = self.tabview.add(".gitignore")

        self._setup_workspace_tab()
        self._setup_history_tab()
        self._setup_gitignore_tab()

        # Panel lateral de Diff a la derecha
        self.diff_frame = ctk.CTkFrame(self.main_container)
        self.diff_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.diff_frame.grid_rowconfigure(1, weight=1)
        self.diff_frame.grid_columnconfigure(0, weight=1)

        diff_title = ctk.CTkLabel(self.diff_frame, text="Vista Previa de Cambios (Diff)", font=("Helvetica", 14, "bold"))
        diff_title.grid(row=0, column=0, sticky="w", padx=10, pady=10)

        self.diff_textbox = ctk.CTkTextbox(self.diff_frame, font=("Courier", 12), wrap="none")
        self.diff_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def _setup_workspace_tab(self):
        tab = self.tab_workspace
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=0)
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)

        # Seccion de Archivos Modificados / No preparados
        frame_unstaged = ctk.CTkFrame(tab)
        frame_unstaged.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        frame_unstaged.grid_rowconfigure(1, weight=1)
        frame_unstaged.grid_columnconfigure(0, weight=1)

        lbl_unstaged = ctk.CTkLabel(frame_unstaged, text="Archivos Modificados / No seguidos", font=("Helvetica", 13, "bold"))
        lbl_unstaged.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.listbox_unstaged = tk.Listbox(frame_unstaged, selectmode=tk.EXTENDED, bg="#2b2b2b", fg="#ffffff", selectbackground="#1f538d", highlightthickness=0, font=("Helvetica", 14))
        self.listbox_unstaged.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.listbox_unstaged.bind("<<ListboxSelect>>", self.on_unstaged_select)

        btn_box_unstaged = ctk.CTkFrame(frame_unstaged, fg_color="transparent")
        btn_box_unstaged.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        btn_stage = ctk.CTkButton(btn_box_unstaged, text="Preparar (Stage)", command=self.on_stage_selected)
        btn_stage.pack(side="left", padx=2)

        btn_discard = ctk.CTkButton(btn_box_unstaged, text="Descartar", fg_color="#a83232", hover_color="#782323", command=self.on_discard_selected)
        btn_discard.pack(side="left", padx=2)

        btn_add_ignore = ctk.CTkButton(btn_box_unstaged, text="+ .gitignore", fg_color="#555555", hover_color="#333333", command=self.on_add_to_gitignore_selected)
        btn_add_ignore.pack(side="left", padx=2)

        # Seccion de Archivos Preparados (Staged)
        frame_staged = ctk.CTkFrame(tab)
        frame_staged.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        frame_staged.grid_rowconfigure(1, weight=1)
        frame_staged.grid_columnconfigure(0, weight=1)

        lbl_staged = ctk.CTkLabel(frame_staged, text="Archivos Preparados (Staged)", font=("Helvetica", 13, "bold"))
        lbl_staged.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.listbox_staged = tk.Listbox(frame_staged, selectmode=tk.EXTENDED, bg="#2b2b2b", fg="#ffffff", selectbackground="#1f538d", highlightthickness=0, font=("Helvetica", 14))
        self.listbox_staged.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.listbox_staged.bind("<<ListboxSelect>>", self.on_staged_select)

        btn_box_staged = ctk.CTkFrame(frame_staged, fg_color="transparent")
        btn_box_staged.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        btn_unstage = ctk.CTkButton(btn_box_staged, text="Despreparar (Unstage)", command=self.on_unstage_selected)
        btn_unstage.pack(side="left", padx=2)

        # Sección para Crear Commit
        frame_commit = ctk.CTkFrame(tab)
        frame_commit.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        frame_commit.grid_columnconfigure(0, weight=1)

        lbl_commit = ctk.CTkLabel(frame_commit, text="Mensaje del Commit:", font=("Helvetica", 12, "bold"))
        lbl_commit.grid(row=0, column=0, sticky="w", padx=10, pady=(5, 0))

        self.entry_commit_msg = ctk.CTkEntry(frame_commit, placeholder_text="Escribe el mensaje de commit aquí...")
        self.entry_commit_msg.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        btn_commit = ctk.CTkButton(frame_commit, text="Crear Commit", font=("Helvetica", 12, "bold"), fg_color="#28a745", hover_color="#1e7e34", command=self.on_create_commit)
        btn_commit.grid(row=1, column=1, padx=10, pady=5)

    def _setup_history_tab(self):
        tab = self.tab_history
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        # Lista de commits
        frame_commits = ctk.CTkFrame(tab)
        frame_commits.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        frame_commits.grid_rowconfigure(1, weight=1)
        frame_commits.grid_columnconfigure(0, weight=1)

        lbl_history = ctk.CTkLabel(frame_commits, text="Últimos Commits", font=("Helvetica", 13, "bold"))
        lbl_history.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.listbox_commits = tk.Listbox(frame_commits, selectmode=tk.SINGLE, bg="#2b2b2b", fg="#ffffff", selectbackground="#1f538d", highlightthickness=0, font=("Helvetica", 14))
        self.listbox_commits.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.listbox_commits.bind("<<ListboxSelect>>", self.on_commit_select)

        # Archivos del commit seleccionado
        frame_commit_files = ctk.CTkFrame(tab)
        frame_commit_files.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        frame_commit_files.grid_rowconfigure(1, weight=1)
        frame_commit_files.grid_columnconfigure(0, weight=1)

        lbl_commit_files = ctk.CTkLabel(frame_commit_files, text="Programas / Archivos Afectados en el Commit", font=("Helvetica", 13, "bold"))
        lbl_commit_files.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.listbox_commit_files = tk.Listbox(frame_commit_files, selectmode=tk.SINGLE, bg="#2b2b2b", fg="#ffffff", selectbackground="#1f538d", highlightthickness=0, font=("Helvetica", 14))
        self.listbox_commit_files.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.listbox_commit_files.bind("<<ListboxSelect>>", self.on_commit_file_select)

    def _setup_gitignore_tab(self):
        tab = self.tab_gitignore
        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        lbl_info = ctk.CTkLabel(tab, text="Editar .gitignore del repositorio:", font=("Helvetica", 13, "bold"))
        lbl_info.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.gitignore_textbox = ctk.CTkTextbox(tab, font=("Courier", 12))
        self.gitignore_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        btn_save_gi = ctk.CTkButton(tab, text="Guardar .gitignore", command=self.on_save_gitignore)
        btn_save_gi.grid(row=2, column=0, sticky="e", padx=10, pady=10)

    def _create_status_bar(self):
        self.status_label = ctk.CTkLabel(self, text="Listo", anchor="w", font=("Helvetica", 11))
        self.status_label.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 5))

    def update_status(self, msg: str):
        self.status_label.configure(text=msg)

    def set_repository(self, repo_path: str):
        if not git_service.is_git_repo(repo_path):
            messagebox.showerror("Error", f"La carpeta '{repo_path}' no es un repositorio Git válido.")
            return

        self.current_repo = repo_path
        self.title(f"Gestor de Repositorio Git - {os.path.basename(repo_path)} ({repo_path})")
        self.recent_repos = git_service.save_recent_repo(repo_path)

        self.combo_recent.configure(values=self.recent_repos)
        self.combo_recent.set(repo_path)

        self.refresh_all()
        self.update_status(f"Repositorio cargado: {repo_path}")

    def on_select_repository(self):
        selected_dir = filedialog.askdirectory(title="Seleccionar Repositorio Git")
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
        self.listbox_unstaged.delete(0, tk.END)
        self.listbox_staged.delete(0, tk.END)

        status = git_service.get_status(self.current_repo)

        self._unstaged_data = status["unstaged"] + status["untracked"]
        for item in self._unstaged_data:
            self.listbox_unstaged.insert(tk.END, f"[{item['status']}] {item['path']}")

        self._staged_data = status["staged"]
        for item in self._staged_data:
            self.listbox_staged.insert(tk.END, f"[{item['status']}] {item['path']}")

    def refresh_history(self):
        self.listbox_commits.delete(0, tk.END)
        self.listbox_commit_files.delete(0, tk.END)

        self._commits_data = git_service.get_commit_history(self.current_repo)
        for commit in self._commits_data:
            line = f"{commit['short_hash']} - {commit['date']} | {commit['message']} ({commit['author']})"
            self.listbox_commits.insert(tk.END, line)

    def refresh_gitignore(self):
        content = git_service.get_gitignore_content(self.current_repo)
        self.gitignore_textbox.delete("1.0", tk.END)
        self.gitignore_textbox.insert("1.0", content)

    # Handlers para área de trabajo
    def on_unstaged_select(self, event):
        selections = self.listbox_unstaged.curselection()
        if not selections or not self.current_repo:
            return
        idx = selections[0]
        if idx < len(self._unstaged_data):
            filepath = self._unstaged_data[idx]["path"]
            diff = git_service.get_file_diff(self.current_repo, filepath, staged=False)
            self.show_diff(f"Cambios no preparados: {filepath}\n\n" + diff)

    def on_staged_select(self, event):
        selections = self.listbox_staged.curselection()
        if not selections or not self.current_repo:
            return
        idx = selections[0]
        if idx < len(self._staged_data):
            filepath = self._staged_data[idx]["path"]
            diff = git_service.get_file_diff(self.current_repo, filepath, staged=True)
            self.show_diff(f"Cambios preparados (Staged): {filepath}\n\n" + diff)

    def on_stage_selected(self):
        selections = self.listbox_unstaged.curselection()
        if not selections or not self.current_repo:
            return
        files_to_stage = [self._unstaged_data[i]["path"] for i in selections]
        if git_service.stage_files(self.current_repo, files_to_stage):
            self.refresh_status()
            self.update_status(f"Archivos añadidos a Stage: {len(files_to_stage)}")
        else:
            messagebox.showerror("Error", "Ocurrió un error al agregar archivos al Stage.")

    def on_unstage_selected(self):
        selections = self.listbox_staged.curselection()
        if not selections or not self.current_repo:
            return
        files_to_unstage = [self._staged_data[i]["path"] for i in selections]
        if git_service.unstage_files(self.current_repo, files_to_unstage):
            self.refresh_status()
            self.update_status(f"Archivos removidos de Stage: {len(files_to_unstage)}")
        else:
            messagebox.showerror("Error", "Ocurrió un error al quitar archivos del Stage.")

    def on_discard_selected(self):
        selections = self.listbox_unstaged.curselection()
        if not selections or not self.current_repo:
            return
        files_to_discard = [self._unstaged_data[i]["path"] for i in selections]
        if messagebox.askyesno("Confirmar", f"¿Estás seguro de descartar cambios en {len(files_to_discard)} archivo(s)? Esta acción no se puede deshacer."):
            if git_service.discard_changes(self.current_repo, files_to_discard):
                self.refresh_status()
                self.update_status("Cambios descartados.")
            else:
                messagebox.showerror("Error", "Ocurrió un error al descartar cambios.")

    def on_add_to_gitignore_selected(self):
        selections = self.listbox_unstaged.curselection()
        if not selections or not self.current_repo:
            return
        for i in selections:
            pattern = self._unstaged_data[i]["path"]
            git_service.add_to_gitignore(self.current_repo, pattern)
        self.refresh_status()
        self.refresh_gitignore()
        self.update_status("Archivos añadidos a .gitignore")

    def on_create_commit(self):
        if not self.current_repo:
            return
        msg = self.entry_commit_msg.get().strip()
        if not msg:
            messagebox.showwarning("Atención", "Por favor ingresa un mensaje para el commit.")
            return

        success, err_or_out = git_service.create_commit(self.current_repo, msg)
        if success:
            self.entry_commit_msg.delete(0, tk.END)
            self.refresh_all()
            self.update_status("Commit creado con éxito.")
            messagebox.showinfo("Éxito", "Commit creado exitosamente.")
        else:
            messagebox.showerror("Error de Commit", f"No se pudo crear el commit:\n{err_or_out}")

    # Handlers para Historial
    def on_commit_select(self, event):
        selections = self.listbox_commits.curselection()
        if not selections or not self.current_repo:
            return
        idx = selections[0]
        self._selected_commit = self._commits_data[idx]
        commit_hash = self._selected_commit["hash"]

        # Cargar archivos afectados en este commit
        self._current_commit_files = git_service.get_commit_files(self.current_repo, commit_hash)
        self.listbox_commit_files.delete(0, tk.END)
        for f in self._current_commit_files:
            self.listbox_commit_files.insert(tk.END, f"[{f['status']}] {f['path']}")

        # Mostrar el diff completo del commit
        diff = git_service.get_commit_diff(self.current_repo, commit_hash)
        self.show_diff(f"Commit {commit_hash}\n"
                       f"Autor: {self._selected_commit['author']}\n"
                       f"Fecha: {self._selected_commit['date']}\n"
                       f"Mensaje: {self._selected_commit['message']}\n\n" + diff)

    def on_commit_file_select(self, event):
        selections = self.listbox_commit_files.curselection()
        if not selections or not self.current_repo or not hasattr(self, "_selected_commit"):
            return
        idx = selections[0]
        filepath = self._current_commit_files[idx]["path"]
        commit_hash = self._selected_commit["hash"]

        diff = git_service.get_commit_diff(self.current_repo, commit_hash, filepath)
        self.show_diff(f"Commit {self._selected_commit['short_hash']} - Archivo: {filepath}\n\n" + diff)

    # Handlers para .gitignore
    def on_save_gitignore(self):
        if not self.current_repo:
            return
        content = self.gitignore_textbox.get("1.0", tk.END)
        if git_service.save_gitignore_content(self.current_repo, content):
            self.refresh_status()
            self.update_status("Archivo .gitignore guardado exitosamente.")
            messagebox.showinfo("Guardado", "El archivo .gitignore se ha actualizado correctamente.")
        else:
            messagebox.showerror("Error", "No se pudo guardar el archivo .gitignore.")

    def show_diff(self, text: str):
        self.diff_textbox.delete("1.0", tk.END)

        # Configurar etiquetas de color y formato para el diff en el widget de texto interno
        internal_textbox = self.diff_textbox._textbox
        internal_textbox.tag_config("diff_add", foreground="#28a745")       # Verde para adiciones
        internal_textbox.tag_config("diff_remove", foreground="#dc3545")    # Rojo para eliminaciones
        internal_textbox.tag_config("diff_header", foreground="#17a2b8")    # Cyan para cabeceras @@
        internal_textbox.tag_config("diff_meta", foreground="#ffc107")      # Amarillo para metadatos
        internal_textbox.tag_config("diff_bold_meta", foreground="#ffc107", font=("Courier", 13, "bold")) # Amarillo y Negrita para Autor, Fecha, Mensaje, Commit

        lines = text.splitlines(keepends=True)
        for line in lines:
            line_start = self.diff_textbox.index("insert")
            self.diff_textbox.insert(tk.END, line)
            line_end = self.diff_textbox.index("insert")

            if line.startswith("Autor:") or line.startswith("Fecha:") or line.startswith("Mensaje:") or line.startswith("Commit ") or line.startswith("Cambios no preparados:") or line.startswith("Cambios preparados"):
                internal_textbox.tag_add("diff_bold_meta", line_start, line_end)
            elif line.startswith("+") and not line.startswith("+++"):
                internal_textbox.tag_add("diff_add", line_start, line_end)
            elif line.startswith("-") and not line.startswith("---"):
                internal_textbox.tag_add("diff_remove", line_start, line_end)
            elif line.startswith("@@"):
                internal_textbox.tag_add("diff_header", line_start, line_end)
            elif line.startswith("diff --git") or line.startswith("index ") or line.startswith("---") or line.startswith("+++"):
                internal_textbox.tag_add("diff_meta", line_start, line_end)

if __name__ == "__main__":
    app = GitGuiApp()
    app.mainloop()
