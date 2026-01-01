#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GTK Player Module - Video player with perfect aspect ratio preservation
Uses GTK AspectFrame to maintain image proportions during window resize
"""
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk, GLib
import numpy as np
import sys


class AspectRatioPlayerWindow(Gtk.Window):
    """
    GTK Window that displays images/video with perfect aspect ratio preservation
    
    Features:
    - Fully resizable (miniature to fullscreen)
    - Aspect ratio always maintained
    - Smooth scaling
    - Keyboard controls (q/ESC to quit)
    """
    
    def __init__(self, title="Extase em 4R73", initial_width=800, initial_height=600):
        super().__init__(title=title)

        self.set_wmclass("extase-em-4r73", "Extase em 4R73")
        self.set_default_size(initial_width, initial_height)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # AspectFrame automatically maintains aspect ratio during resize
        # This is the magic component that solves the distortion problem!
        self.aspect_frame = Gtk.AspectFrame(
            xalign=0.5,      # Center horizontally
            yalign=0.5,      # Center vertically
            ratio=1.0,       # Will be updated based on image
            obey_child=False # We control the ratio, not the child
        )
        
        # Image widget to display frames
        self.image = Gtk.Image()
        self.aspect_frame.add(self.image)
        
        # Add to window
        self.add(self.aspect_frame)
        
        # Keyboard event handling
        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", self.on_destroy)
        
        # Track if window should close
        self.should_close = False
        
    def on_key_press(self, widget, event):
        """Handle keyboard shortcuts"""
        keyval = event.keyval
        keyname = Gdk.keyval_name(keyval)
        
        # Quit on q or Escape
        if keyname in ['q', 'Q', 'Escape']:
            self.should_close = True
            Gtk.main_quit()
            return True
        
        return False
    
    def on_destroy(self, widget):
        """Handle window close"""
        self.should_close = True
        Gtk.main_quit()
    
    def set_frame(self, np_image):
        """
        Update the displayed frame
        
        Args:
            np_image: NumPy array in BGR format (OpenCV format)
        """
        if np_image is None or np_image.size == 0:
            return
        
        h, w = np_image.shape[:2]
        
        # Update aspect ratio
        aspect_ratio = w / h
        self.aspect_frame.set_property("ratio", aspect_ratio)
        
        # Convert BGR (OpenCV) to RGB (GTK)
        rgb_image = np_image[:, :, ::-1].copy()
        
        # Ensure contiguous memory
        if not rgb_image.flags['C_CONTIGUOUS']:
            rgb_image = np.ascontiguousarray(rgb_image)
        
        # Create GdkPixbuf from NumPy array
        pixbuf = GdkPixbuf.Pixbuf.new_from_data(
            rgb_image.tobytes(),
            GdkPixbuf.Colorspace.RGB,
            False,  # No alpha channel
            8,      # 8 bits per sample
            w, h,
            w * 3,  # Row stride
            None,   # Destroy function
            None    # User data
        )
        
        # Update image
        self.image.set_from_pixbuf(pixbuf)
    
    def process_events(self):
        """Process pending GTK events (for video playback)"""
        while Gtk.events_pending():
            Gtk.main_iteration()


def create_player_window(title="Êxtase em 4R73 - Player", width=800, height=600):
    """
    Create and show a new player window
    
    Args:
        title: Window title
        width: Initial width
        height: Initial height
    
    Returns:
        AspectRatioPlayerWindow instance
    """
    window = AspectRatioPlayerWindow(title=title, initial_width=width, initial_height=height)
    window.show_all()
    return window


if __name__ == '__main__':
    # Test the player with a simple colored rectangle
    window = create_player_window()
    
    # Create test image (gradient)
    test_img = np.zeros((200, 400, 3), dtype=np.uint8)
    for i in range(200):
        for j in range(400):
            test_img[i, j] = [i % 256, j % 256, (i + j) % 256]
    
    window.set_frame(test_img)
    
    print("Test window displayed. Try resizing - aspect ratio is preserved!")
    print("Press 'q' or Escape to quit")
    
    Gtk.main()
