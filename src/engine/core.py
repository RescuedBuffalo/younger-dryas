import pygame
import sys
from typing import Tuple, List, Optional, Dict
from world.world import World, TerrainType
from game.mechanics import GameState, ImprovementType, ResourceType
from .camera import Camera

class GameEngine:
    def __init__(self, screen_size: Tuple[int, int] = (800, 600)):
        pygame.init()
        self.screen_size = screen_size
        self.screen = pygame.display.set_mode(screen_size)
        pygame.display.set_caption("Younger Dryas")
        self.clock = pygame.time.Clock()
        self.running = True
        self.fps = 60
        
        # Initialize world and camera
        world_width = 100
        world_height = 80
        self.world = World(world_width, world_height)
        self.camera = Camera(screen_size)
        
        # Initialize game state
        self.game_state = GameState()
        
        # Input state
        self.dragging = False
        self.last_mouse_pos = None
        self.selected_hex: Optional[Tuple[int, int]] = None
        self.hovered_hex: Optional[Tuple[int, int]] = None
        self.drag_start_pos = None
        
        # UI state
        self.show_build_menu = False
        self.show_escape_menu = False
        self.build_options = list(ImprovementType)
        self.selected_improvement = None
        self.action_buttons = self._create_action_buttons()
        self.escape_menu_buttons = self._create_escape_menu_buttons()
        
    def _create_escape_menu_buttons(self) -> List[Dict]:
        """Create the escape menu buttons"""
        button_width = 200
        button_height = 50
        spacing = 20
        
        buttons = []
        buttons.append({
            'rect': pygame.Rect(
                (self.screen_size[0] - button_width) // 2,
                (self.screen_size[1] - button_height) // 2,
                button_width,
                button_height
            ),
            'text': 'Quit Game',
            'action': 'quit',
            'hover': False
        })
        
        return buttons
        
    def _create_action_buttons(self) -> List[Dict]:
        """Create the action buttons configuration"""
        button_width = 120
        button_height = 40
        spacing = 10
        start_x = 10
        bottom_y = self.screen_size[1] - button_height - 10
        
        buttons = []
        
        # Add claim tile button first
        buttons.append({
            'rect': pygame.Rect(start_x, bottom_y, button_width, button_height),
            'text': 'Claim Tile',
            'action': 'claim',
            'hover': False
        })
        
        # Add improvement buttons
        for i, improvement in enumerate(self.build_options, 1):  # Start at 1 to account for claim button
            buttons.append({
                'rect': pygame.Rect(start_x + i * (button_width + spacing), bottom_y, button_width, button_height),
                'text': improvement.value,
                'action': improvement,
                'hover': False
            })
        
        # Add end turn button
        end_turn_rect = pygame.Rect(
            self.screen_size[0] - button_width - 10,
            bottom_y,
            button_width,
            button_height
        )
        buttons.append({
            'rect': end_turn_rect,
            'text': 'End Turn',
            'action': 'end_turn',
            'hover': False
        })
        
        return buttons
        
    def get_hex_at_screen_pos(self, screen_pos: Tuple[float, float]) -> Optional[Tuple[int, int]]:
        """Convert screen coordinates to hex grid coordinates"""
        # Check if mouse is outside the window
        if (screen_pos[0] < 0 or screen_pos[0] >= self.screen_size[0] or 
            screen_pos[1] < 0 or screen_pos[1] >= self.screen_size[1]):
            return None
            
        # Convert screen to world coordinates
        world_x, world_y = self.camera.screen_to_world(*screen_pos)
        col, row = self.world.pixel_to_hex(world_x, world_y)
        
        # Wrap coordinates to world bounds
        return (col % self.world.width, row % self.world.height)
        
    def handle_events(self):
        # Update button hover states
        mouse_pos = pygame.mouse.get_pos()
        for button in self.action_buttons:
            button['hover'] = button['rect'].collidepoint(mouse_pos)
        if self.show_escape_menu:
            for button in self.escape_menu_buttons:
                button['hover'] = button['rect'].collidepoint(mouse_pos)
        
        # Store previous states
        prev_hovered = self.hovered_hex
        
        # Update hover state
        current_hex = self.get_hex_at_screen_pos(mouse_pos)
        
        if current_hex is None and not self.dragging:
            self.hovered_hex = None
        else:
            self.hovered_hex = current_hex
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.show_build_menu:
                        self.show_build_menu = False
                    else:
                        self.show_escape_menu = not self.show_escape_menu
                elif event.key == pygame.K_SPACE and not self.show_escape_menu:
                    self.game_state.end_turn()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if self.show_escape_menu:
                        # Handle escape menu clicks
                        for button in self.escape_menu_buttons:
                            if button['rect'].collidepoint(event.pos):
                                if button['action'] == 'quit':
                                    self.running = False
                                break
                    else:
                        # Check if clicked on an action button
                        for button in self.action_buttons:
                            if button['rect'].collidepoint(event.pos):
                                if button['action'] == 'end_turn':
                                    self.game_state.end_turn()
                                elif button['action'] == 'claim' and self.hovered_hex:
                                    col, row = self.hovered_hex
                                    if self.game_state.claim_hex(col, row):
                                        self.selected_hex = self.hovered_hex
                                elif self.selected_hex:
                                    col, row = self.selected_hex
                                    self.game_state.build_improvement(col, row, button['action'])
                                break
                        else:  # If no button was clicked
                            if self.show_build_menu:
                                self.handle_build_menu_click(event.pos)
                            else:
                                self.dragging = True
                                self.last_mouse_pos = event.pos
                                self.drag_start_pos = event.pos
                elif event.button == 3 and not self.show_escape_menu:  # Right click
                    if self.selected_hex:
                        self.show_build_menu = True
                elif event.button == 4:  # Mouse wheel up
                    self.camera.adjust_zoom(1.1, event.pos)
                elif event.button == 5:  # Mouse wheel down
                    self.camera.adjust_zoom(0.9, event.pos)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left click
                    self.dragging = False
                    if (self.drag_start_pos and 
                        abs(event.pos[0] - self.drag_start_pos[0]) < 5 and 
                        abs(event.pos[1] - self.drag_start_pos[1]) < 5):
                        self.handle_hex_click()
                    self.drag_start_pos = None
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging and self.last_mouse_pos:
                    current_pos = event.pos
                    dx = current_pos[0] - self.last_mouse_pos[0]
                    dy = current_pos[1] - self.last_mouse_pos[1]
                    self.camera.move(-dx, -dy, 1/self.fps)
                    self.last_mouse_pos = current_pos
                    
    def handle_hex_click(self):
        """Handle clicking on a hex"""
        if not self.hovered_hex:
            return
            
        col, row = self.hovered_hex
        hex_data = self.game_state.get_hex_data(col, row)
        
        # If hex is unclaimed and we can claim it, do so
        if hex_data.owner is None and self.game_state.can_claim_hex(col, row):
            self.game_state.claim_hex(col, row)
            self.selected_hex = self.hovered_hex
        else:
            # Toggle selection if clicking owned hex
            if self.hovered_hex == self.selected_hex:
                self.selected_hex = None
            else:
                self.selected_hex = self.hovered_hex
                
    def handle_build_menu_click(self, pos: Tuple[int, int]):
        """Handle clicking in the build menu"""
        if not self.selected_hex:
            return
            
        # Calculate which improvement was clicked
        menu_x, menu_y = self.screen_size[0] - 210, 100
        option_height = 30
        
        for i, improvement in enumerate(self.build_options):
            option_rect = pygame.Rect(menu_x, menu_y + i * option_height, 200, option_height - 2)
            if option_rect.collidepoint(pos):
                col, row = self.selected_hex
                if self.game_state.build_improvement(col, row, improvement):
                    self.show_build_menu = False
                break
                
    def update(self):
        # Handle keyboard input for camera movement
        keys = pygame.key.get_pressed()
        dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
        dy = keys[pygame.K_DOWN] - keys[pygame.K_UP]
        if dx != 0 or dy != 0:
            self.camera.move(dx, dy, 1/self.fps)
        
    def render(self):
        self.screen.fill((0, 0, 0))  # Clear screen
        
        # Calculate visible area
        padding_x = self.world.hex_size * 2 / self.camera.zoom
        padding_y = self.world.hex_size * 2 / self.camera.zoom
        left, top = self.camera.screen_to_world(-padding_x, -padding_y)
        right, bottom = self.camera.screen_to_world(
            self.screen_size[0] + padding_x, 
            self.screen_size[1] + padding_y
        )
        
        # Convert world bounds to hex coordinates
        start_col, start_row = self.world.pixel_to_hex(left, top)
        end_col, end_row = self.world.pixel_to_hex(right, bottom)
        
        # Add padding to ensure we render tiles just outside view
        start_col -= 2
        start_row -= 2
        end_col += 2
        end_row += 2
        
        # First pass: Draw hex fills
        visible_hexes = []
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                # Get hex center in world coordinates
                center_x, center_y = self.world.hex_to_pixel(col, row)
                
                # Convert to screen coordinates
                screen_x, screen_y = self.camera.world_to_screen(center_x, center_y)
                
                # Calculate vertices
                vertices = []
                for vx, vy in self.world.hex_vert:
                    screen_vx = screen_x + vx * self.camera.zoom
                    screen_vy = screen_y + vy * self.camera.zoom
                    vertices.append((screen_vx, screen_vy))
                
                # Check if hex is potentially visible
                min_x = min(v[0] for v in vertices)
                max_x = max(v[0] for v in vertices)
                min_y = min(v[1] for v in vertices)
                max_y = max(v[1] for v in vertices)
                
                if (max_x >= -self.world.hex_size and 
                    min_x <= self.screen_size[0] + self.world.hex_size and
                    max_y >= -self.world.hex_size and 
                    min_y <= self.screen_size[1] + self.world.hex_size):
                    # Get terrain color
                    wrapped_col = col % self.world.width
                    wrapped_row = row % self.world.height
                    color = self.world.get_color_at(wrapped_col, wrapped_row)
                    
                    # Modify color based on ownership
                    hex_data = self.game_state.get_hex_data(col, row)
                    if hex_data.owner is not None:
                        player_color = self.game_state.players[hex_data.owner].color
                        # Blend with terrain color
                        color = tuple(
                            int((c1 * 0.7 + c2 * 0.3))
                            for c1, c2 in zip(player_color, color)
                        )
                    
                    # Draw base hex fill
                    pygame.draw.polygon(self.screen, color, vertices)
                    
                    # Draw improvement icon if any
                    if hex_data.improvement:
                        self.draw_improvement_icon(screen_x, screen_y, hex_data.improvement)
                    
                    # Store for border rendering
                    hex_coord = (col, row)
                    visible_hexes.append((vertices, hex_coord))
        
        # Second pass: Draw borders
        for vertices, hex_coord in visible_hexes:
            # Draw borders as individual lines for consistent thickness
            for i in range(len(vertices)):
                start = vertices[i]
                end = vertices[(i + 1) % len(vertices)]
                
                # Determine border color and width based on hex state
                if hex_coord == self.selected_hex:
                    # Draw a thicker white border for selected hex
                    width = max(3, int(self.camera.zoom * 2.5))
                    # Draw outer glow
                    pygame.draw.line(self.screen, (200, 200, 200), start, end, width + 2)
                    # Draw main border
                    pygame.draw.line(self.screen, (255, 255, 255), start, end, width)
                elif hex_coord == self.hovered_hex and not self.dragging:
                    # Draw a more visible hover effect
                    width = max(2, int(self.camera.zoom * 2))
                    # Draw outer glow
                    pygame.draw.line(self.screen, (140, 140, 140), start, end, width + 2)
                    # Draw main border
                    pygame.draw.line(self.screen, (180, 180, 180), start, end, width)
                elif self.camera.zoom > 0.7:
                    # Normal hex borders
                    color = (32, 32, 32)  # Dark gray for normal
                    width = max(1, int(self.camera.zoom))
                    pygame.draw.line(self.screen, color, start, end, width)
                else:
                    continue  # Skip borders when zoomed out too far
        
        # Render UI elements
        self._render_game_info()
        if self.selected_hex is not None:
            self._render_selected_hex_info()
        if self.show_build_menu:
            self._render_build_menu()
        
        # Render action buttons
        for button in self.action_buttons:
            # Draw button background
            color = (70, 70, 70) if button['hover'] else (50, 50, 50)
            if button['action'] == 'claim':
                # Show if claims are available
                claims_left = (self.game_state.MAX_CLAIMS_PER_TURN - 
                             self.game_state.current_player.claims_this_turn)
                if claims_left <= 0:
                    color = (40, 40, 40)  # Darker if no claims left
            pygame.draw.rect(self.screen, color, button['rect'])
            
            # Draw button border
            border_color = (200, 200, 200) if button['hover'] else (100, 100, 100)
            pygame.draw.rect(self.screen, border_color, button['rect'], 2)
            
            # Draw button text
            font = pygame.font.Font(None, 24)
            text = font.render(button['text'], True, (255, 255, 255))
            text_rect = text.get_rect(center=button['rect'].center)
            self.screen.blit(text, text_rect)
            
            # Show resource cost if it's an improvement button
            if isinstance(button['action'], ImprovementType):
                costs = self.game_state.IMPROVEMENT_COSTS[button['action']]
                cost_text = ", ".join(f"{amount} {res.value}" for res, amount in costs.items())
                cost_surface = font.render(cost_text, True, (200, 200, 200))
                cost_rect = cost_surface.get_rect(
                    midtop=(button['rect'].centerx, button['rect'].bottom + 5)
                )
                self.screen.blit(cost_surface, cost_rect)
            elif button['action'] == 'claim':
                # Show remaining claims
                claims_left = (self.game_state.MAX_CLAIMS_PER_TURN - 
                             self.game_state.current_player.claims_this_turn)
                status_text = f"Claims left: {claims_left}"
                status_surface = font.render(status_text, True, (200, 200, 200))
                status_rect = status_surface.get_rect(
                    midtop=(button['rect'].centerx, button['rect'].bottom + 5)
                )
                self.screen.blit(status_surface, status_rect)
        
        # Render action log
        self._render_action_log()
        
        # Render escape menu if shown
        if self.show_escape_menu:
            self._render_escape_menu()
        
        pygame.display.flip()
        
    def draw_improvement_icon(self, x: float, y: float, improvement: ImprovementType):
        """Draw an icon representing the improvement"""
        icon_size = max(20, int(20 * self.camera.zoom))
        icon_rect = pygame.Rect(x - icon_size//2, y - icon_size//2, icon_size, icon_size)
        
        # Different shapes for different improvements
        if improvement == ImprovementType.SETTLEMENT:
            pygame.draw.polygon(self.screen, (255, 255, 255), [
                (x, y - icon_size//2),  # Top
                (x + icon_size//2, y + icon_size//2),  # Bottom right
                (x - icon_size//2, y + icon_size//2),  # Bottom left
            ])
        elif improvement == ImprovementType.FARM:
            pygame.draw.rect(self.screen, (255, 255, 0), icon_rect)
        elif improvement == ImprovementType.LUMBER_CAMP:
            pygame.draw.rect(self.screen, (139, 69, 19), icon_rect)
        elif improvement == ImprovementType.QUARRY:
            pygame.draw.circle(self.screen, (169, 169, 169), (x, y), icon_size//2)
            
    def _render_game_info(self):
        """Render game state information"""
        font = pygame.font.Font(None, 24)
        current_player = self.game_state.current_player
        
        # Create a semi-transparent panel
        panel_surface = pygame.Surface((200, 150))
        panel_surface.fill((50, 50, 50))
        panel_surface.set_alpha(200)
        self.screen.blit(panel_surface, (10, 10))
        
        # Render text
        texts = [
            f"Turn: {self.game_state.turn_number}",
            f"Player: {current_player.id + 1}",
            "Resources:",
            f"  Food: {current_player.resources[ResourceType.FOOD]}",
            f"  Wood: {current_player.resources[ResourceType.WOOD]}",
            f"  Stone: {current_player.resources[ResourceType.STONE]}",
            "",
            "Space: End Turn"
        ]
        
        for i, text in enumerate(texts):
            text_surface = font.render(text, True, (255, 255, 255))
            self.screen.blit(text_surface, (20, 20 + i * 20))
            
    def _render_selected_hex_info(self):
        """Render information about the selected hex"""
        if not self.selected_hex:
            return
            
        col, row = self.selected_hex
        hex_data = self.game_state.get_hex_data(col, row)
        terrain_value = self.world.terrain[row % self.world.height][col % self.world.width]
        terrain_type = self.world.get_terrain_type(terrain_value)
        
        # Create a semi-transparent info panel
        panel_surface = pygame.Surface((200, 120))
        panel_surface.fill((50, 50, 50))
        panel_surface.set_alpha(200)
        self.screen.blit(panel_surface, (10, 170))
        
        # Render text
        font = pygame.font.Font(None, 24)
        texts = [
            f"Hex: ({col}, {row})",
            f"Terrain: {terrain_type.name}",
            f"Owner: {'None' if hex_data.owner is None else f'Player {hex_data.owner + 1}'}",
            f"Improvement: {hex_data.improvement.name if hex_data.improvement else 'None'}",
            "",
            "Right Click: Build Menu"
        ]
        
        for i, text in enumerate(texts):
            text_surface = font.render(text, True, (255, 255, 255))
            self.screen.blit(text_surface, (20, 180 + i * 20))
            
    def _render_build_menu(self):
        """Render the build menu"""
        if not self.selected_hex:
            return
            
        col, row = self.selected_hex
        
        # Create a semi-transparent menu panel
        menu_x = self.screen_size[0] - 210
        menu_height = len(self.build_options) * 30 + 40
        panel_surface = pygame.Surface((200, menu_height))
        panel_surface.fill((50, 50, 50))
        panel_surface.set_alpha(200)
        self.screen.blit(panel_surface, (menu_x, 100))
        
        # Render title
        font = pygame.font.Font(None, 24)
        title = font.render("Build Improvement", True, (255, 255, 255))
        self.screen.blit(title, (menu_x + 10, 110))
        
        # Render improvement options
        for i, improvement in enumerate(self.build_options):
            y = 140 + i * 30
            option_rect = pygame.Rect(menu_x, y, 200, 28)
            
            # Highlight if can build
            if self.game_state.can_build(col, row, improvement):
                pygame.draw.rect(self.screen, (70, 70, 70), option_rect)
            
            # Render improvement name and cost
            name = font.render(improvement.value, True, (255, 255, 255))
            self.screen.blit(name, (menu_x + 10, y + 5))
            
            # Render cost
            costs = self.game_state.IMPROVEMENT_COSTS[improvement]
            cost_text = ", ".join(f"{amount} {res.value}" for res, amount in costs.items())
            cost_surface = font.render(cost_text, True, (200, 200, 200))
            self.screen.blit(cost_surface, (menu_x + 100, y + 5))
            
    def _render_action_log(self):
        """Render the recent action log"""
        log_entries = self.game_state.get_recent_logs()
        if not log_entries:
            return
            
        # Create log panel
        panel_height = len(log_entries) * 20 + 20
        panel_surface = pygame.Surface((400, panel_height))
        panel_surface.fill((30, 30, 30))
        panel_surface.set_alpha(200)
        
        # Position log panel above the action buttons
        panel_x = 10
        panel_y = self.screen_size[1] - panel_height - 70  # Above action buttons
        
        self.screen.blit(panel_surface, (panel_x, panel_y))
        
        # Render log entries
        font = pygame.font.Font(None, 20)
        for i, entry in enumerate(log_entries):
            text = font.render(entry, True, (200, 200, 200))
            self.screen.blit(text, (panel_x + 10, panel_y + 10 + i * 20))
        
    def _render_escape_menu(self):
        """Render the escape menu overlay"""
        # Create semi-transparent overlay
        overlay = pygame.Surface(self.screen_size)
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))
        
        # Render menu title
        font = pygame.font.Font(None, 48)
        title = font.render("Game Menu", True, (255, 255, 255))
        title_rect = title.get_rect(
            centerx=self.screen_size[0] // 2,
            centery=self.screen_size[1] // 2 - 100
        )
        self.screen.blit(title, title_rect)
        
        # Render buttons
        for button in self.escape_menu_buttons:
            # Draw button background
            color = (70, 70, 70) if button['hover'] else (50, 50, 50)
            pygame.draw.rect(self.screen, color, button['rect'])
            
            # Draw button border
            border_color = (200, 200, 200) if button['hover'] else (100, 100, 100)
            pygame.draw.rect(self.screen, border_color, button['rect'], 2)
            
            # Draw button text
            font = pygame.font.Font(None, 36)
            text = font.render(button['text'], True, (255, 255, 255))
            text_rect = text.get_rect(center=button['rect'].center)
            self.screen.blit(text, text_rect)
        
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(self.fps)
        
        pygame.quit()
        sys.exit() 