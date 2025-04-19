import pygame
from typing import Tuple, Optional

class Camera:
    def __init__(self, screen_size: Tuple[int, int]):
        self.screen_size = screen_size
        self.x = 0  # Camera position in world coordinates
        self.y = 0
        self.zoom = 1.0  # Zoom level (1.0 = 100%)
        self.min_zoom = 0.5
        self.max_zoom = 2.0
        self.pan_speed = 500  # Pixels per second
        
    def move(self, dx: float, dy: float, dt: float):
        """Move camera by delta, scaled by time and zoom"""
        self.x += dx * dt * self.pan_speed / self.zoom
        self.y += dy * dt * self.pan_speed / self.zoom
        
    def adjust_zoom(self, factor: float, mouse_pos: Optional[Tuple[int, int]] = None):
        """Zoom in/out, optionally centered on mouse position"""
        old_zoom = self.zoom
        self.zoom = max(self.min_zoom, min(self.max_zoom, self.zoom * factor))
        
        # If mouse position is provided, zoom towards that point
        if mouse_pos:
            mouse_x, mouse_y = mouse_pos
            # Convert mouse position to world coordinates before zoom
            world_x = mouse_x / old_zoom + self.x
            world_y = mouse_y / old_zoom + self.y
            # Adjust camera position to keep mouse point fixed
            self.x = world_x - mouse_x / self.zoom
            self.y = world_y - mouse_y / self.zoom
            
    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[float, float]:
        """Convert world coordinates to screen coordinates"""
        screen_x = (world_x - self.x) * self.zoom
        screen_y = (world_y - self.y) * self.zoom
        return screen_x, screen_y
        
    def screen_to_world(self, screen_x: float, screen_y: float) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates"""
        world_x = screen_x / self.zoom + self.x
        world_y = screen_y / self.zoom + self.y
        return world_x, world_y 