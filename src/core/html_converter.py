#!/usr/bin/env python3
import cv2
import os
import sys
import subprocess
import logging
import numpy as np
import configparser
import json
import zlib
import base64

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.core.utils.image import sharpen_frame, apply_morphological_refinement
from src.core.utils.ascii_converter import converter_frame_para_ascii, LUMINANCE_RAMP_DEFAULT as LUMINANCE_RAMP, COLOR_SEPARATOR

try:
    from src.core.auto_segmenter import AutoSegmenter, is_available as auto_seg_available
    AUTO_SEG_AVAILABLE = auto_seg_available()
except ImportError:
    AUTO_SEG_AVAILABLE = False

def generate_ansi_palette():
    palette = {}
    # 0-15: Standard (approximations)
    standard = [
        '#000000', '#800000', '#008000', '#808000', '#000080', '#800080', '#008080', '#c0c0c0',
        '#808080', '#ff0000', '#00ff00', '#ffff00', '#0000ff', '#ff00ff', '#00ffff', '#ffffff'
    ]
    for i, hex_c in enumerate(standard):
        palette[i] = hex_c

    # 16-231: 6x6x6
    steps = [0, 95, 135, 175, 215, 255]
    for i in range(216):
        r = steps[(i // 36) % 6]
        g = steps[(i // 6) % 6]
        b = steps[i % 6]
        palette[16 + i] = f'#{r:02x}{g:02x}{b:02x}'

    # 232-255: Grayscale
    for i in range(24):
        v = 8 + 10 * i
        palette[232 + i] = f'#{v:02x}{v:02x}{v:02x}'

    return palette

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Extase em 4R73 - Player ASCII Colorido</title>
    <style>
        body {
            background-color: #0d1117;
            color: #c9d1d9;
            font-family: 'Courier New', Courier, monospace;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            overflow: hidden;
        }
        #player-container {
            background-color: #000;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 0 20px rgba(0, 255, 0, 0.2);
            text-align: center;
        }
        #ascii-display {
            font-family: 'Courier New', Courier, monospace;
            white-space: pre;
            line-height: 1.0;
            font-size: 10px;
            background-color: #000;
            overflow: hidden;
            letter-spacing: 0;
        }
        #controls {
            margin-top: 15px;
            display: flex;
            gap: 10px;
            justify-content: center;
        }
        button {
            background-color: #238636;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-family: sans-serif;
            font-weight: bold;
        }
        button:hover { background-color: #2ea043; }

        /* Paleta ANSI */
        {CSS_PALETTE}
    </style>
</head>
<body>

    <div id="player-container">
        <div id="ascii-display">Carregando...</div>

        <div id="controls">
            <button id="btn-play">Play</button>
            <button id="btn-pause" style="display:none;">Pause</button>
            <input type="range" id="scrubber" min="0" max="0" value="0" style="width: 300px;">
            <span id="time-display">00:00 / 00:00</span>
            <span id="volume-control" style="display:none; margin-left: 10px;">
                <span style="font-size: 12px;">Vol:</span>
                <input type="range" id="volume-slider" min="0" max="100" value="80" style="width: 80px; vertical-align: middle;">
            </span>
        </div>
    </div>

    <script>
        // Formato: Array de Frames.
        // Cada Frame e um Array de linhas [].
        // Cada Linha e uma String ja com HTML spans otimizados ou dados brutos?
        // Vamos usar dados brutos comprimidos para evitar HTML gigante na string JS.
        // [ [ [char_code, color_code, char_code, color_code...], ...linhas ], ...frames ]

        const rawFrames = {FRAMES_DATA};
        const meta = {METADATA};

        let currentFrame = 0;
        let isPlaying = false;
        let fps = meta.fps;
        let intervalId = null;
        let frameCache = [];

        const display = document.getElementById('ascii-display');
        const btnPlay = document.getElementById('btn-play');
        const btnPause = document.getElementById('btn-pause');
        const scrubber = document.getElementById('scrubber');
        const timeDisplay = document.getElementById('time-display');
        const volumeControl = document.getElementById('volume-control');
        const volumeSlider = document.getElementById('volume-slider');

        let audioEl = null;
        if (meta.hasAudio && meta.audioFile) {
            audioEl = new Audio(meta.audioFile);
            audioEl.volume = 0.8;
            audioEl.preload = 'auto';
            volumeControl.style.display = 'inline';

            volumeSlider.addEventListener('input', (e) => {
                if (audioEl) audioEl.volume = parseInt(e.target.value) / 100;
            });

            audioEl.addEventListener('error', () => {
                volumeControl.style.display = 'none';
                audioEl = null;
            });
        }

        display.style.fontSize = `${meta.fontSize}px`;
        display.style.lineHeight = `${meta.fontSize}px`;

        scrubber.max = rawFrames.length - 1;

        function preRenderFrame(frameIndex) {
            if (frameCache[frameIndex]) return frameCache[frameIndex];

            const frameData = rawFrames[frameIndex];
            if (!frameData) return "";

            let html = "";
            const w = meta.width;
            let col = 0;

            for (let i = 0; i < frameData.length; i += 2) {
                const charCode = frameData[i];
                const colorCode = frameData[i+1];
                const char = String.fromCharCode(charCode);

                if (charCode === 32) {
                    html += " ";
                } else {
                    html += `<span class="c${colorCode}">${char}</span>`;
                }

                col++;
                if (col >= w) {
                    html += "\\n";
                    col = 0;
                }
            }

            frameCache[frameIndex] = html;
            return html;
        }

        function updateDisplay() {
            if (rawFrames[currentFrame]) {
                const html = preRenderFrame(currentFrame);
                display.innerHTML = html;
                scrubber.value = currentFrame;
                updateTime();
            }
        }

        function updateTime() {
            const currentSec = Math.floor(currentFrame / fps);
            const totalSec = Math.floor(rawFrames.length / fps);
            timeDisplay.textContent = `${formatTime(currentSec)} / ${formatTime(totalSec)}`;
        }

        function formatTime(s) {
            const m = Math.floor(s / 60).toString().padStart(2, '0');
            const sec = (s % 60).toString().padStart(2, '0');
            return `${m}:${sec}`;
        }

        function play() {
            isPlaying = true;
            btnPlay.style.display = 'none';
            btnPause.style.display = 'inline-block';

            if (audioEl) {
                audioEl.currentTime = currentFrame / fps;
                audioEl.play().catch(() => {});
            }

            intervalId = setInterval(() => {
                currentFrame++;
                if (currentFrame >= rawFrames.length) {
                    currentFrame = 0;
                    if (audioEl) audioEl.currentTime = 0;
                }
                updateDisplay();
            }, 1000 / fps);
        }

        function pause() {
            isPlaying = false;
            btnPlay.style.display = 'inline-block';
            btnPause.style.display = 'none';
            clearInterval(intervalId);
            if (audioEl) audioEl.pause();
        }

        btnPlay.addEventListener('click', play);
        btnPause.addEventListener('click', pause);

        scrubber.addEventListener('input', (e) => {
            pause();
            currentFrame = parseInt(e.target.value);
            updateDisplay();
            if (audioEl) audioEl.currentTime = currentFrame / fps;
        });

        updateDisplay();
    </script>
</body>
</html>
"""

def converter_video_para_html(video_path: str, output_dir: str, config: configparser.ConfigParser, progress_callback=None, chroma_override=None) -> str:
    try:
        target_width = config.getint('Conversor', 'target_width')
        char_aspect_ratio = config.getfloat('Conversor', 'char_aspect_ratio')
        sobel_threshold = config.getint('Conversor', 'sobel_threshold')
        sharpen_enabled = config.getboolean('Conversor', 'sharpen_enabled', fallback=True)
        sharpen_amount = config.getfloat('Conversor', 'sharpen_amount', fallback=0.5)
        luminance_ramp = config.get('Conversor', 'luminance_ramp', fallback=LUMINANCE_RAMP).rstrip('|')

        edge_boost_enabled = config.getboolean('Conversor', 'edge_boost_enabled', fallback=False)
        edge_boost_amount = config.getint('Conversor', 'edge_boost_amount', fallback=100)
        use_edge_chars = config.getboolean('Conversor', 'use_edge_chars', fallback=True)

        render_mode = config.get('Conversor', 'render_mode', fallback='both').lower()
        if render_mode not in ('user', 'background', 'both'):
            render_mode = 'both'

        auto_seg_enabled = config.getboolean('Conversor', 'auto_seg_enabled', fallback=False)
        auto_segmenter = None
        if auto_seg_enabled and AUTO_SEG_AVAILABLE:
            auto_segmenter = AutoSegmenter()
            print("AutoSeg habilitado para conversao HTML")
    except Exception as e:
        raise ValueError(f"Erro ao ler config.ini: {e}")

    captura = cv2.VideoCapture(video_path)
    if not captura.isOpened():
        raise IOError(f"Erro ao abrir video: {video_path}")

    fps = captura.get(cv2.CAP_PROP_FPS)
    total_frames = int(captura.get(cv2.CAP_PROP_FRAME_COUNT))
    source_width = captura.get(cv2.CAP_PROP_FRAME_WIDTH)
    source_height = captura.get(cv2.CAP_PROP_FRAME_HEIGHT)

    target_fps = min(fps, 12)
    frame_interval = max(1, int(fps / target_fps))

    config_height = config.getint('Conversor', 'target_height', fallback=0)
    if config_height > 0:
        target_height = config_height
    else:
        target_height = int((target_width * source_height * char_aspect_ratio) / source_width)

    target_dimensions = (target_width, target_height)

    # Chroma Key
    if chroma_override:
        lower_green = np.array([
            chroma_override['h_min'], chroma_override['s_min'], chroma_override['v_min']
        ])
        upper_green = np.array([
            chroma_override['h_max'], chroma_override['s_max'], chroma_override['v_max']
        ])
        erode_size = chroma_override.get('erode', 2)
        dilate_size = chroma_override.get('dilate', 2)
    else:
        lower_green = np.array([
            config.getint('ChromaKey', 'h_min'), config.getint('ChromaKey', 's_min'), config.getint('ChromaKey', 'v_min')
        ])
        upper_green = np.array([
            config.getint('ChromaKey', 'h_max'), config.getint('ChromaKey', 's_max'), config.getint('ChromaKey', 'v_max')
        ])
        erode_size = config.getint('ChromaKey', 'erode', fallback=2)
        dilate_size = config.getint('ChromaKey', 'dilate', fallback=2)

    frames_data = []
    processed_count = 0
    read_count = 0

    from src.core.renderer import render_ascii_as_image

    print(f"HTML Export: {target_width}x{target_height} @ {target_fps}fps (Colorido)")

    while True:
        sucesso, frame_colorido = captura.read()
        if not sucesso:
            break

        if read_count % frame_interval != 0:
            read_count += 1
            continue

        read_count += 1
        processed_count += 1

        if auto_segmenter:
            mask_refined = auto_segmenter.process(frame_colorido)
        else:
            hsv = cv2.cvtColor(frame_colorido, cv2.COLOR_BGR2HSV)
            mask_green = cv2.inRange(hsv, lower_green, upper_green)

            if erode_size > 0:
                kernel_erode = np.ones((erode_size, erode_size), np.uint8)
                mask_green = cv2.erode(mask_green, kernel_erode, iterations=1)
            if dilate_size > 0:
                kernel_dilate = np.ones((dilate_size, dilate_size), np.uint8)
                mask_green = cv2.dilate(mask_green, kernel_dilate, iterations=1)

            mask_refined = apply_morphological_refinement(mask_green)
        frame_gray = cv2.cvtColor(frame_colorido, cv2.COLOR_BGR2GRAY)

        if sharpen_enabled:
            frame_gray = sharpen_frame(frame_gray, sharpen_amount)

        resized_gray = cv2.resize(frame_gray, target_dimensions, interpolation=cv2.INTER_AREA)
        resized_color = cv2.resize(frame_colorido, target_dimensions, interpolation=cv2.INTER_AREA)
        resized_mask = cv2.resize(mask_refined, target_dimensions, interpolation=cv2.INTER_NEAREST)

        if render_mode == 'user':
            resized_color[resized_mask > 127] = 0
            mask_for_ascii = resized_mask
        elif render_mode == 'background':
            resized_color[resized_mask < 128] = 0
            mask_for_ascii = 255 - resized_mask
        else:
            mask_for_ascii = np.zeros_like(resized_mask)

        dx = cv2.Sobel(resized_gray, cv2.CV_64F, 1, 0, ksize=3)
        dy = cv2.Sobel(resized_gray, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = np.sqrt(dx**2 + dy**2)
        magnitude_norm = np.clip(magnitude, 0, 255).astype(np.uint8)
        angle = np.arctan2(dy, dx)

        ascii_raw = converter_frame_para_ascii(
            resized_gray, resized_color, mask_for_ascii,
            magnitude_norm, angle,
            sobel_threshold, luminance_ramp,
            output_format="file",
            edge_boost_enabled=edge_boost_enabled,
            edge_boost_amount=edge_boost_amount,
            use_edge_chars=use_edge_chars
        )

        # Parse ASCII RAW "char§code§char§code" into Interleaved Integer Array [char, color, char, color...]
        # Remove newlines first to have a continuous stream matching the JS loop logic
        lines = ascii_raw.split('\n')
        frame_int_stream = []

        for line in lines:
            if not line: continue
            parts = line.split(COLOR_SEPARATOR)
            # parts has extra empty element at end usually
            # Format: c, code, c, code...
            # Valid pairs are at indices i, i+1
            for i in range(0, len(parts)-1, 2):
                char_str = parts[i]
                code_str = parts[i+1]
                if char_str and code_str:
                     # Get ord of first char (ASCII assumes 1 char per block)
                     char_code = ord(char_str[0])
                     try:
                         color_code = int(code_str)
                     except:
                         color_code = 232 # Default black/bg

                     frame_int_stream.append(char_code)
                     frame_int_stream.append(color_code)

        frames_data.append(frame_int_stream)

        if progress_callback:
             if processed_count % 30 == 0:
                 thumb = render_ascii_as_image(ascii_raw, font_scale=0.5)
                 progress_callback(read_count, total_frames, thumb)
             else:
                 progress_callback(read_count, total_frames)

    captura.release()

    # Generate CSS Palette
    palette = generate_ansi_palette()
    css_palette_lines = []
    for code, hex_color in palette.items():
        css_palette_lines.append(f".c{code} {{ color: {hex_color}; }}")
    css_palette_block = "\n        ".join(css_palette_lines)

    nome_base = os.path.splitext(os.path.basename(video_path))[0]
    output_html = os.path.join(output_dir, f"{nome_base}_player.html")

    has_audio = False
    audio_filename = f"{nome_base}_player.mp3"
    audio_output_path = os.path.join(output_dir, audio_filename)

    probe_result = subprocess.run(
        ['ffprobe', '-i', video_path, '-show_streams',
         '-select_streams', 'a', '-loglevel', 'error'],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )

    if probe_result.stdout.strip():
        cmd_audio = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-vn',
            '-c:a', 'libmp3lame',
            '-b:a', '128k',
            audio_output_path
        ]
        result = subprocess.run(
            cmd_audio, capture_output=True, text=True,
            encoding='utf-8', errors='replace'
        )
        if result.returncode == 0 and os.path.exists(audio_output_path) and os.path.getsize(audio_output_path) > 1024:
            has_audio = True
            logger.info("Audio MP3 extraido: %s", audio_output_path)
        else:
            has_audio = False
            logger.warning("Falha ao extrair audio MP3 para HTML")

    js_frames_json = json.dumps(frames_data)

    metadata = {
        "fps": target_fps,
        "width": target_width,
        "height": target_height,
        "fontSize": max(6, int(10 * (100 / target_width))),
        "hasAudio": has_audio,
        "audioFile": audio_filename if has_audio else None
    }

    html_content = HTML_TEMPLATE.replace("{FRAMES_DATA}", js_frames_json)
    html_content = html_content.replace("{METADATA}", json.dumps(metadata))
    html_content = html_content.replace("{CSS_PALETTE}", css_palette_block)

    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"HTML Salvo: {output_html}")
    if has_audio:
        print(f"Audio MP3: {audio_output_path}")
    return output_html

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Converte video para Player HTML ASCII Colorido")
    parser.add_argument("--video", required=True, help="Caminho do video de entrada")
    parser.add_argument("--output", default="data_output", help="Diretorio de saida")
    parser.add_argument("--config", default="config.ini", help="Arquivo de configuracao")
    args = parser.parse_args()

    config = configparser.ConfigParser(interpolation=None)
    config.read(args.config)

    try:
        output_file = converter_video_para_html(args.video, args.output, config)
        print(f"\\nSucesso! HTML salvo em: {output_file}")
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)
