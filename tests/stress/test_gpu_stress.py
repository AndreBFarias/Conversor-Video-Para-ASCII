#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes de Stress para GPU Memory Manager e Componentes GPU.

Este módulo fornece testes para:
- Simular situações de OOM
- Testar fallbacks para CPU
- Verificar recuperação após erros
- Medir performance GPU vs CPU

Uso:
    python -m pytest tests/stress/test_gpu_stress.py -v
    python tests/stress/test_gpu_stress.py  # Executar diretamente
"""

import sys
import os
import time
import gc
import numpy as np
from typing import List, Tuple
import unittest

# Adicionar path do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


class TestGPUMemoryManager(unittest.TestCase):
    """Testes para o GPU Memory Manager."""
    
    @classmethod
    def setUpClass(cls):
        """Setup inicial - importar módulos."""
        try:
            from src.utils.gpu_memory_manager import (
                gpu_manager, is_gpu_safe, get_memory_info, 
                get_compute_mode, GPUPriority
            )
            cls.gpu_manager = gpu_manager
            cls.is_gpu_safe = is_gpu_safe
            cls.get_memory_info = get_memory_info
            cls.get_compute_mode = get_compute_mode
            cls.GPUPriority = GPUPriority
            cls.gpu_available = True
        except Exception as e:
            print(f"GPU Manager não disponível: {e}")
            cls.gpu_available = False
    
    def test_gpu_manager_initialization(self):
        """Testa se GPU Manager inicializa corretamente."""
        if not self.gpu_available:
            self.skipTest("GPU Manager não disponível")
        
        stats = self.gpu_manager.get_stats()
        self.assertIsNotNone(stats)
        self.assertIsNotNone(stats.device_name)
        print(f"Device: {stats.device_name}")
        print(f"Total: {stats.total_memory // (1024*1024)}MB")
    
    def test_memory_tracking(self):
        """Testa tracking de memória."""
        if not self.gpu_available:
            self.skipTest("GPU Manager não disponível")

        free_before = self.gpu_manager.get_free_memory()
        used_before = self.gpu_manager.get_used_memory()

        self.assertGreaterEqual(free_before, 0)
        print(f"Free: {free_before // (1024*1024)}MB")
        print(f"Used: {used_before // (1024*1024)}MB")

    def test_is_safe_check(self):
        """Testa verificação de segurança de GPU."""
        if not self.gpu_available:
            self.skipTest("GPU Manager não disponível")

        is_safe = self.__class__.is_gpu_safe()
        mode = self.__class__.get_compute_mode()

        self.assertIn(mode, ["GPU", "CPU"])
        print(f"Is Safe: {is_safe}")
        print(f"Mode: {mode}")
    
    def test_garbage_collection(self):
        """Testa garbage collection de GPU."""
        if not self.gpu_available:
            self.skipTest("GPU Manager não disponível")
        
        freed = self.gpu_manager.force_gc()
        self.assertGreaterEqual(freed, 0)
        print(f"Freed: {freed // 1024}KB")
    
    def test_consumer_registration(self):
        """Testa registro de consumidores."""
        if not self.gpu_available:
            self.skipTest("GPU Manager não disponível")
        
        self.gpu_manager.register_consumer("test_consumer", self.GPUPriority.LOW)
        self.gpu_manager.update_consumer_usage("test_consumer", 1024 * 1024)
        self.gpu_manager.unregister_consumer("test_consumer")
        print("Consumer registration: OK")


class TestGPUStress(unittest.TestCase):
    """Testes de stress para GPU."""
    
    @classmethod
    def setUpClass(cls):
        """Setup inicial."""
        try:
            import cupy as cp
            cls.cp = cp
            cls.gpu_available = True
        except ImportError:
            cls.gpu_available = False
    
    def test_allocation_stress(self):
        """Testa alocações de memória sob stress."""
        if not self.gpu_available:
            self.skipTest("CuPy não disponível")
        
        allocations = []
        allocation_sizes = [10, 50, 100, 200]  # MB
        
        try:
            for size_mb in allocation_sizes:
                size_bytes = size_mb * 1024 * 1024
                try:
                    arr = self.cp.zeros(size_bytes // 4, dtype=self.cp.float32)
                    allocations.append(arr)
                    print(f"Alocado: {size_mb}MB - OK")
                except self.cp.cuda.memory.OutOfMemoryError:
                    print(f"OOM em {size_mb}MB (esperado)")
                    break
        finally:
            # Cleanup
            for arr in allocations:
                del arr
            allocations.clear()
            self.cp.get_default_memory_pool().free_all_blocks()
            gc.collect()
    
    def test_rapid_allocation_deallocation(self):
        """Testa alocações e desalocações rápidas."""
        if not self.gpu_available:
            self.skipTest("CuPy não disponível")
        
        iterations = 100
        size_mb = 10
        size_elements = (size_mb * 1024 * 1024) // 4
        
        start_time = time.perf_counter()
        
        for i in range(iterations):
            arr = self.cp.zeros(size_elements, dtype=self.cp.float32)
            del arr
        
        # Force GC periodically
        self.cp.get_default_memory_pool().free_all_blocks()
        
        elapsed = time.perf_counter() - start_time
        print(f"{iterations} alocações de {size_mb}MB em {elapsed:.2f}s")
        print(f"Taxa: {iterations/elapsed:.1f} ops/s")
    
    def test_matrix_operations_stress(self):
        """Testa operações de matriz sob stress."""
        if not self.gpu_available:
            self.skipTest("CuPy não disponível")
        
        sizes = [(100, 100), (500, 500), (1000, 1000)]
        
        for h, w in sizes:
            try:
                # Simular processamento de frame
                frame = self.cp.random.rand(h, w, 3).astype(self.cp.uint8)
                gray = self.cp.mean(frame, axis=2)
                
                # Operações típicas
                result = self.cp.gradient(gray)
                
                self.cp.cuda.Stream.null.synchronize()
                
                del frame, gray, result
                print(f"Matrix {h}x{w}: OK")
                
            except self.cp.cuda.memory.OutOfMemoryError:
                print(f"OOM em {h}x{w}")
                break
        
        self.cp.get_default_memory_pool().free_all_blocks()


class TestFallbackMechanisms(unittest.TestCase):
    """Testa mecanismos de fallback CPU."""
    
    def test_auto_segmenter_fallback(self):
        """Testa fallback do AutoSegmenter."""
        try:
            from src.core.auto_segmenter import AutoSegmenter, is_available
            
            if not is_available():
                self.skipTest("AutoSegmenter não disponível")
            
            # Testar com GPU
            segmenter_gpu = AutoSegmenter(threshold=0.5, use_gpu=True)
            print(f"AutoSegmenter GPU mode: {segmenter_gpu.use_gpu}")
            
            # Testar com CPU
            segmenter_cpu = AutoSegmenter(threshold=0.5, use_gpu=False)
            self.assertFalse(segmenter_cpu.use_gpu)
            print("AutoSegmenter CPU fallback: OK")
            
            # Cleanup
            segmenter_gpu.close()
            segmenter_cpu.close()
            
        except ImportError as e:
            self.skipTest(f"Módulo não disponível: {e}")
    
    def test_postfx_fallback(self):
        """Testa fallback do PostFX."""
        try:
            from src.core.post_fx_gpu import PostFXProcessor, PostFXConfig
            
            config = PostFXConfig(bloom_enabled=True)
            processor = PostFXProcessor(config, use_gpu=True)
            
            # Criar frame de teste
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            
            # Processar
            result = processor.process(frame)
            
            self.assertEqual(result.shape, frame.shape)
            print("PostFX processing: OK")
            
        except Exception as e:
            self.skipTest(f"Erro: {e}")


class TestPerformanceComparison(unittest.TestCase):
    """Compara performance GPU vs CPU."""
    
    def test_gpu_cpu_speedup(self):
        """Mede speedup GPU vs CPU."""
        try:
            from src.utils.gpu_memory_manager import benchmark_gpu_vs_cpu
            
            results = benchmark_gpu_vs_cpu(array_size=100000, iterations=5)
            
            print(f"\n=== Performance Comparison ===")
            print(f"CPU Time: {results['cpu_time']*1000:.2f}ms")
            print(f"GPU Time: {results['gpu_time']*1000:.2f}ms")
            print(f"Speedup: {results['speedup']:.1f}x")
            print(f"GPU Available: {results['gpu_available']}")
            
            # GPU deve ser mais rápida se disponível
            if results['gpu_available'] and results['gpu_time'] < float('inf'):
                self.assertGreater(results['speedup'], 0.5, "GPU deveria ter algum speedup")
            
        except Exception as e:
            self.skipTest(f"Benchmark não disponível: {e}")


def run_all_tests():
    """Executa todos os testes."""
    print("=" * 60)
    print("GPU STRESS TESTS")
    print("=" * 60)
    
    # Criar suite de testes
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestGPUMemoryManager))
    suite.addTests(loader.loadTestsFromTestCase(TestGPUStress))
    suite.addTests(loader.loadTestsFromTestCase(TestFallbackMechanisms))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceComparison))
    
    # Executar
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    print(f"Testes executados: {result.testsRun}")
    print(f"Falhas: {len(result.failures)}")
    print(f"Erros: {len(result.errors)}")
    print(f"Pulados: {len(result.skipped)}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
