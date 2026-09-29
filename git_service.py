import os
import json
import pygit2
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

CONFIG_FILE = os.path.expanduser("~/.pygit_gui_config.json")

def load_config() -> Dict[str, Any]:
    """Carga la configuración guardada del archivo de preferencias."""
    if not os.path.exists(CONFIG_FILE):
        return {"recent_repos": [], "last_repo": None}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            recent = [path for path in data.get("recent_repos", []) if os.path.isdir(path)]
            last_repo = data.get("last_repo")
            if last_repo and not os.path.isdir(last_repo):
                last_repo = None
            return {"recent_repos": recent, "last_repo": last_repo}
    except Exception:
        return {"recent_repos": [], "last_repo": None}

def load_recent_repos() -> List[str]:
    """Carga la lista de repositorios recientes guardados."""
    return load_config().get("recent_repos", [])

def load_last_repo() -> Optional[str]:
    """Obtiene el último repositorio seleccionado por el usuario."""
    return load_config().get("last_repo")

def save_recent_repo(repo_path: str) -> List[str]:
    """Guarda un repositorio como el último usado y en la lista de recientes."""
    repo_path = os.path.abspath(repo_path)
    recent = load_recent_repos()
    if repo_path in recent:
        recent.remove(repo_path)
    recent.insert(0, repo_path)
    recent = recent[:10]  # Mantener los 10 más recientes

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "recent_repos": recent,
                "last_repo": repo_path
            }, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
    return recent

def is_git_repo(repo_path: str) -> bool:
    """Verifica si el directorio dado es un repositorio git válido mediante PyGit2."""
    if not repo_path or not os.path.isdir(repo_path):
        return False
    try:
        pygit2.discover_repository(repo_path)
        return True
    except Exception:
        return False

def open_repo(repo_path: str) -> pygit2.Repository:
    """Abre y retorna un objeto Repository de PyGit2."""
    discovered = pygit2.discover_repository(repo_path)
    if not discovered:
        raise ValueError(f"No es un repositorio Git válido: {repo_path}")
    return pygit2.Repository(discovered)

