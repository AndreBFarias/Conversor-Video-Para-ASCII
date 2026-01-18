# -*- coding: utf-8 -*-
"""
GPU Memory Manager - Sistema centralizado de gerenciamento de memória GPU.

Este módulo fornece:
- Monitoramento de VRAM em tempo real
- Sistema de prioridades para alocação
- Fallback automático para CPU quando memória baixa
- Watchdog para proteção do sistema
- Decoradores para operações GPU seguras
- Suporte a multithreading com ThreadPoolExecutor

Autor: Extase em 4R73
"""

import gc
import time
import threading
import functools
import numpy as np
from typing import Optional, Callable, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from enum import Enum
import warnings

# Tentativa de importar CuPy
try:
    import cupy as cp
    CUPY_AVAILABLE = True
except ImportError:
    CUPY_AVAILABLE = False
    cp = None

# Tentativa de verificar CUDA
try:
    if CUPY_AVAILABLE:
        cp.cuda.Device(0).compute_capability
        CUDA_AVAILABLE = True
    else:
        CUDA_AVAILABLE = False
except Exception:
    CUDA_AVAILABLE = False


class GPUPriority(Enum):
    """Prioridades para alocação de memória GPU."""
    CRITICAL = 1      # Renderização principal
    HIGH = 2          # Efeitos visuais essenciais
    MEDIUM = 3        # Efeitos opcionais
    LOW = 4           # Background tasks
    BACKGROUND = 5    # Pode ser adiado


@dataclass
class MemoryConsumer:
    """Representa um consumidor de memória GPU."""
    name: str
    priority: GPUPriority
    estimated_usage_bytes: int = 0
    last_active: float = field(default_factory=time.time)
    is_active: bool = False


@dataclass 
class GPUStats:
    """Estatísticas de memória GPU."""
    total_memory: int  # bytes
    used_memory: int   # bytes
    free_memory: int   # bytes
    usage_percent: float
    is_gpu_available: bool
    device_name: str
    compute_mode: str = "GPU"


