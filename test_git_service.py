import os
import shutil
import tempfile
import unittest
import subprocess
import git_service

class TestGitService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        # Inicializar repositorio git temporal
        subprocess.run(["git", "init"], cwd=self.temp_dir, capture_output=True, check=True)
        # Configurar usuario local para git
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.temp_dir, check=True)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_is_git_repo(self):
        self.assertTrue(git_service.is_git_repo(self.temp_dir))
        self.assertFalse(git_service.is_git_repo("/path/that/does/not/exist_123456"))

    def test_gitignore_operations(self):
        # Inicialmente vacío
        content = git_service.get_gitignore_content(self.temp_dir)
        self.assertEqual(content, "")

        # Añadir patrón
        success = git_service.add_to_gitignore(self.temp_dir, "*.log")
        self.assertTrue(success)
        self.assertIn("*.log", git_service.get_gitignore_content(self.temp_dir))

        # Añadir duplicado
        git_service.add_to_gitignore(self.temp_dir, "*.log")
        lines = git_service.get_gitignore_content(self.temp_dir).strip().splitlines()
        self.assertEqual(lines.count("*.log"), 1)

    def test_status_stage_commit_history(self):
        # Crear archivo no seguido
        file1 = os.path.join(self.temp_dir, "file1.txt")
        with open(file1, "w") as f:
            f.write("hello world")

        status = git_service.get_status(self.temp_dir)
        self.assertEqual(len(status["untracked"]), 1)
        self.assertEqual(status["untracked"][0]["path"], "file1.txt")

        # Staging
        staged_ok = git_service.stage_files(self.temp_dir, ["file1.txt"])
        self.assertTrue(staged_ok)

        status = git_service.get_status(self.temp_dir)
        self.assertEqual(len(status["staged"]), 1)

        # Unstaging
        unstage_ok = git_service.unstage_files(self.temp_dir, ["file1.txt"])
        self.assertTrue(unstage_ok)

        status = git_service.get_status(self.temp_dir)
        self.assertEqual(len(status["staged"]), 0)

        # Stage and commit
        git_service.stage_files(self.temp_dir, ["file1.txt"])
        commit_ok, msg = git_service.create_commit(self.temp_dir, "Initial commit")
        self.assertTrue(commit_ok)

        history = git_service.get_commit_history(self.temp_dir)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["message"], "Initial commit")

        # Check affected files in commit
        files = git_service.get_commit_files(self.temp_dir, history[0]["hash"])
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["path"], "file1.txt")

    def test_recent_repos_save_load(self):
        # Probar guardado y carga de repositorios recientes
        git_service.save_recent_repo(self.temp_dir)
        recent = git_service.load_recent_repos()
        self.assertIn(os.path.abspath(self.temp_dir), recent)

if __name__ == "__main__":
    unittest.main()
