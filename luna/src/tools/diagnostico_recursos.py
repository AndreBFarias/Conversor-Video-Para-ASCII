import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def get_gpu_info():
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(",")
            return {
                "gpu_util": f"{parts[0].strip()}%",
                "mem_util": f"{parts[1].strip()}%",
                "mem_used": f"{parts[2].strip()}MB",
                "mem_total": f"{parts[3].strip()}MB",
                "temp": f"{parts[4].strip()}C",
            }
    except Exception as e:
        print(f"Debug: nvidia-smi falhou: {e}")
    return None


def get_luna_processes():
    processes = []
    for proc in psutil.process_iter(["pid", "name", "cmdline", "memory_info", "cpu_percent", "num_threads"]):
        try:
            cmdline = " ".join(proc.info.get("cmdline", []))
            if "luna" in cmdline.lower() or "main.py" in cmdline.lower():
                if "python" in proc.info.get("name", "").lower():
                    mem = proc.info.get("memory_info")
                    processes.append(
                        {
                            "pid": proc.info["pid"],
                            "name": proc.info["name"],
                            "cmdline": cmdline[:80],
                            "rss_mb": mem.rss / 1024 / 1024 if mem else 0,
                            "cpu": proc.info.get("cpu_percent", 0),
                            "threads": proc.info.get("num_threads", 0),
                        }
                    )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return processes


def get_ollama_processes():
    processes = []
    for proc in psutil.process_iter(["pid", "name", "memory_info", "cpu_percent"]):
        try:
            if "ollama" in proc.info.get("name", "").lower():
                mem = proc.info.get("memory_info")
                processes.append(
                    {
                        "pid": proc.info["pid"],
                        "name": proc.info["name"],
                        "rss_mb": mem.rss / 1024 / 1024 if mem else 0,
                        "cpu": proc.info.get("cpu_percent", 0),
                    }
                )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return processes


def get_system_memory():
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "total_gb": mem.total / 1024 / 1024 / 1024,
        "used_gb": mem.used / 1024 / 1024 / 1024,
        "available_gb": mem.available / 1024 / 1024 / 1024,
        "percent": mem.percent,
        "swap_used_gb": swap.used / 1024 / 1024 / 1024,
        "swap_percent": swap.percent,
    }


def check_audio_devices():
    try:
        import pyaudio

        p = pyaudio.PyAudio()
        devices = []
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info.get("maxInputChannels", 0) > 0:
                devices.append(
                    {
                        "index": i,
                        "name": info["name"],
                        "rate": int(info["defaultSampleRate"]),
                        "channels": info["maxInputChannels"],
                    }
                )
        p.terminate()
        return devices
    except Exception as e:
        return [{"error": str(e)}]


def check_whisper_model():
    try:
        import config

        model_path = config.WHISPER_MODELS_DIR
        model_size = config.WHISPER_CONFIG["MODEL_SIZE"]
        model_files = list(model_path.glob(f"*{model_size}*"))
        return {
            "path": str(model_path),
            "model_size": model_size,
            "files_found": len(model_files),
            "compute_type": config.WHISPER_CONFIG["COMPUTE_TYPE"],
            "use_gpu": config.WHISPER_CONFIG["USE_GPU"],
        }
    except Exception as e:
        return {"error": str(e)}


def check_thread_status():
    import threading

    threads = []
    for t in threading.enumerate():
        threads.append({"name": t.name, "alive": t.is_alive(), "daemon": t.daemon})
    return threads


