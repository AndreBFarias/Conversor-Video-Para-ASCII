#!/usr/bin/env python3
import argparse
import configparser
import os
import shutil
import subprocess
import sys
import tempfile


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.app.constants import (
    QUALITY_PRESETS, STYLE_PRESETS, LUMINANCE_RAMPS,
    FIXED_PALETTES, BIT_PRESETS, DEFAULT_CONFIG_PATH,
    CONFIG_PATH, VIDEO_EXTENSIONS, IMAGE_EXTENSIONS
)

DEFAULT_OUTPUT_DIR = os.path.join(ROOT_DIR, "data_output")


def _resolve_config_path(args_config: str | None) -> str:
    if args_config:
        return os.path.abspath(args_config)
    if os.path.exists(CONFIG_PATH):
        return CONFIG_PATH
    if os.path.exists(DEFAULT_CONFIG_PATH):
        return DEFAULT_CONFIG_PATH
    print("[FAIL] config.ini nao encontrado", file=sys.stderr)
    sys.exit(1)


def _load_config(config_path: str) -> configparser.ConfigParser:
    config = configparser.ConfigParser(interpolation=None)
    config.read(config_path, encoding='utf-8')
    return config


def _apply_overrides(config: configparser.ConfigParser, args: argparse.Namespace) -> None:
    if hasattr(args, 'quality') and args.quality and args.quality != 'custom':
        preset = QUALITY_PRESETS[args.quality]
        config.set('Conversor', 'target_width', str(preset['width']))
        config.set('Conversor', 'target_height', str(preset['height']))
        config.set('Conversor', 'char_aspect_ratio', str(preset['aspect']))
        config.set('Quality', 'preset', args.quality)

    if hasattr(args, 'style') and args.style:
        preset = STYLE_PRESETS[args.style]
        config.set('Conversor', 'luminance_ramp', preset['luminance_ramp'])
        config.set('Conversor', 'sobel_threshold', str(preset['sobel']))
        config.set('Conversor', 'sharpen_amount', str(preset['sharpen_amount']))
        config.set('Conversor', 'char_aspect_ratio', str(preset['aspect']))

    if hasattr(args, 'luminance') and args.luminance:
        ramp = LUMINANCE_RAMPS[args.luminance]['ramp']
        config.set('Conversor', 'luminance_ramp', ramp)
        config.set('Conversor', 'luminance_preset', args.luminance)

    if hasattr(args, 'width') and args.width:
        config.set('Conversor', 'target_width', str(args.width))

    if hasattr(args, 'height') and args.height:
        config.set('Conversor', 'target_height', str(args.height))

    if hasattr(args, 'gpu') and args.gpu is not None:
        config.set('Conversor', 'gpu_enabled', str(args.gpu).lower())

    if hasattr(args, 'mode') and args.mode:
        config.set('Mode', 'conversion_mode', args.mode)

    if hasattr(args, 'format') and args.format:
        fmt = args.format
        if fmt == 'png':
            fmt = 'png_first'
        config.set('Output', 'format', fmt)

    if hasattr(args, 'no_preview') and args.no_preview:
        if not config.has_section('Preview'):
            config.add_section('Preview')
        config.set('Preview', 'preview_during_conversion', 'false')


