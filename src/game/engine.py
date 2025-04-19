class GameEngine:
    def __init__(self, screen_size=(800, 600)):
        pygame.init()
        self.screen_size = screen_size
        self.screen = pygame.display.set_mode(screen_size)
        pygame.display.set_caption("Younger Dryas")
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.running = True
        self.world = World(screen_size)
        self.ui = UI(screen_size)
        self.game_state = GameState()
        self.victory_font = pygame.font.Font(None, 74)  # Large font for victory message
        self.button_font = pygame.font.Font(None, 36)  # Smaller font for buttons
        
    def run(self):
        """Main game loop"""
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.handle_input(event)
            
            # Update and render
            self.render()
            self.clock.tick(self.fps)
        
        pygame.quit()
        
    def render_victory_screen(self):
        """Render the victory screen with darkened background"""
        # Create a semi-transparent dark overlay
        overlay = pygame.Surface(self.screen_size)
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))
        
        # Render victory message
        if self.game_state.winner:
            message = f"Player {self.game_state.winner.id + 1} Wins!"
            message_color = self.game_state.winner.color
        else:
            message = "It's a Tie!"
            message_color = (255, 255, 255)
            
        text = self.victory_font.render(message, True, message_color)
        text_rect = text.get_rect(center=(self.screen_size[0] // 2, self.screen_size[1] // 2 - 50))
        self.screen.blit(text, text_rect)
        
        # Render points
        if self.game_state.winner:
            points = self.game_state.calculate_player_points(self.game_state.winner)
            points_text = self.button_font.render(f"Points: {points}", True, message_color)
            points_rect = points_text.get_rect(center=(self.screen_size[0] // 2, self.screen_size[1] // 2 + 20))
            self.screen.blit(points_text, points_rect)
        
        # Render quit button
        button_rect = pygame.Rect(0, 0, 200, 50)
        button_rect.center = (self.screen_size[0] // 2, self.screen_size[1] // 2 + 100)
        pygame.draw.rect(self.screen, (100, 100, 100), button_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), button_rect, 2)
        
        quit_text = self.button_font.render("Quit Game", True, (255, 255, 255))
        quit_rect = quit_text.get_rect(center=button_rect.center)
        self.screen.blit(quit_text, quit_rect)
        
        return button_rect  # Return the rect for click detection
        
    def handle_input(self, event):
        """Handle input events"""
        if self.game_state.game_over:
            # Only handle quit button clicks when game is over
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
                mouse_pos = pygame.mouse.get_pos()
                quit_button = self.render_victory_screen()  # Get the button rect
                if quit_button.collidepoint(mouse_pos):
                    self.running = False
            return
            
        # Handle regular game input when game is not over
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self.world.handle_click(event.pos, self.game_state)
            elif event.button == 3:  # Right click
                self.world.handle_right_click(event.pos, self.game_state)
                
    def render(self):
        """Render the game state"""
        self.screen.fill((0, 0, 0))  # Clear screen
        
        # Render world and UI
        self.world.render(self.screen, self.game_state)
        self.ui.render(self.screen, self.game_state, self.world)
        
        # If game is over, render victory screen
        if self.game_state.game_over:
            self.render_victory_screen()
        
        pygame.display.flip() 