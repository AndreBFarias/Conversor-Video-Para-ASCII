#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import time
import configparser
import tempfile
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from src.app.constants import (
    CONFIG_PATH, ROOT_DIR, CONVERTER_SCRIPT, IMAGE_CONVERTER_SCRIPT,
    PLAYER_SCRIPT, GTK_CALIBRATOR_SCRIPT, REALTIME_SCRIPT,
    VIDEO_EXTENSIONS, IMAGE_EXTENSIONS, QUALITY_PRESETS
)


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error = None
        self.duration = 0.0


class TUISimulator:
    def __init__(self):
        self.config = configparser.ConfigParser(interpolation=None)
        self.config_path = CONFIG_PATH
        self.results: list[TestResult] = []
        self.test_video = None
        self.test_image = None
        self.output_dir = None
        self.input_dir = None

        self._load_config()
        self._find_test_files()

    def _load_config(self):
        if os.path.exists(self.config_path):
            self.config.read(self.config_path, encoding='utf-8')
            self.input_dir = os.path.abspath(os.path.join(
                ROOT_DIR,
                self.config.get('Pastas', 'input_dir', fallback='data_input')
            ))
            self.output_dir = os.path.abspath(os.path.join(
                ROOT_DIR,
                self.config.get('Pastas', 'output_dir', fallback='data_output')
            ))
        else:
            print(f"{Colors.FAIL}[ERRO] config.ini não encontrado em {self.config_path}{Colors.ENDC}")
            sys.exit(1)

    def _find_test_files(self):
        if os.path.isdir(self.input_dir):
            for root, dirs, files in os.walk(self.input_dir):
                for f in files:
                    path = os.path.join(root, f)
                    if f.lower().endswith(VIDEO_EXTENSIONS) and not self.test_video:
                        self.test_video = path
                    elif f.lower().endswith(IMAGE_EXTENSIONS) and not self.test_image:
                        self.test_image = path
                    if self.test_video and self.test_image:
                        return

    def _print_header(self, text: str):
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}  {text}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

    def _print_test(self, name: str, status: str, duration: float = 0):
        if status == "PASS":
            icon = f"{Colors.GREEN}✓{Colors.ENDC}"
            status_text = f"{Colors.GREEN}PASS{Colors.ENDC}"
        elif status == "FAIL":
            icon = f"{Colors.FAIL}✗{Colors.ENDC}"
            status_text = f"{Colors.FAIL}FAIL{Colors.ENDC}"
        elif status == "SKIP":
            icon = f"{Colors.WARNING}○{Colors.ENDC}"
            status_text = f"{Colors.WARNING}SKIP{Colors.ENDC}"
        else:
            icon = f"{Colors.CYAN}►{Colors.ENDC}"
            status_text = f"{Colors.CYAN}RUN{Colors.ENDC}"

        duration_str = f" ({duration:.2f}s)" if duration > 0 else ""
        print(f"  {icon} {name}: {status_text}{duration_str}")

    def _run_test(self, name: str, test_func) -> TestResult:
        result = TestResult(name)
        self._print_test(name, "RUN")
        start = time.time()

        try:
            test_func()
            result.passed = True
            result.duration = time.time() - start
            self._print_test(name, "PASS", result.duration)
        except AssertionError as e:
            result.error = str(e)
            result.duration = time.time() - start
            self._print_test(name, "FAIL", result.duration)
            print(f"      {Colors.FAIL}Erro: {e}{Colors.ENDC}")
        except Exception as e:
            result.error = str(e)
            result.duration = time.time() - start
            self._print_test(name, "FAIL", result.duration)
            print(f"      {Colors.FAIL}Exceção: {e}{Colors.ENDC}")

        self.results.append(result)
        return result

    def test_config_load(self):
        assert os.path.exists(self.config_path), f"config.ini não existe: {self.config_path}"
        assert self.config.sections(), "config.ini está vazio"
        assert 'Conversor' in self.config, "Seção [Conversor] não encontrada"
        assert 'ChromaKey' in self.config, "Seção [ChromaKey] não encontrada"
        assert 'Pastas' in self.config, "Seção [Pastas] não encontrada"

    def test_directories_exist(self):
        assert os.path.isdir(self.input_dir), f"Pasta input não existe: {self.input_dir}"
        assert os.path.isdir(self.output_dir), f"Pasta output não existe: {self.output_dir}"

    def test_scripts_exist(self):
        scripts = [
            ('converter.py', CONVERTER_SCRIPT),
            ('image_converter.py', IMAGE_CONVERTER_SCRIPT),
            ('cli_player.py', PLAYER_SCRIPT),
            ('gtk_calibrator.py', GTK_CALIBRATOR_SCRIPT),
            ('realtime_ascii.py', REALTIME_SCRIPT),
        ]
        for name, path in scripts:
            assert os.path.exists(path), f"Script {name} não encontrado: {path}"

    def test_quality_presets(self):
        assert QUALITY_PRESETS, "QUALITY_PRESETS está vazio"
        for preset_id, preset in QUALITY_PRESETS.items():
            assert 'width' in preset, f"Preset {preset_id} sem 'width'"
            assert 'height' in preset, f"Preset {preset_id} sem 'height'"
            assert 'aspect' in preset, f"Preset {preset_id} sem 'aspect'"
            assert 'zoom' in preset, f"Preset {preset_id} sem 'zoom'"

    def test_config_save(self):
        backup_path = self.config_path + '.bak'
        shutil.copy(self.config_path, backup_path)

        try:
            test_value = str(int(time.time()))
            if 'Test' not in self.config:
                self.config.add_section('Test')
            self.config.set('Test', 'timestamp', test_value)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)

            config_reload = configparser.ConfigParser(interpolation=None)
            config_reload.read(self.config_path, encoding='utf-8')

            saved_value = config_reload.get('Test', 'timestamp', fallback=None)
            assert saved_value == test_value, f"Valor salvo não confere: {saved_value} != {test_value}"

        finally:
            shutil.copy(backup_path, self.config_path)
            os.remove(backup_path)
            self.config.read(self.config_path, encoding='utf-8')

    def test_chroma_key_values(self):
        h_min = self.config.getint('ChromaKey', 'h_min', fallback=-1)
        h_max = self.config.getint('ChromaKey', 'h_max', fallback=-1)
        s_min = self.config.getint('ChromaKey', 's_min', fallback=-1)
        s_max = self.config.getint('ChromaKey', 's_max', fallback=-1)

        assert 0 <= h_min <= 179, f"h_min inválido: {h_min}"
        assert 0 <= h_max <= 179, f"h_max inválido: {h_max}"
        assert 0 <= s_min <= 255, f"s_min inválido: {s_min}"
        assert 0 <= s_max <= 255, f"s_max inválido: {s_max}"

    def test_conversor_values(self):
        width = self.config.getint('Conversor', 'target_width', fallback=0)
        height = self.config.getint('Conversor', 'target_height', fallback=-1)
        sobel = self.config.getint('Conversor', 'sobel_threshold', fallback=-1)
        aspect = self.config.getfloat('Conversor', 'char_aspect_ratio', fallback=0)

        assert 40 <= width <= 400, f"target_width inválido: {width}"
        assert height >= 0, f"target_height inválido: {height}"
        assert 0 <= sobel <= 255, f"sobel_threshold inválido: {sobel}"
        assert 0.1 <= aspect <= 2.0, f"char_aspect_ratio inválido: {aspect}"

    def test_video_conversion(self):
        if not self.test_video:
            raise AssertionError("Nenhum vídeo de teste encontrado em data_input/")

        import subprocess

        python_exe = os.path.join(ROOT_DIR, 'venv', 'bin', 'python')
        if not os.path.exists(python_exe):
            python_exe = sys.executable

        cmd = [python_exe, CONVERTER_SCRIPT, '--video', self.test_video, '--config', self.config_path]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        assert result.returncode == 0, f"Conversão falhou: {result.stderr}"

        output_name = os.path.splitext(os.path.basename(self.test_video))[0] + '.txt'
        output_path = os.path.join(self.output_dir, output_name)

        assert os.path.exists(output_path), f"Arquivo de saída não gerado: {output_path}"
        assert os.path.getsize(output_path) > 0, f"Arquivo de saída vazio: {output_path}"

    def test_image_conversion(self):
        if not self.test_image:
            raise AssertionError("Nenhuma imagem de teste encontrada em data_input/")

        import subprocess

        python_exe = os.path.join(ROOT_DIR, 'venv', 'bin', 'python')
        if not os.path.exists(python_exe):
            python_exe = sys.executable

        cmd = [python_exe, IMAGE_CONVERTER_SCRIPT, '--image', self.test_image, '--config', self.config_path]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        assert result.returncode == 0, f"Conversão de imagem falhou: {result.stderr}"

        output_name = os.path.splitext(os.path.basename(self.test_image))[0] + '.txt'
        output_path = os.path.join(self.output_dir, output_name)

        assert os.path.exists(output_path), f"Arquivo de saída não gerado: {output_path}"

    def test_ascii_file_format(self):
        ascii_files = [f for f in os.listdir(self.output_dir) if f.endswith('.txt')]
        assert ascii_files, "Nenhum arquivo ASCII encontrado em data_output/"

        test_file = os.path.join(self.output_dir, ascii_files[0])
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()

        assert content, "Arquivo ASCII vazio"

        has_header = content.startswith('FPS:') or 'FRAME_START' in content or '\033[' in content
        assert has_header or len(content) > 100, "Formato de arquivo ASCII inválido"

    def test_player_script_syntax(self):
        import subprocess

        python_exe = os.path.join(ROOT_DIR, 'venv', 'bin', 'python')
        if not os.path.exists(python_exe):
            python_exe = sys.executable

        cmd = [python_exe, '-m', 'py_compile', PLAYER_SCRIPT]
        result = subprocess.run(cmd, capture_output=True, text=True)

        assert result.returncode == 0, f"Erro de sintaxe em cli_player.py: {result.stderr}"

    def test_loop_config(self):
        loop_val = self.config.get('Player', 'loop', fallback='nao').lower()
        valid_values = ['sim', 'nao', 'yes', 'no', 'true', 'false', '1', '0', 'on', 'off']
        assert loop_val in valid_values, f"Valor de loop inválido: {loop_val}"

    def test_pixel_art_config(self):
        if 'PixelArt' in self.config:
            pixel_size = self.config.getint('PixelArt', 'pixel_size', fallback=1)
            palette_size = self.config.getint('PixelArt', 'color_palette_size', fallback=16)

            assert 1 <= pixel_size <= 16, f"pixel_size inválido: {pixel_size}"
            assert 2 <= palette_size <= 256, f"color_palette_size inválido: {palette_size}"

    def test_mode_config(self):
        if 'Mode' in self.config:
            mode = self.config.get('Mode', 'conversion_mode', fallback='ascii').lower()
            assert mode in ['ascii', 'pixelart'], f"conversion_mode inválido: {mode}"

    def test_utils_imports(self):
        from src.core.utils.color import rgb_to_ansi256
        from src.core.utils.image import sharpen_frame, apply_morphological_refinement
        from src.core.utils.ascii_converter import converter_frame_para_ascii

        color = rgb_to_ansi256(255, 0, 0)
        assert isinstance(color, int), "rgb_to_ansi256 não retornou int"
        assert 16 <= color <= 231, f"Código ANSI inválido: {color}"

    def test_app_imports(self):
        from src.app.constants import QUALITY_PRESETS, VIDEO_EXTENSIONS
        from src.app.actions.file_actions import FileActionsMixin
        from src.app.actions.conversion_actions import ConversionActionsMixin
        from src.app.actions.playback_actions import PlaybackActionsMixin
        from src.app.actions.calibration_actions import CalibrationActionsMixin
        from src.app.actions.options_actions import OptionsActionsMixin

        assert QUALITY_PRESETS, "QUALITY_PRESETS vazio"
        assert VIDEO_EXTENSIONS, "VIDEO_EXTENSIONS vazio"

    def run_all_tests(self):
        self._print_header("SIMULADOR TUI - TESTES DE INTEGRAÇÃO")

        print(f"{Colors.CYAN}Ambiente:{Colors.ENDC}")
        print(f"  Config: {self.config_path}")
        print(f"  Input:  {self.input_dir}")
        print(f"  Output: {self.output_dir}")
        print(f"  Vídeo:  {self.test_video or 'Não encontrado'}")
        print(f"  Imagem: {self.test_image or 'Não encontrada'}")

        self._print_header("1. TESTES DE CONFIGURAÇÃO")
        self._run_test("Carregar config.ini", self.test_config_load)
        self._run_test("Verificar diretórios", self.test_directories_exist)
        self._run_test("Verificar scripts", self.test_scripts_exist)
        self._run_test("Verificar presets de qualidade", self.test_quality_presets)

        self._print_header("2. TESTES DE VALORES")
        self._run_test("Valores ChromaKey válidos", self.test_chroma_key_values)
        self._run_test("Valores Conversor válidos", self.test_conversor_values)
        self._run_test("Configuração de loop", self.test_loop_config)
        self._run_test("Configuração Pixel Art", self.test_pixel_art_config)
        self._run_test("Configuração de modo", self.test_mode_config)

        self._print_header("3. TESTES DE SALVAMENTO")
        self._run_test("Salvar e recarregar config", self.test_config_save)

        self._print_header("4. TESTES DE IMPORTS")
        self._run_test("Importar utils", self.test_utils_imports)
        self._run_test("Importar app modules", self.test_app_imports)

        self._print_header("5. TESTES DE CONVERSÃO")
        self._run_test("Sintaxe cli_player.py", self.test_player_script_syntax)

        if self.test_video:
            self._run_test("Conversão de vídeo", self.test_video_conversion)
        else:
            print(f"  {Colors.WARNING}○ Conversão de vídeo: SKIP (sem vídeo de teste){Colors.ENDC}")

        if self.test_image:
            self._run_test("Conversão de imagem", self.test_image_conversion)
        else:
            print(f"  {Colors.WARNING}○ Conversão de imagem: SKIP (sem imagem de teste){Colors.ENDC}")

        self._print_header("6. TESTES DE FORMATO")
        try:
            self._run_test("Formato arquivo ASCII", self.test_ascii_file_format)
        except:
            print(f"  {Colors.WARNING}○ Formato arquivo ASCII: SKIP (sem arquivos){Colors.ENDC}")

        self._print_summary()

    def _print_summary(self):
        self._print_header("RESUMO")

        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)
        total_time = sum(r.duration for r in self.results)

        print(f"  Total:    {total} testes")
        print(f"  {Colors.GREEN}Passou:   {passed}{Colors.ENDC}")
        print(f"  {Colors.FAIL}Falhou:   {failed}{Colors.ENDC}")
        print(f"  Tempo:    {total_time:.2f}s")
        print()

        if failed > 0:
            print(f"{Colors.FAIL}Testes que falharam:{Colors.ENDC}")
            for r in self.results:
                if not r.passed:
                    print(f"  - {r.name}: {r.error}")
            print()

        if failed == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ TODOS OS TESTES PASSARAM!{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}{Colors.BOLD}✗ {failed} TESTE(S) FALHOU(ARAM){Colors.ENDC}")

        return failed == 0


def main():
    print(f"\n{Colors.BOLD}Iniciando Simulador TUI...{Colors.ENDC}\n")

    simulator = TUISimulator()
    success = simulator.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