def _detect_input_type(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    return "unknown"


def _print_header(text: str) -> None:
    print(f"\n{text}")
    print("=" * len(text))


def _print_ok(label: str, detail: str = "") -> None:
    suffix = f" -- {detail}" if detail else ""
    print(f"  [OK]   {label}{suffix}")


def _print_fail(label: str, detail: str = "") -> None:
    suffix = f" -- {detail}" if detail else ""
    print(f"  [FAIL] {label}{suffix}")


def cli_progress(current: int, total: int, frame_data=None) -> None:
    if total <= 0:
        return
    pct = (current / total) * 100
    filled = int(40 * current / total)
    bar = "=" * filled + "-" * (40 - filled)
    sys.stdout.write(f"\r  [{bar}] {pct:5.1f}% ({current}/{total})")
    sys.stdout.flush()
    if current >= total:
        print()


def _convert_single(file_path: str, input_type: str, output_dir: str,
                     config: configparser.ConfigParser) -> int:
    output_format = config.get('Output', 'format', fallback='txt').lower()
    conversion_mode = config.get('Mode', 'conversion_mode', fallback='ascii').lower()

    nome_base = os.path.splitext(os.path.basename(file_path))[0]
    _print_header(f"Convertendo: {os.path.basename(file_path)}")
    print(f"  Formato: {output_format} | Modo: {conversion_mode} | Saida: {output_dir}")

    try:
        if output_format == 'mp4' and input_type == 'video':
            gpu_enabled = config.getboolean('Conversor', 'gpu_enabled', fallback=True)
            if gpu_enabled:
                try:
                    from src.core.gpu_converter import converter_video_para_mp4_gpu
                    result = converter_video_para_mp4_gpu(
                        file_path, output_dir, config, progress_callback=cli_progress
                    )
                except ImportError:
                    print("  GPU nao disponivel (cupy), usando CPU...")
                    from src.core.mp4_converter import converter_video_para_mp4
                    result = converter_video_para_mp4(
                        file_path, output_dir, config, progress_callback=cli_progress
                    )
            else:
                from src.core.mp4_converter import converter_video_para_mp4
                result = converter_video_para_mp4(
                    file_path, output_dir, config, progress_callback=cli_progress
                )

        elif output_format == 'gif' and input_type == 'video':
            from src.core.gif_converter import converter_video_para_gif
            result = converter_video_para_gif(
                file_path, output_dir, config, progress_callback=cli_progress
            )

        elif output_format == 'html' and input_type == 'video':
            from src.core.html_converter import converter_video_para_html
            result = converter_video_para_html(
                file_path, output_dir, config, progress_callback=cli_progress
            )

        elif output_format == 'png_first' and input_type == 'video':
            from src.core.png_converter import converter_video_para_png_primeiro
            result = converter_video_para_png_primeiro(
                file_path, output_dir, config, progress_callback=cli_progress
            )

        elif output_format == 'png_all' and input_type == 'video':
            from src.core.png_converter import converter_video_para_png_todos
            result = converter_video_para_png_todos(
                file_path, output_dir, config, progress_callback=cli_progress
            )

        elif output_format in ('png_first', 'png_all') and input_type == 'image':
            from src.core.png_converter import converter_imagem_para_png
            result = converter_imagem_para_png(file_path, output_dir, config)

        elif input_type == 'image':
            if conversion_mode == 'pixelart':
                from src.core.pixel_art_image_converter import iniciar_conversao_imagem
                result = iniciar_conversao_imagem(file_path, output_dir, config)
            else:
                from src.core.image_converter import iniciar_conversao_imagem
                result = iniciar_conversao_imagem(file_path, output_dir, config)

        elif input_type == 'video':
            if conversion_mode == 'pixelart':
                from src.core.pixel_art_converter import iniciar_conversao
                result = iniciar_conversao(file_path, output_dir, config)
            else:
                from src.core.converter import iniciar_conversao
                result = iniciar_conversao(file_path, output_dir, config)

        else:
            print(f"[FAIL] Combinacao nao suportada: format={output_format}, type={input_type}", file=sys.stderr)
            return 1

        print(f"\n  Concluido: {result}")
        return 0

    except Exception as e:
        print(f"\n[FAIL] Erro na conversao: {e}", file=sys.stderr)
        return 1


def cmd_convert(args: argparse.Namespace) -> int:
    config_path = _resolve_config_path(args.config)
    config = _load_config(config_path)
    _apply_overrides(config, args)

    if args.folder:
        folder_path = os.path.abspath(args.folder)
        if not os.path.isdir(folder_path):
            print(f"[FAIL] Pasta nao encontrada: {folder_path}", file=sys.stderr)
            return 1

        output_dir = args.output or config.get('Pastas', 'output_dir', fallback='') or DEFAULT_OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)

        files = sorted([
            os.path.join(folder_path, f)
            for f in os.listdir(folder_path)
            if os.path.splitext(f)[1].lower() in VIDEO_EXTENSIONS + IMAGE_EXTENSIONS
        ])

        if not files:
            print(f"[FAIL] Nenhum arquivo de midia encontrado em: {folder_path}", file=sys.stderr)
            return 1

        _print_header(f"Conversao em lote: {len(files)} arquivo(s)")
        errors = 0
        for i, fp in enumerate(files, 1):
            print(f"\n  [{i}/{len(files)}]")
            input_type = _detect_input_type(fp)
            if input_type == "unknown":
                print(f"  [SKIP] Formato nao reconhecido: {os.path.basename(fp)}")
                continue
            rc = _convert_single(fp, input_type, output_dir, config)
            if rc != 0:
                errors += 1

        _print_header("Resultado do Lote")
        print(f"  {len(files) - errors}/{len(files)} concluidos com sucesso")
        return 1 if errors > 0 else 0

    if args.video and args.image:
        print("[FAIL] Use --video ou --image, nao ambos", file=sys.stderr)
        return 1

    file_path = args.video or args.image
    if not file_path:
        print("[FAIL] Especifique --video, --image ou --folder", file=sys.stderr)
        return 1

    if not os.path.exists(file_path):
        print(f"[FAIL] Arquivo nao encontrado: {file_path}", file=sys.stderr)
        return 1

    input_type = _detect_input_type(file_path)
    if input_type == "unknown":
        if args.video:
            input_type = "video"
        elif args.image:
            input_type = "image"
        else:
            print(f"[FAIL] Extensao nao reconhecida: {file_path}", file=sys.stderr)
            return 1

    output_dir = args.output or config.get('Pastas', 'output_dir', fallback='') or DEFAULT_OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)

    return _convert_single(file_path, input_type, output_dir, config)