class GPUMemoryManager:
    """
    Gerenciador centralizado de memória GPU.
    
    Responsável por:
    - Monitorar uso de VRAM em tempo real
    - Gerenciar alocações com sistema de prioridades
    - Fornecer fallback automático para CPU
    - Proteção contra OOM (Out of Memory)
    - Watchdog para detectar deadlocks
    """
    
    _instance: Optional['GPUMemoryManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern para gerenciador global."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(
        self,
        vram_limit_mb: Optional[int] = None,
        threshold_percent: float = 0.80,
        emergency_threshold: float = 0.95,
        enable_watchdog: bool = True,
        watchdog_timeout_seconds: float = 10.0,
        max_workers: int = 4
    ):
        """
        Inicializa o gerenciador de memória GPU.
        
        Args:
            vram_limit_mb: Limite máximo de VRAM em MB (None = auto-detect 80% do total)
            threshold_percent: Threshold para começar a liberar memória (0-1)
            emergency_threshold: Threshold para limpeza de emergência (0-1)
            enable_watchdog: Habilitar watchdog para detectar deadlocks
            watchdog_timeout_seconds: Timeout do watchdog
            max_workers: Número máximo de workers para ThreadPoolExecutor
        """
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._initialized = True
        self._lock = threading.RLock()
        
        # Configurações
        self._threshold_percent = threshold_percent
        self._emergency_threshold = emergency_threshold
        self._watchdog_timeout = watchdog_timeout_seconds
        self._enable_watchdog = enable_watchdog
        
        # Estado
        self._consumers: Dict[str, MemoryConsumer] = {}
        self._gpu_available = CUDA_AVAILABLE
        self._fallback_mode = not self._gpu_available
        self._last_gc_time = 0.0
        self._gc_cooldown = 2.0  # segundos entre GCs
        self._consecutive_oom_count = 0
        self._max_consecutive_oom = 3
        
        # Thread pool para operações assíncronas
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="gpu_worker")
        self._pending_futures: Dict[str, Future] = {}
        
        # Cache de stats para evitar bloqueio
        self._stats_cache: Optional[GPUStats] = None
        self._stats_cache_time = 0.0
        self._stats_cache_ttl = 1.0  # TTL em segundos
        
        # Watchdog
        self._watchdog_thread: Optional[threading.Thread] = None
        self._watchdog_stop = threading.Event()
        self._last_activity = time.time()
        
        # Detectar memória total e definir limites
        self._total_memory = 0
        self._vram_limit = 0
        
        if self._gpu_available:
            try:
                stats = self._get_gpu_stats_internal()
                self._total_memory = stats.total_memory
                
                if vram_limit_mb is not None:
                    self._vram_limit = vram_limit_mb * 1024 * 1024
                else:
                    # Auto-detect: usar 80% da memória total
                    self._vram_limit = int(self._total_memory * 0.80)
                    
                print(f"[GPUManager] Inicializado: {stats.device_name}")
                print(f"[GPUManager] VRAM Total: {self._total_memory // (1024*1024)}MB, "
                      f"Limite: {self._vram_limit // (1024*1024)}MB")
            except Exception as e:
                print(f"[GPUManager] Erro ao detectar GPU: {e}")
                self._gpu_available = False
                self._fallback_mode = True
        else:
            print("[GPUManager] GPU não disponível, usando modo CPU")
        
        # Iniciar watchdog se habilitado
        if self._enable_watchdog and self._gpu_available:
            self._start_watchdog()
    
    def _get_gpu_stats_internal(self) -> GPUStats:
        """Obtém estatísticas internas da GPU."""
        if not self._gpu_available:
            return GPUStats(
                total_memory=0,
                used_memory=0,
                free_memory=0,
                usage_percent=0.0,
                is_gpu_available=False,
                device_name="N/A",
                compute_mode="CPU"
            )
        
        try:
            mempool = cp.get_default_memory_pool()
            used_bytes = mempool.used_bytes()
            total_bytes = mempool.total_bytes()
            
            # Obter memória física do device
            device = cp.cuda.Device(0)
            free_mem, total_mem = device.mem_info
            
            device_props = cp.cuda.runtime.getDeviceProperties(0)
            device_name = device_props['name'].decode('utf-8') if isinstance(device_props['name'], bytes) else device_props['name']
            
            usage_percent = (total_mem - free_mem) / total_mem if total_mem > 0 else 0.0
            
            return GPUStats(
                total_memory=total_mem,
                used_memory=total_mem - free_mem,
                free_memory=free_mem,
                usage_percent=usage_percent,
                is_gpu_available=True,
                device_name=device_name,
                compute_mode="GPU"
            )
        except Exception as e:
            warnings.warn(f"Erro ao obter stats GPU: {e}")
            return GPUStats(
                total_memory=0,
                used_memory=0,
                free_memory=0,
                usage_percent=0.0,
                is_gpu_available=False,
                device_name="Error",
                compute_mode="CPU"
            )
    
    def get_stats(self) -> GPUStats:
        """Retorna estatísticas atuais de memória GPU (com cache)."""
        now = time.time()
        
        # Retornar cache se ainda válido
        if self._stats_cache is not None and (now - self._stats_cache_time) < self._stats_cache_ttl:
            return self._stats_cache
        
        # Atualizar cache
        with self._lock:
            self._stats_cache = self._get_gpu_stats_internal()
            self._stats_cache_time = now
            return self._stats_cache
    
    def get_stats_fast(self) -> GPUStats:
        """Retorna stats do cache sem atualizar (não bloqueia)."""
        if self._stats_cache is not None:
            return self._stats_cache
        # Se não há cache, retorna valor padrão
        return GPUStats(
            total_memory=self._total_memory,
            used_memory=0,
            free_memory=self._total_memory,
            usage_percent=0.0,
            is_gpu_available=self._gpu_available,
            device_name="cached",
            compute_mode="GPU" if not self._fallback_mode else "CPU"
        )
    
    def get_free_memory(self) -> int:
        """Retorna memória GPU livre em bytes."""
        stats = self.get_stats()
        return stats.free_memory
    
    def get_used_memory(self) -> int:
        """Retorna memória GPU usada em bytes."""
        stats = self.get_stats()
        return stats.used_memory
    
    def get_total_memory(self) -> int:
        """Retorna memória GPU total em bytes."""
        return self._total_memory
    
    def is_gpu_available(self) -> bool:
        """Verifica se GPU está disponível."""
        return self._gpu_available and not self._fallback_mode
    
    def is_safe_to_use_gpu(self, use_cache: bool = True) -> bool:
        """
        Verifica se é seguro usar GPU considerando memória disponível.
        
        Args:
            use_cache: Se True, usa cache de stats (não bloqueia)
        
        Returns:
            True se GPU pode ser usada, False se deve usar CPU
        """
        if not self._gpu_available or self._fallback_mode:
            return False
        
        # Se tivemos muitos OOMs consecutivos, desabilitar temporariamente
        if self._consecutive_oom_count >= self._max_consecutive_oom:
            return False
        
        # Usar cache para não bloquear thread principal
        if use_cache:
            stats = self.get_stats_fast()
        else:
            stats = self.get_stats()
        
        # Se usar mais que threshold, não é seguro
        if stats.usage_percent > self._threshold_percent:
            return False
        
        return True
    
    def check_available(self, required_bytes: int) -> bool:
        """
        Verifica se há memória suficiente para alocação.
        
        Args:
            required_bytes: Bytes necessários para alocação
            
        Returns:
            True se há memória suficiente
        """
        if not self._gpu_available:
            return False
        
        free = self.get_free_memory()
        # Manter 20% de margem de segurança
        available = int(free * 0.8)
        
        return available >= required_bytes
    
    def get_safe_allocation_size(self) -> int:
        """
        Retorna o tamanho máximo seguro para alocação.
        
        Returns:
            Bytes disponíveis para alocação segura
        """
        if not self._gpu_available:
            return 0
        
        free = self.get_free_memory()
        # Retornar 60% da memória livre como seguro
        return int(free * 0.6)
    
    def register_consumer(self, name: str, priority: GPUPriority = GPUPriority.MEDIUM) -> None:
        """
        Registra um consumidor de memória GPU.
        
        Args:
            name: Nome identificador do consumidor
            priority: Prioridade do consumidor
        """
        with self._lock:
            self._consumers[name] = MemoryConsumer(
                name=name,
                priority=priority,
                last_active=time.time(),
                is_active=True
            )
    
    def unregister_consumer(self, name: str) -> None:
        """Remove registro de um consumidor."""
        with self._lock:
            if name in self._consumers:
                del self._consumers[name]
    
    def update_consumer_usage(self, name: str, bytes_used: int) -> None:
        """Atualiza uso de memória de um consumidor."""
        with self._lock:
            if name in self._consumers:
                self._consumers[name].estimated_usage_bytes = bytes_used
                self._consumers[name].last_active = time.time()
    
    def force_gc(self) -> int:
        """
        Força garbage collection de memória GPU.
        
        Returns:
            Bytes liberados (estimativa)
        """
        if not self._gpu_available:
            gc.collect()
            return 0
        
        # Evitar GC muito frequente
        now = time.time()
        if now - self._last_gc_time < self._gc_cooldown:
            return 0
        
        self._last_gc_time = now
        
        try:
            with self._lock:
                before = self.get_used_memory()
                
                # Sincronizar streams CUDA
                cp.cuda.Stream.null.synchronize()
                
                # Liberar blocos não utilizados do memory pool
                mempool = cp.get_default_memory_pool()
                mempool.free_all_blocks()
                
                # Limpar pinned memory pool também
                pinned_mempool = cp.get_default_pinned_memory_pool()
                pinned_mempool.free_all_blocks()
                
                # Python GC
                gc.collect()
                
                after = self.get_used_memory()
                freed = max(0, before - after)
                
                if freed > 0:
                    print(f"[GPUManager] GC liberou {freed // (1024*1024)}MB")
                
                return freed
        except Exception as e:
            print(f"[GPUManager] Erro no GC: {e}")
            return 0
    
    def emergency_cleanup(self) -> None:
        """
        Limpeza de emergência - libera toda a memória possível.
        Chamado quando sistema está próximo de OOM.
        """
        print("[GPUManager] ⚠️ LIMPEZA DE EMERGÊNCIA ⚠️")
        
        with self._lock:
            # Marcar todos consumidores de baixa prioridade como inativos
            for consumer in self._consumers.values():
                if consumer.priority.value >= GPUPriority.LOW.value:
                    consumer.is_active = False
            
            # Forçar GC múltiplas vezes
            for _ in range(3):
                self.force_gc()
                time.sleep(0.1)
            
            # Reset contador de OOM
            self._consecutive_oom_count = 0
    
    def notify_oom(self) -> None:
        """Notifica que ocorreu um OOM error."""
        with self._lock:
            self._consecutive_oom_count += 1
            
            if self._consecutive_oom_count >= self._max_consecutive_oom:
                print(f"[GPUManager] {self._consecutive_oom_count} OOMs consecutivos, "
                      "habilitando fallback CPU")
                self._fallback_mode = True
    
    def reset_oom_counter(self) -> None:
        """Reseta contador de OOM (chamar após operação bem sucedida)."""
        with self._lock:
            if self._consecutive_oom_count > 0:
                self._consecutive_oom_count = max(0, self._consecutive_oom_count - 1)
    
    def enable_gpu(self) -> bool:
        """
        Tenta reabilitar GPU após fallback.
        
        Returns:
            True se GPU foi reabilitada
        """
        if not CUDA_AVAILABLE:
            return False
        
        with self._lock:
            # Tentar limpar e reabilitar
            self.force_gc()
            stats = self.get_stats()
            
            if stats.free_memory > self._vram_limit * 0.5:
                self._fallback_mode = False
                self._consecutive_oom_count = 0
                print("[GPUManager] GPU reabilitada")
                return True
            
            return False
    
    # =========================================================================
    # Multithreading Support
    # =========================================================================
    
    def submit_gpu_task(
        self,
        func: Callable,
        *args,
        task_name: str = "unnamed",
        priority: GPUPriority = GPUPriority.MEDIUM,
        **kwargs
    ) -> Future:
        """
        Submete uma tarefa GPU para execução assíncrona.
        
        Args:
            func: Função a executar
            *args: Argumentos posicionais
            task_name: Nome da tarefa para tracking
            priority: Prioridade da tarefa
            **kwargs: Argumentos nomeados
            
        Returns:
            Future representando a tarefa
        """
        self.register_consumer(task_name, priority)
        
        def wrapper():
            try:
                self._last_activity = time.time()
                result = func(*args, **kwargs)
                self.reset_oom_counter()
                return result
            except cp.cuda.memory.OutOfMemoryError:
                self.notify_oom()
                raise
            finally:
                self.unregister_consumer(task_name)
        
        future = self._executor.submit(wrapper)
        self._pending_futures[task_name] = future
        
        return future
    
    def wait_all_tasks(self, timeout: Optional[float] = None) -> bool:
        """
        Aguarda todas as tarefas pendentes completarem.
        
        Args:
            timeout: Timeout em segundos (None = sem timeout)
            
        Returns:
            True se todas completaram, False se timeout
        """
        from concurrent.futures import wait, ALL_COMPLETED
        
        futures = list(self._pending_futures.values())
        if not futures:
            return True
        
        done, not_done = wait(futures, timeout=timeout, return_when=ALL_COMPLETED)
        
        # Limpar futures completados
        completed = [name for name, f in self._pending_futures.items() if f.done()]
        for name in completed:
            del self._pending_futures[name]
        
        return len(not_done) == 0
    
    def cancel_low_priority_tasks(self) -> int:
        """
        Cancela tarefas de baixa prioridade.
        
        Returns:
            Número de tarefas canceladas
        """
        cancelled = 0
        
        for name, consumer in list(self._consumers.items()):
            if consumer.priority.value >= GPUPriority.LOW.value:
                if name in self._pending_futures:
                    future = self._pending_futures[name]
                    if future.cancel():
                        cancelled += 1
                        del self._pending_futures[name]
        
        return cancelled
    
    # =========================================================================
    # Watchdog
    # =========================================================================
    
    def _start_watchdog(self) -> None:
        """Inicia thread do watchdog."""
        if self._watchdog_thread is not None and self._watchdog_thread.is_alive():
            return
        
        self._watchdog_stop.clear()
        self._watchdog_thread = threading.Thread(
            target=self._watchdog_loop,
            name="gpu_watchdog",
            daemon=True
        )
        self._watchdog_thread.start()
    
    def _watchdog_loop(self) -> None:
        """Loop principal do watchdog."""
        while not self._watchdog_stop.is_set():
            time.sleep(1.0)
            
            # Verificar timeout de inatividade durante operação
            with self._lock:
                if len(self._pending_futures) > 0:
                    elapsed = time.time() - self._last_activity
                    if elapsed > self._watchdog_timeout:
                        print(f"[GPUManager] ⚠️ Watchdog: {elapsed:.1f}s sem atividade")
                        self.emergency_cleanup()
                        self._last_activity = time.time()
                
                # Verificar memória periodicamente
                stats = self._get_gpu_stats_internal()
                if stats.usage_percent > self._emergency_threshold:
                    print(f"[GPUManager] ⚠️ Uso crítico de memória: {stats.usage_percent:.1%}")
                    self.emergency_cleanup()
    
    def stop_watchdog(self) -> None:
        """Para o watchdog."""
        self._watchdog_stop.set()
        if self._watchdog_thread:
            self._watchdog_thread.join(timeout=2.0)
    
    # =========================================================================
    # Context Manager
    # =========================================================================
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            if CUPY_AVAILABLE and isinstance(exc_val, cp.cuda.memory.OutOfMemoryError):
                self.notify_oom()
                self.emergency_cleanup()
        return False
    
    # =========================================================================
    # Cleanup
    # =========================================================================
    
    def shutdown(self) -> None:
        """Desliga o gerenciador e libera recursos."""
        self.stop_watchdog()
        self._executor.shutdown(wait=False)
        self.force_gc()


