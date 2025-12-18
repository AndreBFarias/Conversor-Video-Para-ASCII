#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Renderer Module - Handles display output for ASCII/Pixel Art converter
Supports terminal (ANSI), OpenCV window, and GTK window rendering
GTK mode provides perfect aspect ratio preservation
"""
import sys
import cv2
import numpy as np

# GTK player for aspect ratio preservation
try:
    from .gtk_player import create_player_window
    GTK_AVAILABLE = True
except ImportError:
    GTK_AVAILABLE = False
    print("Warning: GTK player not available, falling back to OpenCV")

# ANSI escape codes for terminal rendering
ANSI_CLEAR_AND_HOME = "\033[2J\033[H"
ANSI_RESET = "\033[0m"
COLOR_SEPARATOR = "§"

# Window configuration  
DEFAULT_WINDOW_NAME = "ASCII Converter Output"
DEFAULT_SCALE_FACTOR = 2

# ASCII rendering configuration
ASCII_FONT = cv2.FONT_HERSHEY_SIMPLEX
ASCII_FONT_SCALE = 0.4
ASCII_FONT_THICKNESS = 1
ASCII_CHAR_WIDTH = 8
ASCII_CHAR_HEIGHT = 16


def render_terminal(ascii_string):
    """
    Render ASCII art to terminal using ANSI color codes
    
    Args:
        ascii_string: String with ASCII art and ANSI color codes (§-separated format)
    """
    output_buffer = []
    lines = ascii_string.split('\n')

    for line in lines:
        if not line:
            continue
        pixels = line.split(COLOR_SEPARATOR)
        line_buffer = []
        for i in range(0, len(pixels) - 1, 2):
            char = pixels[i]
            code = pixels[i+1]
            if char and code.isdigit():
                line_buffer.append(f"\033[38;5;{code}m{char}")
            elif char:
                line_buffer.append(char)
        output_buffer.append("".join(line_buffer))

    sys.stdout.write(ANSI_CLEAR_AND_HOME)
    sys.stdout.write("\n".join(output_buffer) + ANSI_RESET)
    sys.stdout.flush()


def ansi256_to_bgr(ansi_code):
    """
    Convert ANSI 256 color code to BGR tuple
    
    Args:
        ansi_code: ANSI 256 color code (0-255)
    
    Returns:
        Tuple (B, G, R) representing the color
    """
    ansi_code = int(ansi_code)
    
    # Grayscale colors (232-255)
    if 232 <= ansi_code <= 255:
        gray = int(8 + (ansi_code - 232) * 10.39)
        return (gray, gray, gray)
    
    # Standard system colors (16-231)
    if 16 <= ansi_code <= 231:
        idx = ansi_code - 16
        r = (idx // 36) * 51
        g = ((idx % 36) // 6) * 51
        b = (idx % 6) * 51
        return (b, g, r)
    
    # Basic 16 colors (0-15)
    basic_colors = [
        (0, 0, 0), (128, 0, 0), (0, 128, 0), (128, 128, 0),
        (0, 0, 128), (128, 0, 128), (0, 128, 128), (192, 192, 192),
        (128, 128, 128), (255, 0, 0), (0, 255, 0), (255, 255, 0),
        (0, 0, 255), (255, 0, 255), (0, 255, 255), (255, 255, 255)
    ]
    if 0 <= ansi_code < len(basic_colors):
        r, g, b = basic_colors[ansi_code]
        return (b, g, r)
    
    return (255, 255, 255)  # Default to white


def render_ascii_as_image(ascii_string, font_scale=ASCII_FONT_SCALE):
    """
    Convert ASCII art string to OpenCV image for window rendering
    
    Args:
        ascii_string: String with ASCII art and ANSI color codes (§-separated format)
        font_scale: Font scale for rendering (default: 0.4)
    
    Returns:
        NumPy array (BGR format) of rendered ASCII art
    """
    lines = ascii_string.split('\n')
    
    # Parse lines and extract characters with colors
    parsed_lines = []
    max_width = 0
    
    for line in lines:
        if not line:
            parsed_lines.append([])
            continue
        
        pixels = line.split(COLOR_SEPARATOR)
        chars_with_colors = []
        
        for i in range(0, len(pixels) - 1, 2):
            char = pixels[i]
            code = pixels[i+1] if i+1 < len(pixels) else '255'
            
            if char and code.isdigit():
                chars_with_colors.append((char, int(code)))
            elif char:
                chars_with_colors.append((char, 255))
        
        parsed_lines.append(chars_with_colors)
        max_width = max(max_width, len(chars_with_colors))
    
    # Create canvas
    height = len(parsed_lines) * ASCII_CHAR_HEIGHT
    width = max_width * ASCII_CHAR_WIDTH
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Draw characters
    for y, line in enumerate(parsed_lines):
        for x, (char, ansi_code) in enumerate(line):
            if char.strip():  # Skip spaces
                pos_x = x * ASCII_CHAR_WIDTH
                pos_y = (y + 1) * ASCII_CHAR_HEIGHT - 4
                color = ansi256_to_bgr(ansi_code)
                
                cv2.putText(canvas, char, (pos_x, pos_y), ASCII_FONT, 
                           font_scale, color, ASCII_FONT_THICKNESS, cv2.LINE_AA)
    
    return canvas


def render_window_gtk(pixel_frame, gtk_window=None, is_ascii=False, ascii_string=None):
    """
    Render to GTK window with perfect aspect ratio preservation
    
    Args:
        pixel_frame: NumPy array (BGR format) or None if is_ascii=True
        gtk_window: Existing GTK window or None to create new
        is_ascii: If True, render ascii_string as image
        ascii_string: ASCII art string to render
        
    Returns:
        GTK window instance
    """
    if not GTK_AVAILABLE:
        raise RuntimeError("GTK player not available")
    
    # Convert ASCII to image if needed
    if is_ascii and ascii_string:
        pixel_frame = render_ascii_as_image(ascii_string)
    
    if pixel_frame is None or pixel_frame.size == 0:
        return gtk_window
    
    # Create window if needed
    if gtk_window is None:
        h, w = pixel_frame.shape[:2]
        gtk_window = create_player_window(
            title="Êxtase em 4R73 - Player",
            width=w * 2,  # Initial 2x scale
            height=h * 2
        )
    
    # Update frame
    gtk_window.set_frame(pixel_frame)
    
    return gtk_window


def render_window(pixel_frame, window_name=DEFAULT_WINDOW_NAME, scale_factor=DEFAULT_SCALE_FACTOR, 
                 is_ascii=False, ascii_string=None):
    """
    Render to OpenCV window (fallback mode)
    
    Note: Has aspect ratio limitations, use render_window_gtk for better results
    """
    # Convert ASCII to image if needed
    if is_ascii and ascii_string:
        pixel_frame = render_ascii_as_image(ascii_string)
    
    if pixel_frame is None or pixel_frame.size == 0:
        return scale_factor
    
    # Create resizable window
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    # Get original dimensions and apply initial scale
    h, w = pixel_frame.shape[:2]
    
    if scale_factor > 1:
        upscaled_h = int(h * scale_factor)
        upscaled_w = int(w * scale_factor)
        display_frame = cv2.resize(pixel_frame, (upscaled_w, upscaled_h), 
                                  interpolation=cv2.INTER_LINEAR)
    else:
        display_frame = pixel_frame
        upscaled_w, upscaled_h = w, h
    
    # Display the frame
    cv2.imshow(window_name, display_frame)
    
    # Set initial window size
    try:
        cv2.resizeWindow(window_name, upscaled_w, upscaled_h)
    except:
        pass
    
    return scale_factor


def cleanup_window(window_name=DEFAULT_WINDOW_NAME):
    """
    Clean up OpenCV window resources
    
    Args:
        window_name: Name of the window to destroy
    """
    try:
        cv2.destroyWindow(window_name)
        cv2.waitKey(1)
    except Exception:
        pass