def cmd_config(args: argparse.Namespace) -> int:
    config_path = _resolve_config_path(args.config)
    config = _load_config(config_path)

    sub = args.config_cmd

    if sub == 'show':
        _print_header(f"Config: {config_path}")
        for section in config.sections():
            print(f"\n  [{section}]")
            for key, value in config.items(section):
                print(f"    {key} = {value}")
        return 0

    if sub == 'get':
        if not config.has_section(args.section):
            print(f"[FAIL] Secao nao existe: {args.section}", file=sys.stderr)
            return 1
        if not config.has_option(args.section, args.key):
            print(f"[FAIL] Chave nao existe: [{args.section}] {args.key}", file=sys.stderr)
            return 1
        print(config.get(args.section, args.key))
        return 0

    if sub == 'set':
        if not config.has_section(args.section):
            config.add_section(args.section)
        config.set(args.section, args.key, args.value)
        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)
        print(f"  [{args.section}] {args.key} = {args.value}")
        return 0

    if sub == 'reset':
        default_path = os.path.join(ROOT_DIR, "config.ini")
        if config_path != default_path and os.path.exists(default_path):
            shutil.copy(default_path, config_path)
            print(f"  Config restaurado de: {default_path}")
        else:
            print("  Nenhum default disponivel para restaurar")
        return 0

    if sub == 'presets':
        _print_header("Quality Presets")
        for name, p in QUALITY_PRESETS.items():
            print(f"  {name:12s} -> {p['width']}x{p['height']} aspect={p['aspect']}")

        _print_header("Style Presets")
        for name, p in STYLE_PRESETS.items():
            print(f"  {name:16s} -> {p['name']} (sobel={p['sobel']}, sharpen={p['sharpen_amount']})")

        _print_header("Luminance Ramps")
        for name, p in LUMINANCE_RAMPS.items():
            print(f"  {name:12s} -> {p['name']}")

        _print_header("Fixed Palettes (Pixel Art)")
        for name, p in FIXED_PALETTES.items():
            print(f"  {name:16s} -> {p['name']} ({len(p['colors'])} cores)")

        _print_header("Bit Presets (Pixel Art)")
        for name, p in BIT_PRESETS.items():
            print(f"  {name:12s} -> pixel_size={p['pixel_size']}, palette={p['palette_size']}")

        return 0

    print(f"[FAIL] Subcomando desconhecido: {sub}", file=sys.stderr)
    return 1


