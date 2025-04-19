import numpy as np
from noise import snoise2
from enum import Enum
from typing import Tuple, List
import math

class TerrainType(Enum):
    WATER = (0, 0, 255)      # Blue
    PLAINS = (34, 139, 34)   # Forest Green
    FOREST = (0, 100, 0)     # Dark Green
    MOUNTAIN = (139, 137, 137)  # Gray
    TUNDRA = (238, 233, 233)  # Snow White

class World:
    def __init__(self, width: int = 80, height: int = 60):
        self.width = width
        self.height = height
        self.scale = 50.0  # Scale factor for noise
        self.octaves = 6   # Number of passes for noise generation
        self.persistence = 0.5  # How much each octave contributes
        self.lacunarity = 2.0   # How much detail is added in each octave
        self.terrain = self._generate_terrain()
        
        # Hex grid constants
        self.hex_size = 40  # Distance from center to corner
        self.hex_width = self.hex_size * 2
        self.hex_height = self.hex_size * math.sqrt(3)
        # Calculate horizontal and vertical spacing between hexes
        self.hex_horiz_spacing = self.hex_width * 3/4  # Overlapping portion gives tight fit
        self.hex_vert_spacing = self.hex_height
        self.hex_vert = self._calculate_hex_vertices()
        
    def _calculate_hex_vertices(self) -> List[Tuple[float, float]]:
        """Calculate the vertices of a hexagon relative to its center"""
        vertices = []
        for i in range(6):
            angle_deg = 60 * i  # Start at 0 degrees (pointy top)
            angle_rad = math.pi / 180 * angle_deg
            x = self.hex_size * math.cos(angle_rad)
            y = self.hex_size * math.sin(angle_rad)
            vertices.append((x, y))
        return vertices
        
    def point_in_hex(self, px: float, py: float, hex_x: float, hex_y: float) -> bool:
        """Test if a point is inside a hexagon centered at (hex_x, hex_y)"""
        # Translate point to hex-relative coordinates
        dx = px - hex_x
        dy = py - hex_y
        
        # For flat-topped hexagons, we need to check against the hex bounds
        # These are the magic numbers for a flat-topped hex
        x_threshold = self.hex_size * 0.866025404  # sqrt(3)/2
        y_threshold = self.hex_size * 0.5
        
        # Quick boundary check
        if abs(dx) > self.hex_size or abs(dy) > self.hex_height/2:
            return False
            
        # Detailed check using the hex shape
        if abs(dx) <= x_threshold:
            return abs(dy) <= self.hex_size
        else:
            slope = (self.hex_size - abs(dy)) / x_threshold
            return slope * (self.hex_size - abs(dx)) >= 0

    def pixel_to_hex(self, px: float, py: float) -> Tuple[int, int]:
        """Convert pixel coordinates to hex grid coordinates"""
        # Convert to hex coordinate space (using flat-topped hexagon formulas)
        # First convert to axial coordinates
        q = (2.0/3.0 * px) / self.hex_size
        r = (-1.0/3.0 * px + math.sqrt(3)/3.0 * py) / self.hex_size
        
        # Convert to cube coordinates for better rounding
        x = q
        z = r
        y = -x - z
        
        # Round cube coordinates
        rx = round(x)
        ry = round(y)
        rz = round(z)
        
        # Fix rounding errors
        x_diff = abs(rx - x)
        y_diff = abs(ry - y)
        z_diff = abs(rz - z)
        
        if x_diff > y_diff and x_diff > z_diff:
            rx = -ry - rz
        elif y_diff > z_diff:
            ry = -rx - rz
        else:
            rz = -rx - ry
            
        # Convert back to offset coordinates
        col = rx
        row = rz + (rx + (rx & 1)) // 2
        
        # Verify the selected hex using point-in-hex test
        center_x, center_y = self.hex_to_pixel(col, row)
        if not self.point_in_hex(px, py, center_x, center_y):
            # Check immediate neighbors if point isn't in the primary hex
            best_distance = float('inf')
            best_hex = (col, row)
            
            # Define neighbor offsets for flat-topped hexes
            neighbors = [
                (1, 0), (1, -1), (0, -1),
                (-1, -1), (-1, 0), (0, 1)
            ]
            
            for dc, dr in neighbors:
                test_col = col + dc
                test_row = row + dr
                if test_col & 1:  # Adjust row for odd columns
                    test_row += (dr == 0)  # Only adjust when moving horizontally
                test_x, test_y = self.hex_to_pixel(test_col, test_row)
                
                if self.point_in_hex(px, py, test_x, test_y):
                    dx = px - test_x
                    dy = py - test_y
                    dist = dx * dx + dy * dy
                    if dist < best_distance:
                        best_distance = dist
                        best_hex = (test_col, test_row)
            
            return best_hex
            
        return col, row
        
    def hex_to_pixel(self, col: int, row: int) -> Tuple[float, float]:
        """Convert hex grid coordinates to pixel coordinates"""
        # Using flat-topped hexagon coordinate system
        x = col * self.hex_horiz_spacing
        y = (row - (col & 1) * 0.5) * self.hex_vert_spacing  # Adjust offset for odd columns
        return x, y

    def _generate_terrain(self) -> np.ndarray:
        """Generate terrain using Perlin noise"""
        world = np.zeros((self.height, self.width))
        
        # Generate base noise
        for y in range(self.height):
            for x in range(self.width):
                world[y][x] = snoise2(
                    x / self.scale, 
                    y / self.scale, 
                    octaves=self.octaves, 
                    persistence=self.persistence,
                    lacunarity=self.lacunarity
                )
        
        # Normalize values to 0-1 range
        world = (world - world.min()) / (world.max() - world.min())
        return world
    
    def get_terrain_type(self, value: float) -> TerrainType:
        """Convert noise value to terrain type"""
        if value < 0.2:
            return TerrainType.WATER
        elif value < 0.4:
            return TerrainType.PLAINS
        elif value < 0.6:
            return TerrainType.FOREST
        elif value < 0.8:
            return TerrainType.MOUNTAIN
        else:
            return TerrainType.TUNDRA
    
    def get_color_at(self, x: int, y: int) -> Tuple[int, int, int]:
        """Get the color for a specific coordinate"""
        if 0 <= y < self.height and 0 <= x < self.width:
            value = self.terrain[y][x]
            return self.get_terrain_type(value).value
        return (0, 0, 0)  # Black for out of bounds 