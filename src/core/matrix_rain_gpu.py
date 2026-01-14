import numpy as np
from typing import Tuple, Optional

CHAR_SETS = {
    'katakana': [ord(c) for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*+=<>'],
    'binary': [ord('0'), ord('1')],
    'hex': [ord(c) for c in '0123456789ABCDEF'],
    'ascii': list(range(33, 127)),
    'math': [ord(c) for c in '+-*/=<>^~|&%#@!?'],
}


class MatrixRainGPU:
    def __init__(
        self,
        grid_w: int,
        grid_h: int,
        num_particles: int = 5000,
        char_set: str = 'katakana',
        speed_multiplier: float = 1.0
    ):
        self.grid_w = grid_w
        self.grid_h = grid_h
        self.speed_multiplier = max(0.1, speed_multiplier)
        self.num_columns = grid_w
        self.trail_length = min(grid_h, 15)
        self.char_set_name = char_set

        self._init_arrays()
        self._init_columns(char_set)

    def _init_arrays(self):
        self.canvas_char = np.full((self.grid_h, self.grid_w), ord(' '), dtype=np.uint16)
        self.canvas_color = np.zeros((self.grid_h, self.grid_w, 3), dtype=np.uint8)

    def _init_columns(self, char_set: str):
        self.charset = np.array(CHAR_SETS.get(char_set, CHAR_SETS['katakana']), dtype=np.uint16)
        self.charset_len = len(self.charset)

        self.head_y = np.random.uniform(0, self.grid_h, self.num_columns).astype(np.float32)
        self.speeds = np.random.uniform(0.5, 1.5, self.num_columns).astype(np.float32)

        self.char_grid = np.random.randint(0, self.charset_len, (self.grid_h, self.grid_w), dtype=np.int32)
        self.brightness_grid = np.zeros((self.grid_h, self.grid_w), dtype=np.float32)

        for _ in range(10):
            self._update_internal(0.1)

    def resize(self, new_w: int, new_h: int):
        if new_w == self.grid_w and new_h == self.grid_h:
            return

        self.grid_w = new_w
        self.grid_h = new_h
        self.num_columns = new_w
        self.trail_length = min(new_h, 15)

        self._init_arrays()
        self._init_columns(self.char_set_name)

    def _update_internal(self, dt: float):
        movement = self.speeds * 5.0 * dt * self.speed_multiplier
        self.head_y += movement

        reset_mask = self.head_y > self.grid_h + self.trail_length
        num_reset = np.sum(reset_mask)
        if num_reset > 0:
            self.head_y[reset_mask] = np.random.uniform(-self.trail_length, 0, num_reset)
            self.speeds[reset_mask] = np.random.uniform(0.5, 1.5, num_reset)

        self.brightness_grid *= 0.85

        head_int = self.head_y.astype(np.int32)

        for col in range(self.num_columns):
            head = head_int[col]
            for offset in range(self.trail_length):
                y = head - offset
                if 0 <= y < self.grid_h:
                    if offset == 0:
                        self.brightness_grid[y, col] = 1.5
                    elif offset == 1:
                        self.brightness_grid[y, col] = max(self.brightness_grid[y, col], 1.3)
                    else:
                        trail_val = 1.0 - (offset / self.trail_length) * 0.7
                        self.brightness_grid[y, col] = max(self.brightness_grid[y, col], trail_val)

    def update(self, dt: float = 0.033, gravity: float = 200.0):
        self._update_internal(dt)

        if np.random.random() < 0.3:
            num_changes = max(1, int(self.grid_w * self.grid_h * 0.02))
            change_y = np.random.randint(0, self.grid_h, num_changes)
            change_x = np.random.randint(0, self.grid_w, num_changes)
            self.char_grid[change_y, change_x] = np.random.randint(0, self.charset_len, num_changes)

    def render(self, canvas_char, canvas_color):
        target_h, target_w = canvas_char.shape[:2]

        if target_h != self.grid_h or target_w != self.grid_w:
            self.resize(target_w, target_h)

        self.canvas_char.fill(ord(' '))
        self.canvas_color.fill(0)

        bright_mask = self.brightness_grid > 0.05

        if not np.any(bright_mask):
            canvas_char[:] = self.canvas_char
            canvas_color[:] = self.canvas_color
            return

        ys, xs = np.where(bright_mask)

        for i in range(len(ys)):
            y, x = ys[i], xs[i]
            brightness = self.brightness_grid[y, x]
            char_idx = self.char_grid[y, x]

            self.canvas_char[y, x] = self.charset[char_idx]

            if brightness >= 1.2:
                self.canvas_color[y, x] = [200, 255, 200]
            elif brightness >= 0.8:
                self.canvas_color[y, x] = [50, 255, 50]
            elif brightness >= 0.5:
                g_val = int(200 * brightness)
                self.canvas_color[y, x] = [0, g_val, 0]
            else:
                g_val = int(150 * brightness)
                self.canvas_color[y, x] = [0, g_val, 0]

        try:
            import cupy as cp
            if hasattr(canvas_char, 'device'):
                canvas_char[:] = cp.asarray(self.canvas_char)
                canvas_color[:] = cp.asarray(self.canvas_color)
            else:
                canvas_char[:] = self.canvas_char
                canvas_color[:] = self.canvas_color
        except:
            canvas_char[:] = self.canvas_char
            canvas_color[:] = self.canvas_color

    def render_with_mask(self, canvas_char, canvas_color, mask):
        self.render(canvas_char, canvas_color)

    def render_blend(self, canvas_char, canvas_color, alpha: float = 0.5):
        self.render(canvas_char, canvas_color)

    def change_char_set(self, char_set: str):
        self.char_set_name = char_set
        self.charset = np.array(CHAR_SETS.get(char_set, CHAR_SETS['katakana']), dtype=np.uint16)
        self.charset_len = len(self.charset)
        self.char_grid = np.random.randint(0, self.charset_len, (self.grid_h, self.grid_w), dtype=np.int32)

    def set_speed(self, speed_multiplier: float):
        self.speed_multiplier = max(0.1, speed_multiplier)


# "A consciencia e a unica coisa que nao pode ser simulada." - Godel