def cmd_validate(args: argparse.Namespace) -> int:
    config_path = _resolve_config_path(args.config)
    config = _load_config(config_path)
    video_path = args.video
    ok_count = 0
    fail_count = 0

    _print_header("Extase em 4R73 - Validacao")

    # 1. Config Integrity
    expected_sections = [
        'Conversor', 'Geral', 'Quality', 'Pastas', 'Player', 'ChromaKey',
        'Mode', 'PixelArt', 'Output', 'Preview', 'MatrixRain', 'PostFX',
        'Style', 'OpticalFlow', 'Audio', 'Interface'
    ]
    missing = [s for s in expected_sections if not config.has_section(s)]
    if not missing:
        _print_ok("Config Integrity", f"{len(expected_sections)} secoes encontradas")
        ok_count += 1
    else:
        _print_fail("Config Integrity", f"faltando: {', '.join(missing)}")
        fail_count += 1

    # 2. ffmpeg/ffprobe
    ffmpeg_path = shutil.which('ffmpeg')
    ffprobe_path = shutil.which('ffprobe')
    if ffmpeg_path and ffprobe_path:
        try:
            ver = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
            version_line = ver.stdout.split('\n')[0] if ver.stdout else 'desconhecida'
            _print_ok("ffmpeg/ffprobe", version_line)
            ok_count += 1
        except Exception as e:
            _print_fail("ffmpeg/ffprobe", str(e))
            fail_count += 1
    else:
        _print_fail("ffmpeg/ffprobe", f"ffmpeg={'ok' if ffmpeg_path else 'FALTANDO'} ffprobe={'ok' if ffprobe_path else 'FALTANDO'}")
        fail_count += 1

    # 3. GPU (cupy)
    try:
        import cupy as cp
        device_name = cp.cuda.runtime.getDeviceProperties(0)['name'].decode('utf-8')
        _print_ok("GPU (cupy)", device_name)
        ok_count += 1
    except ImportError:
        _print_fail("GPU (cupy)", "cupy nao instalado")
        fail_count += 1
    except Exception as e:
        _print_fail("GPU (cupy)", str(e))
        fail_count += 1

    # 4. OpenCV
    try:
        import cv2
        _print_ok("OpenCV", f"v{cv2.__version__}")
        ok_count += 1
    except ImportError:
        _print_fail("OpenCV", "nao instalado")
        fail_count += 1

    # 5. Converter Imports
    converters = [
        ("converter", "src.core.converter"),
        ("image_converter", "src.core.image_converter"),
        ("pixel_art_converter", "src.core.pixel_art_converter"),
        ("pixel_art_image_converter", "src.core.pixel_art_image_converter"),
        ("mp4_converter", "src.core.mp4_converter"),
        ("gpu_converter", "src.core.gpu_converter"),
        ("gif_converter", "src.core.gif_converter"),
        ("html_converter", "src.core.html_converter"),
        ("png_converter", "src.core.png_converter"),
    ]
    conv_ok = 0
    conv_fail = 0
    for name, module_path in converters:
        try:
            __import__(module_path)
            conv_ok += 1
        except ImportError as e:
            _print_fail(f"  Import {name}", str(e))
            conv_fail += 1
        except Exception as e:
            _print_fail(f"  Import {name}", str(e))
            conv_fail += 1

    if conv_fail == 0:
        _print_ok("Converter Imports", f"{conv_ok}/{len(converters)} ok")
        ok_count += 1
    else:
        _print_fail("Converter Imports", f"{conv_ok}/{len(converters)} ok, {conv_fail} falhas")
        fail_count += 1

    # 6. audio_utils
    try:
        from src.core.audio_utils import extract_audio_as_aac, mux_video_audio
        _print_ok("audio_utils", "extract_audio_as_aac, mux_video_audio")
        ok_count += 1
    except ImportError as e:
        _print_fail("audio_utils", str(e))
        fail_count += 1

    # 7. Output dir
    output_dir = config.get('Pastas', 'output_dir', fallback='') or DEFAULT_OUTPUT_DIR
    if os.path.isdir(output_dir) and os.access(output_dir, os.W_OK):
        _print_ok("Output Dir", output_dir)
        ok_count += 1
    else:
        try:
            os.makedirs(output_dir, exist_ok=True)
            _print_ok("Output Dir", f"{output_dir} (criado)")
            ok_count += 1
        except Exception as e:
            _print_fail("Output Dir", str(e))
            fail_count += 1

    # Checks que precisam de video real
    if video_path:
        if not os.path.exists(video_path):
            _print_fail("Video de teste", f"nao encontrado: {video_path}")
            fail_count += 1
        else:
            # 8. Audio Pipeline
            try:
                from src.core.audio_utils import extract_audio_as_aac
                temp_dir = tempfile.mkdtemp(prefix="cli_validate_")
                audio_file = extract_audio_as_aac(video_path, temp_dir)
                if audio_file and os.path.exists(audio_file):
                    size_kb = os.path.getsize(audio_file) / 1024
                    _print_ok("Audio Pipeline", f"extraido {size_kb:.0f}KB")
                    ok_count += 1
                else:
                    _print_ok("Audio Pipeline", "video sem audio (comportamento correto)")
                    ok_count += 1
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                _print_fail("Audio Pipeline", str(e))
                fail_count += 1

            # 9. MP4 Pipeline
            try:
                from src.core.mp4_converter import converter_video_para_mp4
                test_output = os.path.join(DEFAULT_OUTPUT_DIR, "_cli_validate_test.mp4")
                os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
                result_file = converter_video_para_mp4(
                    video_path, DEFAULT_OUTPUT_DIR, config, progress_callback=cli_progress
                )
                if os.path.exists(result_file):
                    probe = subprocess.run(
                        ['ffprobe', '-i', result_file, '-show_streams',
                         '-select_streams', 'a', '-loglevel', 'error'],
                        capture_output=True, text=True
                    )
                    has_audio = bool(probe.stdout.strip())
                    size_mb = os.path.getsize(result_file) / (1024 * 1024)
                    _print_ok("MP4 Pipeline", f"{size_mb:.1f}MB, audio={'sim' if has_audio else 'nao'}")
                    ok_count += 1
                    os.remove(result_file)
                else:
                    _print_fail("MP4 Pipeline", "arquivo de saida nao criado")
                    fail_count += 1
            except Exception as e:
                _print_fail("MP4 Pipeline", str(e))
                fail_count += 1

            # 10. HTML Audio
            try:
                from src.core.html_converter import converter_video_para_html
                result_file = converter_video_para_html(
                    video_path, DEFAULT_OUTPUT_DIR, config, progress_callback=cli_progress
                )
                if os.path.exists(result_file):
                    nome_base = os.path.splitext(os.path.basename(video_path))[0]
                    mp3_path = os.path.join(DEFAULT_OUTPUT_DIR, f"{nome_base}_player.mp3")
                    has_mp3 = os.path.exists(mp3_path)
                    _print_ok("HTML Audio", f"html={'ok'}, mp3={'encontrado' if has_mp3 else 'nao encontrado'}")
                    ok_count += 1
                    os.remove(result_file)
                    if has_mp3:
                        os.remove(mp3_path)
                else:
                    _print_fail("HTML Audio", "arquivo HTML nao criado")
                    fail_count += 1
            except Exception as e:
                _print_fail("HTML Audio", str(e))
                fail_count += 1
    else:
        print("\n  (Checks 8-10 pulados: use --video para testar pipelines com video real)")

    # 11. Settings Sync
    settings_checks = {
        'MatrixRain': ['enabled', 'mode', 'char_set', 'num_particles', 'speed_multiplier'],
        'PostFX': ['bloom_enabled', 'chromatic_enabled', 'scanlines_enabled', 'glitch_enabled'],
        'OpticalFlow': ['enabled', 'target_fps', 'quality'],
        'Audio': ['enabled', 'sample_rate', 'chunk_size'],
    }
    settings_missing = []
    for section, keys in settings_checks.items():
        if not config.has_section(section):
            settings_missing.append(f"[{section}] (secao inteira)")
            continue
        for key in keys:
            if not config.has_option(section, key):
                settings_missing.append(f"[{section}] {key}")

    if not settings_missing:
        _print_ok("Settings Sync", "MatrixRain, PostFX, OpticalFlow, Audio ok")
        ok_count += 1
    else:
        _print_fail("Settings Sync", f"faltando: {', '.join(settings_missing)}")
        fail_count += 1

    _print_header("Resultado")
    total = ok_count + fail_count
    print(f"  {ok_count}/{total} checks passaram")
    if fail_count > 0:
        print(f"  {fail_count} falha(s)")
    return 0 if fail_count == 0 else 1


