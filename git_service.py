import os
import json
import subprocess
from typing import List, Dict, Any, Optional

CONFIG_FILE = os.path.expanduser("~/.pygit_gui_config.json")

def load_recent_repos() -> List[str]:
    """Carga la lista de repositorios recientes guardados."""
    if not os.path.exists(CONFIG_FILE):
        return []
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [path for path in data.get("recent_repos", []) if os.path.isdir(path)]
    except Exception:
        return []

def save_recent_repo(repo_path: str) -> List[str]:
    """Guarda un repositorio en la lista de recientes y retorna la lista actualizada."""
    repo_path = os.path.abspath(repo_path)
    recent = load_recent_repos()
    if repo_path in recent:
        recent.remove(repo_path)
    recent.insert(0, repo_path)
    recent = recent[:10]  # Mantener los 10 más recientes

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"recent_repos": recent}, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
    return recent

def run_git_command(repo_path: str, args: List[str]) -> subprocess.CompletedProcess:
    """Ejecuta un comando de git en el directorio del repositorio."""
    return subprocess.run(
        ["git"] + args,
        cwd=repo_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

def is_git_repo(repo_path: str) -> bool:
    """Verifica si el directorio dado es un repositorio git válido."""
    if not repo_path or not os.path.isdir(repo_path):
        return False
    res = run_git_command(repo_path, ["rev-parse", "--is-inside-work-tree"])
    return res.returncode == 0 and res.stdout.strip() == "true"

def get_status(repo_path: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Obtiene el estado actual del repositorio.
    Retorna un diccionario con 'staged', 'unstaged', y 'untracked'.
    """
    res = run_git_command(repo_path, ["status", "--porcelain=v1"])
    staged = []
    unstaged = []
    untracked = []

    if res.returncode != 0:
        return {"staged": staged, "unstaged": unstaged, "untracked": untracked}

    for line in res.stdout.splitlines():
        if len(line) < 4:
            continue
        index_status = line[0]
        worktree_status = line[1]
        filepath = line[3:].strip()

        # Manejar renombrados si aplica (e.g., "R  old -> new")
        if " -> " in filepath:
            filepath = filepath.split(" -> ")[1]

        # Archivos Untracked (no seguidos)
        if index_status == "?" and worktree_status == "?":
            untracked.append({"path": filepath, "status": "No seguido"})
            continue

        # Archivos Staged
        if index_status not in (" ", "?"):
            status_desc = {
                "M": "Modificado",
                "A": "Añadido",
                "D": "Eliminado",
                "R": "Renombrado",
                "C": "Copiado"
            }.get(index_status, index_status)
            staged.append({"path": filepath, "status": status_desc, "code": index_status})

        # Archivos Unstaged
        if worktree_status not in (" ", "?"):
            status_desc = {
                "M": "Modificado",
                "D": "Eliminado"
            }.get(worktree_status, worktree_status)
            unstaged.append({"path": filepath, "status": status_desc, "code": worktree_status})

    return {"staged": staged, "unstaged": unstaged, "untracked": untracked}

def stage_files(repo_path: str, filepaths: List[str]) -> bool:
    """Agrega archivos al área de preparación (stage)."""
    if not filepaths:
        return True
    res = run_git_command(repo_path, ["add"] + filepaths)
    return res.returncode == 0

def unstage_files(repo_path: str, filepaths: List[str]) -> bool:
    """Quita archivos del área de preparación (unstage)."""
    if not filepaths:
        return True
    # 'git restore --staged' falla si aún no existe un HEAD (repo sin commits previas)
    res = run_git_command(repo_path, ["restore", "--staged"] + filepaths)
    if res.returncode != 0:
        res = run_git_command(repo_path, ["rm", "--cached", "-r"] + filepaths)
    return res.returncode == 0

def discard_changes(repo_path: str, filepaths: List[str]) -> bool:
    """Descarta los cambios en el directorio de trabajo."""
    if not filepaths:
        return True
    res = run_git_command(repo_path, ["checkout", "--"] + filepaths)
    return res.returncode == 0

def create_commit(repo_path: str, message: str) -> tuple[bool, str]:
    """Crea un commit con el mensaje proporcionado."""
    if not message.strip():
        return False, "El mensaje de commit no puede estar vacío."
    res = run_git_command(repo_path, ["commit", "-m", message])
    if res.returncode == 0:
        return True, res.stdout.strip()
    return False, res.stderr.strip() or res.stdout.strip()

def get_commit_history(repo_path: str, max_count: int = 30) -> List[Dict[str, Any]]:
    """Obtiene el historial de últimos commits."""
    fmt = "%H%x1f%h%x1f%an%x1f%ad%x1f%s"
    res = run_git_command(
        repo_path,
        ["log", f"-n{max_count}", f"--format={fmt}", "--date=short"]
    )
    commits = []
    if res.returncode != 0:
        return commits

    for line in res.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\x1f")
        if len(parts) == 5:
            full_hash, short_hash, author, date, message = parts
            commits.append({
                "hash": full_hash,
                "short_hash": short_hash,
                "author": author,
                "date": date,
                "message": message
            })
    return commits

def get_commit_files(repo_path: str, commit_hash: str) -> List[Dict[str, str]]:
    """Obtiene la lista de archivos afectados en un commit específico."""
    res = run_git_command(repo_path, ["show", "--name-status", "--oneline", commit_hash])
    files = []
    if res.returncode != 0:
        return files

    lines = res.stdout.splitlines()
    # La primera línea es la cabecera con el commit hash y mensaje
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            status_code, filepath = parts
            status_map = {
                "M": "Modificado",
                "A": "Añadido",
                "D": "Eliminado",
                "R": "Renombrado"
            }
            files.append({
                "path": filepath,
                "status": status_map.get(status_code[0], status_code)
            })
    return files

def get_file_diff(repo_path: str, filepath: str, staged: bool = False) -> str:
    """Obtiene el diff de un archivo."""
    args = ["diff"]
    if staged:
        args.append("--staged")
    args.extend(["--", filepath])
    res = run_git_command(repo_path, args)
    if res.returncode == 0:
        return res.stdout if res.stdout else "Sin cambios detectados."
    return res.stderr

def get_commit_diff(repo_path: str, commit_hash: str, filepath: Optional[str] = None) -> str:
    """Obtiene el diff completo de un commit o de un archivo dentro del commit."""
    args = ["show", commit_hash]
    if filepath:
        args.extend(["--", filepath])
    res = run_git_command(repo_path, args)
    if res.returncode == 0:
        return res.stdout
    return res.stderr

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
    """Agrega un patrón o nombre de archivo al .gitignore si no existe aún."""
    pattern = pattern.strip()
    if not pattern:
        return False
    current_content = get_gitignore_content(repo_path)
    lines = [line.strip() for line in current_content.splitlines()]
    if pattern in lines:
        return True  # Ya existe

    new_content = current_content
    if current_content and not current_content.endswith("\n"):
        new_content += "\n"
    new_content += pattern + "\n"
    return save_gitignore_content(repo_path, new_content)