def get_status(repo_path: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Obtiene el estado del repositorio de forma ultra rápida con PyGit2.
    Retorna listas separadas para staged, unstaged y untracked sin duplicar datos.
    """
    staged = []
    unstaged = []
    untracked = []

    try:
        repo = open_repo(repo_path)
        status_flags = repo.status()
    except Exception:
        return {"staged": staged, "unstaged": unstaged, "untracked": untracked}

    for filepath, flags in status_flags.items():
        # Untracked
        if flags & pygit2.GIT_STATUS_WT_NEW:
            untracked.append({"path": filepath, "status": "No seguido"})
            continue

        # Staged
        if flags & pygit2.GIT_STATUS_INDEX_NEW:
            staged.append({"path": filepath, "status": "Añadido", "code": "A"})
        elif flags & pygit2.GIT_STATUS_INDEX_MODIFIED:
            staged.append({"path": filepath, "status": "Modificado", "code": "M"})
        elif flags & pygit2.GIT_STATUS_INDEX_DELETED:
            staged.append({"path": filepath, "status": "Eliminado", "code": "D"})
        elif flags & pygit2.GIT_STATUS_INDEX_RENAMED:
            staged.append({"path": filepath, "status": "Renombrado", "code": "R"})

        # Unstaged (Directorio de trabajo)
        if flags & pygit2.GIT_STATUS_WT_MODIFIED:
            unstaged.append({"path": filepath, "status": "Modificado", "code": "M"})
        elif flags & pygit2.GIT_STATUS_WT_DELETED:
            unstaged.append({"path": filepath, "status": "Eliminado", "code": "D"})
        elif flags & pygit2.GIT_STATUS_WT_RENAMED:
            unstaged.append({"path": filepath, "status": "Renombrado", "code": "R"})

    return {"staged": staged, "unstaged": unstaged, "untracked": untracked}

def stage_files(repo_path: str, filepaths: List[str]) -> bool:
    """Añade archivos al index (Stage) con PyGit2."""
    if not filepaths:
        return True
    try:
        repo = open_repo(repo_path)
        index = repo.index
        for path in filepaths:
            full_p = os.path.join(repo.workdir, path)
            if os.path.exists(full_p):
                index.add(path)
            else:
                index.remove(path)
        index.write()
        return True
    except Exception:
        return False

def unstage_files(repo_path: str, filepaths: List[str]) -> bool:
    """Quita archivos del index (Unstage) con PyGit2."""
    if not filepaths:
        return True
    try:
        repo = open_repo(repo_path)
        if repo.is_empty or repo.head_is_unborn:
            for path in filepaths:
                try:
                    repo.index.remove(path)
                except KeyError:
                    pass
            repo.index.write()
            return True

        head_commit = repo[repo.head.target]
        for path in filepaths:
            try:
                tree_entry = head_commit.tree[path]
                index_entry = pygit2.IndexEntry(path, tree_entry.id, tree_entry.filemode)
                repo.index.add(index_entry)
            except KeyError:
                try:
                    repo.index.remove(path)
                except KeyError:
                    pass
        repo.index.write()
        return True
    except Exception:
        return False

def discard_changes(repo_path: str, filepaths: List[str]) -> bool:
    """Restaura cambios en los archivos del directorio de trabajo con PyGit2."""
    if not filepaths:
        return True
    try:
        repo = open_repo(repo_path)
        repo.checkout_head(strategy=pygit2.GIT_CHECKOUT_FORCE, paths=filepaths)
        return True
    except Exception:
        return False

def create_commit(repo_path: str, subject: str, description: str = "") -> tuple[bool, str]:
    """Crea un commit usando la API en memoria de PyGit2."""
    subject = subject.strip()
    if not subject:
        return False, "El título del commit no puede estar vacío."

    full_message = subject
    description = description.strip()
    if description:
        full_message += f"\n\n{description}"

    try:
        repo = open_repo(repo_path)
        config = repo.config

        # Obtener o configurar datos de firma
        try:
            name = config['user.name']
            email = config['user.email']
        except KeyError:
            name = "Usuario Git"
            email = "usuario@ejemplo.com"

        author = pygit2.Signature(name, email)
        committer = author

        index = repo.index
        tree_id = index.write_tree()

        parents = []
        if not repo.is_empty and not repo.head_is_unborn:
            parents = [repo.head.target]

        commit_id = repo.create_commit('HEAD', author, committer, full_message, tree_id, parents)
        return True, str(commit_id)
    except Exception as e:
        return False, str(e)

def format_timestamp(ts: int, tz_offset: int) -> str:
    """Convierte timestamp unix y offset en string de fecha ISO corta."""
    tz = timezone(timedelta(minutes=tz_offset))
    dt = datetime.fromtimestamp(ts, tz)
    return dt.strftime("%Y-%m-%d")

def get_commit_history(repo_path: str, max_count: int = 30) -> List[Dict[str, Any]]:
    """Obtiene el historial de commits desde la memoria con PyGit2 estructurando de forma limpia."""
    commits = []
    try:
        repo = open_repo(repo_path)
        if repo.is_empty or repo.head_is_unborn:
            return commits

        walker = repo.walk(repo.head.target, pygit2.GIT_SORT_TIME)
        for i, commit in enumerate(walker):
            if i >= max_count:
                break

            msg_parts = commit.message.strip().split("\n", 1)
            subject = msg_parts[0].strip()
            description = msg_parts[1].strip() if len(msg_parts) > 1 else ""

            date_str = format_timestamp(commit.author.time, commit.author.offset)

            commits.append({
                "hash": str(commit.id),
                "short_hash": str(commit.short_id),
                "author": commit.author.name,
                "date": date_str,
                "message": subject,
                "description": description
            })
    except Exception:
        pass
    return commits

def get_commit_files(repo_path: str, commit_hash: str) -> List[Dict[str, str]]:
    """Obtiene archivos modificados en un commit específico."""
    files = []
    try:
        repo = open_repo(repo_path)
        commit = repo[commit_hash]

        if commit.parents:
            diff = repo.diff(commit.parents[0].tree, commit.tree)
        else:
            diff = commit.tree.diff_to_tree()

        for patch in diff:
            status_map = {
                pygit2.GIT_DELTA_ADDED: "Añadido",
                pygit2.GIT_DELTA_DELETED: "Eliminado",
                pygit2.GIT_DELTA_MODIFIED: "Modificado",
                pygit2.GIT_DELTA_RENAMED: "Renombrado"
            }
            # Si es el commit raíz diff_to_tree invierte del/add
            if not commit.parents and patch.delta.status == pygit2.GIT_DELTA_DELETED:
                status_str = "Añadido"
            else:
                status_str = status_map.get(patch.delta.status, "Modificado")

            filepath = patch.delta.new_file.path or patch.delta.old_file.path
            files.append({"path": filepath, "status": status_str})
    except Exception:
        pass
    return files

def get_file_diff(repo_path: str, filepath: str, staged: bool = False) -> str:
    """Obtiene el diff de un archivo específico de forma ultrarrápida."""
    try:
        repo = open_repo(repo_path)
        if staged:
            # Diff entre HEAD e INDEX
            parent_tree = repo[repo.head.target].tree if not repo.head_is_unborn else None
            diff = repo.diff(parent_tree, flags=pygit2.GIT_DIFF_NORMAL)
        else:
            # Diff entre INDEX y Workdir
            diff = repo.diff(flags=pygit2.GIT_DIFF_NORMAL)

        patch_text = ""
        for patch in diff:
            p_path = patch.delta.new_file.path or patch.delta.old_file.path
            if p_path == filepath:
                patch_text = patch.text
                break
        return patch_text if patch_text else "Sin cambios detectados."
    except Exception as e:
        return f"Error al generar diff: {e}"

def get_commit_diff(repo_path: str, commit_hash: str, filepath: Optional[str] = None) -> str:
    """Obtiene el diff de un commit completo o de un archivo dentro del commit."""
    try:
        repo = open_repo(repo_path)
        commit = repo[commit_hash]

        if commit.parents:
            diff = repo.diff(commit.parents[0].tree, commit.tree)
        else:
            diff = commit.tree.diff_to_tree()

        if filepath:
            for patch in diff:
                p_path = patch.delta.new_file.path or patch.delta.old_file.path
                if p_path == filepath:
                    return patch.text
            return "Sin diferencias en este archivo."

        return diff.patch if diff.patch else "Sin cambios en el commit."
    except Exception as e:
        return f"Error al obtener diff de commit: {e}"

def get_gitignore_content(repo_path: str) -> str:
    """Lee el contenido del archivo .gitignore."""
    gitignore_path = os.path.join(repo_path, ".gitignore")
    if not os.path.exists(gitignore_path):
        return ""
    try:
        with open(gitignore_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def save_gitignore_content(repo_path: str, content: str) -> bool:
    """Guarda el contenido del archivo .gitignore."""
    gitignore_path = os.path.join(repo_path, ".gitignore")
    try:
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception:
        return False

def add_to_gitignore(repo_path: str, pattern: str) -> bool:
    """Agrega un patrón o archivo a .gitignore."""
    pattern = pattern.strip()
    if not pattern:
        return False
    current = get_gitignore_content(repo_path)
    lines = [l.strip() for l in current.splitlines()]
    if pattern in lines:
        return True

    new_content = current
    if current and not current.endswith("\n"):
        new_content += "\n"
    new_content += pattern + "\n"
    return save_gitignore_content(repo_path, new_content)