def cmd_info(args: argparse.Namespace) -> int:
    config_path = _resolve_config_path(args.config)
    config = _load_config(config_path)

    _print_header("Extase em 4R73 - Diagnostico")

    print(f"  Config        : {config_path}")
    print(f"  Input Dir     : {config.get('Pastas', 'input_dir', fallback='(nao definido)')}")
    print(f"  Output Dir    : {config.get('Pastas', 'output_dir', fallback=DEFAULT_OUTPUT_DIR)}")

    try:
        import cupy as cp
        device_name = cp.cuda.runtime.getDeviceProperties(0)['name'].decode('utf-8')
        print(f"  GPU           : {device_name} (cupy ok)")
    except Exception:
        print("  GPU           : nao disponivel")

    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        try:
            ver = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
            version_line = ver.stdout.split('\n')[0].replace('ffmpeg version ', '') if ver.stdout else '?'
            print(f"  ffmpeg        : {version_line}")
        except Exception:
            print("  ffmpeg        : encontrado mas erro ao obter versao")
    else:
        print("  ffmpeg        : nao encontrado")

    try:
        import cv2
        print(f"  OpenCV        : v{cv2.__version__}")
    except ImportError:
        print("  OpenCV        : nao instalado")

    print(f"  Python        : {sys.version.split()[0]}")

    _print_header("Configuracao Atual")
    fmt = config.get('Output', 'format', fallback='txt')
    mode = config.get('Mode', 'conversion_mode', fallback='ascii')
    w = config.get('Conversor', 'target_width', fallback='?')
    h = config.get('Conversor', 'target_height', fallback='?')
    quality = config.get('Quality', 'preset', fallback='custom')
    gpu = config.get('Conversor', 'gpu_enabled', fallback='true')
    lum_preset = config.get('Conversor', 'luminance_preset', fallback='standard')

    postfx_items = []
    if config.getboolean('PostFX', 'bloom_enabled', fallback=False):
        postfx_items.append('bloom')
    if config.getboolean('PostFX', 'chromatic_enabled', fallback=False):
        postfx_items.append('chromatic')
    if config.getboolean('PostFX', 'scanlines_enabled', fallback=False):
        postfx_items.append('scanlines')
    if config.getboolean('PostFX', 'glitch_enabled', fallback=False):
        postfx_items.append('glitch')
    postfx_str = ', '.join(postfx_items) if postfx_items else 'nenhum'

    matrix = 'habilitado' if config.getboolean('MatrixRain', 'enabled', fallback=False) else 'desabilitado'
    optical = 'habilitado' if config.getboolean('OpticalFlow', 'enabled', fallback=False) else 'desabilitado'
    audio = 'habilitado' if config.getboolean('Audio', 'enabled', fallback=False) else 'desabilitado'

    print(f"  Formato       : {fmt}")
    print(f"  Modo          : {mode}")
    print(f"  Qualidade     : {quality} ({w}x{h})")
    print(f"  GPU           : {'habilitado' if gpu.lower() == 'true' else 'desabilitado'}")
    print(f"  Luminance     : {lum_preset}")
    print(f"  PostFX        : {postfx_str}")
    print(f"  MatrixRain    : {matrix}")
    print(f"  OpticalFlow   : {optical}")
    print(f"  Audio React   : {audio}")

    _print_header("Converters Disponiveis")
    converter_list = [
        ("converter.py", "src.core.converter", "ASCII TXT"),
        ("image_converter.py", "src.core.image_converter", "ASCII TXT (imagem)"),
        ("pixel_art_converter.py", "src.core.pixel_art_converter", "Pixel Art TXT"),
        ("pixel_art_image_converter.py", "src.core.pixel_art_image_converter", "Pixel Art TXT (imagem)"),
        ("mp4_converter.py", "src.core.mp4_converter", "CPU MP4"),
        ("gpu_converter.py", "src.core.gpu_converter", "GPU MP4"),
        ("gif_converter.py", "src.core.gif_converter", "GIF"),
        ("html_converter.py", "src.core.html_converter", "HTML Player"),
        ("png_converter.py", "src.core.png_converter", "PNG"),
    ]
    for filename, module_path, desc in converter_list:
        try:
            __import__(module_path)
            _print_ok(f"{filename}", desc)
        except ImportError as e:
            _print_fail(f"{filename}", f"{desc} -- {e}")
        except Exception as e:
            _print_fail(f"{filename}", f"{desc} -- {e}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="Extase em 4R73 - CLI Unificado"
    )
    subparsers = parser.add_subparsers(dest='command', help='Subcomandos disponiveis')

    # convert
    p_convert = subparsers.add_parser('convert', help='Converte video/imagem')
    p_convert.add_argument('--video', type=str, help='Caminho do video de entrada')
    p_convert.add_argument('--image', type=str, help='Caminho da imagem de entrada')
    p_convert.add_argument('--format', choices=['txt', 'mp4', 'gif', 'html', 'png', 'png_all'], help='Formato de saida')
    p_convert.add_argument('--quality', choices=list(QUALITY_PRESETS.keys()) + ['custom'], help='Preset de qualidade')
    p_convert.add_argument('--mode', choices=['ascii', 'pixelart'], help='Modo de conversao')
    p_convert.add_argument('--style', choices=list(STYLE_PRESETS.keys()), help='Preset de estilo')
    p_convert.add_argument('--luminance', choices=list(LUMINANCE_RAMPS.keys()), help='Rampa de luminancia')
    gpu_group = p_convert.add_mutually_exclusive_group()
    gpu_group.add_argument('--gpu', action='store_true', default=None, dest='gpu', help='Forcar GPU')
    gpu_group.add_argument('--no-gpu', action='store_false', dest='gpu', help='Forcar CPU')
    p_convert.add_argument('--no-preview', action='store_true', help='Desabilitar preview durante conversao')
    p_convert.add_argument('--width', type=int, help='Largura em caracteres')
    p_convert.add_argument('--height', type=int, help='Altura em caracteres')
    p_convert.add_argument('--folder', type=str, help='Pasta com videos para conversao em lote')
    p_convert.add_argument('--output', type=str, help='Diretorio de saida')
    p_convert.add_argument('--config', type=str, help='Caminho do config.ini')

    # config
    p_config = subparsers.add_parser('config', help='Gerencia configuracoes')
    config_sub = p_config.add_subparsers(dest='config_cmd')

    config_sub.add_parser('show', help='Mostra todas as configuracoes')
    config_sub.add_parser('presets', help='Lista presets disponiveis')
    config_sub.add_parser('reset', help='Restaura config.ini para defaults')

    p_get = config_sub.add_parser('get', help='Retorna valor de uma chave')
    p_get.add_argument('section', help='Secao do config.ini')
    p_get.add_argument('key', help='Chave')

    p_set = config_sub.add_parser('set', help='Define valor de uma chave')
    p_set.add_argument('section', help='Secao do config.ini')
    p_set.add_argument('key', help='Chave')
    p_set.add_argument('value', help='Valor')

    p_config.add_argument('--config', type=str, help='Caminho do config.ini')

    # validate
    p_validate = subparsers.add_parser('validate', help='Validacao de integridade')
    p_validate.add_argument('--video', type=str, help='Video para testes de pipeline')
    p_validate.add_argument('--config', type=str, help='Caminho do config.ini')

    # info
    p_info = subparsers.add_parser('info', help='Diagnostico do sistema')
    p_info.add_argument('--config', type=str, help='Caminho do config.ini')

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        'convert': cmd_convert,
        'config': cmd_config,
        'validate': cmd_validate,
        'info': cmd_info,
    }

    handler = dispatch.get(args.command)
    if not handler:
        parser.print_help()
        sys.exit(1)

    sys.exit(handler(args))


if __name__ == '__main__':
    main()

# "A ferramenta e a extensao da vontade." - Ernst Junger