def print_separator(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print("=" * 60)


def run_diagnostics():
    print(f"\n{'#'*60}")
    print(f" DIAGNOSTICO LUNA - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("#" * 60)

    print_separator("GPU (NVIDIA)")
    gpu = get_gpu_info()
    if gpu:
        print(f"  Utilizacao GPU: {gpu['gpu_util']}")
        print(f"  Utilizacao VRAM: {gpu['mem_util']}")
        print(f"  VRAM Usada: {gpu['mem_used']} / {gpu['mem_total']}")
        print(f"  Temperatura: {gpu['temp']}")
    else:
        print("  GPU nao disponivel ou nvidia-smi nao encontrado")

    print_separator("MEMORIA DO SISTEMA")
    mem = get_system_memory()
    print(f"  RAM Total: {mem['total_gb']:.1f} GB")
    print(f"  RAM Usada: {mem['used_gb']:.1f} GB ({mem['percent']:.1f}%)")
    print(f"  RAM Disponivel: {mem['available_gb']:.1f} GB")
    print(f"  Swap Usado: {mem['swap_used_gb']:.1f} GB ({mem['swap_percent']:.1f}%)")

    print_separator("PROCESSOS LUNA")
    luna_procs = get_luna_processes()
    if luna_procs:
        for p in luna_procs:
            print(f"  PID {p['pid']}: {p['rss_mb']:.0f}MB RAM, {p['cpu']:.1f}% CPU, {p['threads']} threads")
            print(f"    {p['cmdline']}")
    else:
        print("  Nenhum processo Luna encontrado")

    print_separator("PROCESSOS OLLAMA")
    ollama_procs = get_ollama_processes()
    if ollama_procs:
        for p in ollama_procs:
            print(f"  PID {p['pid']}: {p['rss_mb']:.0f}MB RAM, {p['cpu']:.1f}% CPU")
    else:
        print("  Ollama nao esta rodando")

    print_separator("DISPOSITIVOS DE AUDIO")
    devices = check_audio_devices()
    for d in devices:
        if "error" in d:
            print(f"  Erro: {d['error']}")
        else:
            print(f"  [{d['index']}] {d['name']}")
            print(f"      Rate: {d['rate']}Hz, Channels: {d['channels']}")

    print_separator("MODELO WHISPER (STT)")
    whisper = check_whisper_model()
    if "error" in whisper:
        print(f"  Erro: {whisper['error']}")
    else:
        print(f"  Path: {whisper['path']}")
        print(f"  Modelo: {whisper['model_size']}")
        print(f"  Compute Type: {whisper['compute_type']}")
        print(f"  Use GPU: {whisper['use_gpu']}")
        print(f"  Arquivos: {whisper['files_found']}")

    print_separator("CONFIGURACOES CRITICAS")
    try:
        import config

        print(f"  VAD Energy Threshold: {config.VAD_CONFIG['ENERGY_THRESHOLD']}")
        print(f"  VAD Mode: {config.VAD_CONFIG['MODE']}")
        print(f"  VAD Silence Frame Limit: {config.VAD_CONFIG['SILENCE_FRAME_LIMIT']}")
        print(f"  VAD Min Speech Chunks: {config.VAD_CONFIG['MIN_SPEECH_CHUNKS']}")
        print(f"  Wake Word Enabled: {config.WAKE_WORD_ENABLED}")
        print(f"  Wake Word Cooldown: {config.WAKE_WORD_COOLDOWN}s")
        print(f"  Audio Sample Rate: {config.AUDIO_CONFIG['SAMPLE_RATE']}Hz")
        print(f"  Audio Chunk Size: {config.AUDIO_CONFIG['CHUNK_SIZE']}")
    except Exception as e:
        print(f"  Erro ao ler config: {e}")

    print("\n" + "=" * 60)
    print(" FIM DO DIAGNOSTICO")
    print("=" * 60 + "\n")


def monitor_realtime(interval=2, duration=30):
    print(f"\n{'#'*60}")
    print(f" MONITORAMENTO EM TEMPO REAL ({duration}s)")
    print("#" * 60)

    start = time.time()
    while time.time() - start < duration:
        os.system("clear" if os.name == "posix" else "cls")

        print(f"=== MONITOR LUNA === {datetime.now().strftime('%H:%M:%S')} ===\n")

        gpu = get_gpu_info()
        if gpu:
            print(f"GPU: {gpu['gpu_util']} | VRAM: {gpu['mem_used']}/{gpu['mem_total']} | Temp: {gpu['temp']}")

        mem = get_system_memory()
        print(
            f"RAM: {mem['used_gb']:.1f}/{mem['total_gb']:.1f}GB ({mem['percent']:.0f}%) | Swap: {mem['swap_used_gb']:.1f}GB"
        )

        print("\nProcessos Luna:")
        for p in get_luna_processes():
            print(f"  PID {p['pid']}: {p['rss_mb']:.0f}MB, {p['cpu']:.1f}% CPU, {p['threads']} threads")

        print(f"\n[Ctrl+C para sair | {int(duration - (time.time() - start))}s restantes]")

        time.sleep(interval)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--monitor":
        duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        try:
            monitor_realtime(interval=2, duration=duration)
        except KeyboardInterrupt:
            print("\nMonitoramento encerrado")
    else:
        run_diagnostics()
