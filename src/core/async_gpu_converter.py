import cupy as cp
import numpy as np
from typing import List, Tuple, Optional
import queue
import threading

from .gpu_converter import GPUConverter


class AsyncGPUConverter:
    def __init__(
        self,
        target_width: int,
        target_height: int,
        num_streams: int = 4,
        braille_enabled: bool = False,
        temporal_coherence: bool = False,
        luminance_ramp: str = None
    ):
        self.target_width = target_width
        self.target_height = target_height
        self.num_streams = num_streams

        self.gpu_converter = GPUConverter(
            target_width,
            target_height,
            braille_enabled=braille_enabled,
            temporal_coherence=temporal_coherence,
            luminance_ramp=luminance_ramp
        )

        self.streams = [cp.cuda.Stream() for _ in range(num_streams)]

        grid_w = target_width
        grid_h = target_height

        if braille_enabled:
            grid_w = target_width // 2
            grid_h = target_height // 4

        self.grid_w = grid_w
        self.grid_h = grid_h

        self.frame_buffers_gray = [
            cp.zeros((grid_h, grid_w), dtype=cp.uint8)
            for _ in range(num_streams)
        ]

        self.frame_buffers_color = [
            cp.zeros((grid_h, grid_w, 3), dtype=cp.uint8)
            for _ in range(num_streams)
        ]

        self.char_indices_buffers = [
            cp.zeros((grid_h, grid_w), dtype=cp.int32)
            for _ in range(num_streams)
        ]

        self.color_indices_buffers = [
            cp.zeros((grid_h, grid_w), dtype=cp.int32)
            for _ in range(num_streams)
        ]

    def process_frame_async(
        self,
        gray_frame: np.ndarray,
        color_frame: np.ndarray,
        stream_idx: int
    ) -> Tuple[cp.ndarray, cp.ndarray]:
        stream = self.streams[stream_idx]

        with stream:
            gray_gpu = cp.asarray(gray_frame, dtype=cp.uint8)
            color_gpu = cp.asarray(color_frame, dtype=cp.uint8)

            if self.gpu_converter.braille_enabled:
                char_indices_gpu = self.gpu_converter.convert_to_braille(
                    gray_gpu,
                    threshold=128
                )

                downsampled_gray = gray_gpu[::4, ::2]
                downsampled_color = cp.array(
                    [
                        [color_gpu[y * 4, x * 2] for x in range(self.grid_w)]
                        for y in range(self.grid_h)
                    ],
                    dtype=cp.uint8
                )

                if self.gpu_converter.temporal_coherence:
                    char_indices_gpu = self.gpu_converter.apply_temporal_coherence(
                        char_indices_gpu,
                        downsampled_gray,
                        threshold=20
                    )

                color_indices_gpu = self.gpu_converter.renderer_module.rgb_to_ansi256_vectorized(
                    downsampled_color
                )
            else:
                lum_indices = ((gray_gpu / 255.0) * (len(self.gpu_converter.ramp_gpu) - 1)).astype(cp.int32)
                char_indices_gpu = self.gpu_converter.ramp_gpu[lum_indices]

                if self.gpu_converter.temporal_coherence:
                    char_indices_gpu = self.gpu_converter.apply_temporal_coherence(
                        char_indices_gpu,
                        gray_gpu,
                        threshold=20
                    )

                color_indices_gpu = self.gpu_converter.renderer_module.rgb_to_ansi256_vectorized(
                    color_gpu
                )

            cp.copyto(self.char_indices_buffers[stream_idx], char_indices_gpu)
            cp.copyto(self.color_indices_buffers[stream_idx], color_indices_gpu)

        return self.char_indices_buffers[stream_idx], self.color_indices_buffers[stream_idx]

    def process_batch(
        self,
        gray_frames: List[np.ndarray],
        color_frames: List[np.ndarray]
    ) -> List[Tuple[np.ndarray, np.ndarray]]:
        num_frames = len(gray_frames)
        results = [None] * num_frames

        for i in range(num_frames):
            stream_idx = i % self.num_streams
            results[i] = self.process_frame_async(
                gray_frames[i],
                color_frames[i],
                stream_idx
            )

        for stream in self.streams:
            stream.synchronize()

        return [
            (char_buf.get(), color_buf.get())
            for char_buf, color_buf in results
        ]

    def render_batch_async(
        self,
        char_indices_batch: List[cp.ndarray],
        color_indices_batch: List[cp.ndarray]
    ) -> List[np.ndarray]:
        num_frames = len(char_indices_batch)
        results = [None] * num_frames

        for i in range(num_frames):
            stream_idx = i % self.num_streams
            stream = self.streams[stream_idx]

            with stream:
                result_gpu = self.gpu_converter.render_frame(
                    char_indices_batch[i],
                    color_indices_batch[i]
                )
                results[i] = result_gpu

        for stream in self.streams:
            stream.synchronize()

        return [result.get() if result is not None else None for result in results]


class AsyncPipeline:
    def __init__(
        self,
        async_converter: AsyncGPUConverter,
        batch_size: int = 8,
        queue_size: int = 16
    ):
        self.async_converter = async_converter
        self.batch_size = batch_size

        self.input_queue = queue.Queue(maxsize=queue_size)
        self.output_queue = queue.Queue(maxsize=queue_size)

        self.processing_thread = None
        self.running = False

    def start(self):
        self.running = True
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()

    def stop(self):
        self.running = False
        self.input_queue.put(None)
        if self.processing_thread:
            self.processing_thread.join(timeout=5)

    def put_frame(self, gray_frame: np.ndarray, color_frame: np.ndarray):
        self.input_queue.put((gray_frame, color_frame))

    def get_result(self, timeout: Optional[float] = None):
        return self.output_queue.get(timeout=timeout)

    def _processing_loop(self):
        gray_batch = []
        color_batch = []

        while self.running:
            try:
                item = self.input_queue.get(timeout=0.1)

                if item is None:
                    break

                gray_frame, color_frame = item
                gray_batch.append(gray_frame)
                color_batch.append(color_frame)

                if len(gray_batch) >= self.batch_size:
                    results = self.async_converter.process_batch(gray_batch, color_batch)

                    for char_indices, color_indices in results:
                        self.output_queue.put((char_indices, color_indices))

                    gray_batch = []
                    color_batch = []

            except queue.Empty:
                if gray_batch:
                    results = self.async_converter.process_batch(gray_batch, color_batch)

                    for char_indices, color_indices in results:
                        self.output_queue.put((char_indices, color_indices))

                    gray_batch = []
                    color_batch = []
                continue

        if gray_batch:
            results = self.async_converter.process_batch(gray_batch, color_batch)
            for char_indices, color_indices in results:
                self.output_queue.put((char_indices, color_indices))
