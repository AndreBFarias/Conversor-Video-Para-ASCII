import logging
import os
import subprocess
import tempfile

logger = logging.getLogger(__name__)


class FileAttachmentHandler:
    def __init__(self, app):
        self.app = app
        self.attached_file_path = None
        self.attached_file_content = None
        self.attached_root_dir = None

    def clear_attachments(self):
        self.attached_file_path = None
        self.attached_file_content = None
        self.attached_root_dir = None

    async def handle_attachment(self):
        temp_dir_obj = None

        try:
            choice_proc = subprocess.run(
                [
                    "zenity",
                    "--list",
                    "--title=Anexar Conteudo",
                    "--text=O que deseja anexar?",
                    "--column=Tipo",
                    "Arquivos",
                    "Pasta (Projeto)",
                    "GitHub Repo",
                ],
                capture_output=True,
                text=True,
            )
            choice = choice_proc.stdout.strip()

            if not choice:
                logger.info("Usuario cancelou selecao de tipo.")
                return None, None, None

            paths = []
            root_dir_for_rel_path = None

            if choice == "GitHub Repo":
                url_proc = subprocess.run(
                    [
                        "zenity",
                        "--entry",
                        "--title=GitHub Repo",
                        "--text=Cole a URL do repositorio (ex: https://github.com/user/repo)",
                    ],
                    capture_output=True,
                    text=True,
                )
                repo_url = url_proc.stdout.strip()
                if not repo_url:
                    return None, None, None

                self.app.add_chat_entry("kernel", f"Clonando {repo_url}...")
                logger.info(f"Clonando {repo_url}...")

                temp_dir_obj = tempfile.TemporaryDirectory()
                temp_path = temp_dir_obj.name

                try:
                    subprocess.run(
                        ["git", "clone", "--depth", "1", repo_url, temp_path], check=True, capture_output=True
                    )
                    logger.info("Clone sucesso.")
                    choice = "Pasta (Projeto)"
                    root_dir = temp_path
                except subprocess.CalledProcessError as e:
                    self.app.add_chat_entry("kernel", f"Erro ao clonar: {e}")
                    logger.error(f"Git clone error: {e}")
                    temp_dir_obj.cleanup()
                    return None, None, None

            if choice == "Arquivos":
                proc = subprocess.run(
                    [
                        "zenity",
                        "--file-selection",
                        "--multiple",
                        "--separator=|",
                        "--title=Selecione arquivos (Texto/Codigo)",
                        "--file-filter=CODIGO | *.txt *.md *.py *.json *.csv *.log *.css *.html *.js *.sh *.ini",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                paths = proc.stdout.strip().split("|")

            elif choice == "Pasta (Projeto)":
                if "root_dir" not in locals():
                    proc = subprocess.run(
                        ["zenity", "--file-selection", "--directory", "--title=Selecione a pasta do projeto"],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    root_dir = proc.stdout.strip()

                if root_dir:
                    root_dir_for_rel_path = root_dir
                    for root, dirs, files in os.walk(root_dir):
                        dirs[:] = [
                            d
                            for d in dirs
                            if d
                            not in [
                                "venv",
                                ".git",
                                "__pycache__",
                                "node_modules",
                                ".idea",
                                ".vscode",
                                "build",
                                "dist",
                                "egg-info",
                                ".github",
                            ]
                        ]

                        for file in files:
                            if any(
                                file.endswith(ext)
                                for ext in [
                                    ".txt",
                                    ".md",
                                    ".py",
                                    ".json",
                                    ".csv",
                                    ".log",
                                    ".css",
                                    ".html",
                                    ".js",
                                    ".sh",
                                    ".ini",
                                    ".yaml",
                                    ".yml",
                                    ".toml",
                                ]
                            ):
                                paths.append(os.path.join(root, file))

            if not paths:
                logger.warning("Nenhum arquivo valido selecionado/encontrado.")
                self.app.add_chat_entry("kernel", "Nenhum arquivo valido encontrado para anexar.")
                if temp_dir_obj:
                    temp_dir_obj.cleanup()
                return None, None, None

            file_tree = []
            files_data = []

            total_tokens_est = 0

            for p in paths:
                if not os.path.exists(p):
                    continue

                if root_dir_for_rel_path:
                    rel_path = os.path.relpath(p, root_dir_for_rel_path)
                else:
                    rel_path = os.path.basename(p)

                file_tree.append(rel_path)

                try:
                    size = os.path.getsize(p)
                    if size > 100 * 1024:
                        with open(p, encoding="utf-8", errors="ignore") as f:
                            head = f.read(2000)
                            f.seek(size - 2000)
                            tail = f.read(2000)
                            content = f"{head}\n... [CONTEUDO TRUNCADO: Total {size} bytes] ...\n{tail}"
                    else:
                        with open(p, encoding="utf-8", errors="ignore") as f:
                            content = f.read()

                    files_data.append((rel_path, content))
                    total_tokens_est += len(content) // 4

                except Exception as e:
                    logger.error(f"Erro ao ler {p}: {e}")
                    files_data.append((rel_path, f"[Erro ao ler: {e}]"))

            if files_data:
                combined_content = (
                    "ESTRUTURA DE ARQUIVOS:\n" + "\n".join(f"- {f}" for f in file_tree) + "\n\nCONTEUDO DOS ARQUIVOS:\n"
                )

                current_size = 0
                MAX_CHARS = 100000

                for path, content in files_data:
                    entry = f"\n--- ARQUIVO: {path} ---\n{content}\n"
                    if current_size + len(entry) > MAX_CHARS:
                        combined_content += f"\n[... Limite de contexto atingido. Arquivo {path} omitido ...]"
                        break
                    combined_content += entry
                    current_size += len(entry)

                self.attached_file_content = combined_content
                self.attached_file_path = (
                    f"Projeto ({len(files_data)} arquivos)" if root_dir_for_rel_path else "Multiplos Arquivos"
                )

                if root_dir_for_rel_path:
                    self.attached_root_dir = root_dir_for_rel_path

                msg_sys = f"Anexado: {len(file_tree)} arquivos. Contexto otimizado (~{current_size} chars)."
                self.app.add_chat_entry("kernel", msg_sys)
                logger.info(msg_sys)
                self.app.query_one("#main_input").focus()

                return self.attached_file_content, self.attached_file_path, self.attached_root_dir
            else:
                self.app.add_chat_entry("kernel", "Falha ao ler conteudos.")
                return None, None, None

        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("Zenity cancelado ou nao encontrado.")
            return None, None, None
        except Exception as e:
            logger.error(f"Erro inesperado ao anexar: {e}", exc_info=True)
            self.app.add_chat_entry("kernel", f"Erro ao anexar: {e}")
            return None, None, None
        finally:
            if temp_dir_obj:
                temp_dir_obj.cleanup()
                logger.info("Diretorio temporario limpo.")