# ============================================================================
# Instância global singleton
# ============================================================================

gpu_manager = GPUMemoryManager()


# ============================================================================
# Decoradores
# ============================================================================

def gpu_safe_operation(
    fallback_cpu: bool = True,
    max_retries: int = 2,
    cleanup_on_fail: bool = True,
    priority: GPUPriority = GPUPriority.MEDIUM
) -> Callable:
    """
    Decorador para tornar operações GPU seguras.
    
    Automaticamente:
    - Verifica se GPU está disponível
    - Captura OOM errors e tenta fallback para CPU
    - Limpa memória em caso de falha
    - Retenta operação após cleanup
    
    Args:
        fallback_cpu: Se True, tenta executar em CPU em caso de falha GPU
        max_retries: Número máximo de tentativas
        cleanup_on_fail: Se True, força GC após falha
        priority: Prioridade da operação
    
    Example:
        @gpu_safe_operation(fallback_cpu=True)
        def process_frame(frame):
            # Operação GPU
            return cp.array(frame)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Verificar se GPU está segura
            if not gpu_manager.is_safe_to_use_gpu():
                if fallback_cpu:
                    # Forçar modo CPU nos kwargs se a função suportar
                    kwargs['_force_cpu'] = True
                    return func(*args, **kwargs)
                else:
                    raise RuntimeError("GPU indisponível e fallback CPU desabilitado")
            
            # Tentar executar com retry
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    gpu_manager.reset_oom_counter()
                    return result
                    
                except Exception as e:
                    last_exception = e
                    is_oom = CUPY_AVAILABLE and isinstance(e, cp.cuda.memory.OutOfMemoryError)
                    
                    if is_oom:
                        gpu_manager.notify_oom()
                        
                        if cleanup_on_fail:
                            gpu_manager.force_gc()
                        
                        if attempt < max_retries:
                            print(f"[GPUManager] Retry {attempt + 1}/{max_retries} após OOM")
                            time.sleep(0.5)
                            continue
                        
                        # Última tentativa: fallback CPU
                        if fallback_cpu:
                            print(f"[GPUManager] Fallback para CPU após {max_retries} tentativas")
                            kwargs['_force_cpu'] = True
                            return func(*args, **kwargs)
                    
                    # Não é OOM, propagar exceção
                    raise
            
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def is_gpu_safe() -> bool:
    """
    Função utilitária para verificar se GPU está segura para uso.
    
    Returns:
        True se GPU pode ser usada
    """
    return gpu_manager.is_safe_to_use_gpu()


def get_compute_mode() -> str:
    """
    Retorna o modo de computação atual.
    
    Returns:
        "GPU" ou "CPU"
    """
    if gpu_manager.is_gpu_available():
        return "GPU"
    return "CPU"


def format_memory_size(bytes_size: int) -> str:
    """Formata tamanho de memória para exibição."""
    if bytes_size < 1024:
        return f"{bytes_size}B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f}KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.1f}MB"
    else:
        return f"{bytes_size / (1024 * 1024 * 1024):.2f}GB"


def get_memory_info() -> Dict[str, Any]:
    """
    Retorna informações de memória formatadas.
    
    Returns:
        Dict com informações de memória
    """
    stats = gpu_manager.get_stats()
    return {
        'device': stats.device_name,
        'mode': stats.compute_mode,
        'total': format_memory_size(stats.total_memory),
        'used': format_memory_size(stats.used_memory),
        'free': format_memory_size(stats.free_memory),
        'usage_percent': f"{stats.usage_percent:.1%}",
        'is_safe': gpu_manager.is_safe_to_use_gpu()
    }


# ============================================================================
# Benchmark para comparação GPU vs CPU
# ============================================================================

def benchmark_gpu_vs_cpu(array_size: int = 1000000, iterations: int = 10) -> Dict[str, float]:
    """
    Benchmark comparando performance GPU vs CPU.
    
    Args:
        array_size: Tamanho do array para teste
        iterations: Número de iterações
        
    Returns:
        Dict com tempos de execução
    """
    import time
    
    results = {
        'cpu_time': 0.0,
        'gpu_time': 0.0,
        'speedup': 0.0,
        'gpu_available': gpu_manager.is_gpu_available()
    }
    
    # Teste CPU
    arr_cpu = np.random.rand(array_size).astype(np.float32)
    start = time.perf_counter()
    for _ in range(iterations):
        _ = np.fft.fft(arr_cpu)
        _ = np.sort(arr_cpu)
    results['cpu_time'] = (time.perf_counter() - start) / iterations
    
    # Teste GPU
    if gpu_manager.is_gpu_available():
        try:
            arr_gpu = cp.array(arr_cpu)
            # Warmup
            _ = cp.fft.fft(arr_gpu)
            cp.cuda.Stream.null.synchronize()
            
            start = time.perf_counter()
            for _ in range(iterations):
                _ = cp.fft.fft(arr_gpu)
                _ = cp.sort(arr_gpu)
                cp.cuda.Stream.null.synchronize()
            results['gpu_time'] = (time.perf_counter() - start) / iterations
            
            if results['gpu_time'] > 0:
                results['speedup'] = results['cpu_time'] / results['gpu_time']
            
            # Cleanup
            del arr_gpu
            gpu_manager.force_gc()
            
        except Exception as e:
            print(f"[Benchmark] Erro GPU: {e}")
            results['gpu_time'] = float('inf')
    
    return results


# "A memória é o diário que todos carregamos conosco." - Oscar Wilde
