import pygame
import sys
from settings import *

class GUI:
    """Handles the graphical user interface (GUI) for the game menu."""
    def __init__(self, screen, text_font):
        """Initializes the GUI with buttons and music.

        Args:
            screen (pygame.Surface): The surface to render the GUI on.
            text_font (pygame.font.Font): The font to render the button text.
        """
        self.music_choice = None
        self.screen = screen
        self.running = True
        self.text_font = text_font
        
        # Load background images for tiling
        self.bg_tile = pygame.image.load('images/tiles/tile045.png')
        self.bg_tile = pygame.transform.scale(self.bg_tile, (64, 64))
        
        # Create title text
        self.title_font = pygame.font.Font('font/Silkscreen-Regular.ttf', 60)
        self.title_text = self.title_font.render('Knight Days', True, (255, 215, 0))
        self.title_shadow = self.title_font.render('Knight Days', True, (139, 69, 19))
        self.title_rect = self.title_text.get_rect(center=(W // 2, 80))
        self.title_shadow_rect = self.title_shadow.get_rect(center=(W // 2 + 4, 84))
        
        # Button vertical positioning with more space
        button_y_start = 150  # Moved up from 170
        button_spacing = 65   # Slightly reduced spacing
        button_width = 300
        button_height = 60
        button_x = (W - button_width) // 2
        
        # Create buttons with new styling
        self.button1 = Button('Play', (button_x, button_y_start), button_width, button_height, self.screen, self.text_font)
        self.button2 = Button('Linear', (button_x, button_y_start + button_spacing), button_width, button_height, self.screen, self.text_font)
        self.button3 = Button('Adaptive', (button_x, button_y_start + button_spacing * 2), button_width, button_height, self.screen, self.text_font)
        self.button4 = Button('Generative', (button_x, button_y_start + button_spacing * 3), button_width, button_height, self.screen, self.text_font)
        self.button5 = Button('Quit', (button_x, button_y_start + button_spacing * 4), button_width, button_height, self.screen, self.text_font)

        self.buttons = [self.button2, self.button3, self.button4]

        self.music = pygame.mixer.Sound('linear/menu.mp3')
        self.music.set_volume(0.8)
        self.music.play(loops=-1)


    def main_menu(self):
        """Displays the main menu with all buttons.

        Calls the `all_in_one` method on each button to render them on the screen.
        """
        # Draw tiled background
        for y in range(0, H, 64):
            for x in range(0, W, 64):
                self.screen.blit(self.bg_tile, (x, y))
        
        # Add semi-transparent overlay for better text visibility
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Black with 50% transparency
        self.screen.blit(overlay, (0, 0))
        
        # Draw title with shadow effect
        self.screen.blit(self.title_shadow, self.title_shadow_rect)
        self.screen.blit(self.title_text, self.title_rect)
        
        # Draw buttons
        self.button1.all_in_one()
        self.button2.all_in_one()
        self.button3.all_in_one()
        self.button4.all_in_one()
        self.button5.all_in_one()

    def check_pressed_music(self):
        """Checks if a button is pressed and sets the pressed state.

        Loops through all buttons to check if the mouse cursor is over a button 
        and if the left mouse button is clicked. If a button is pressed, 
        it sets that button as pressed and releases the others.
        """
        for button in self.buttons:
            if button.button_rect.collidepoint(pygame.mouse.get_pos()):
                if pygame.mouse.get_pressed()[0]:
                    for btn in self.buttons:
                        if btn != button:
                            btn.set_pressed(False)
                    button.set_pressed(True)
                    pygame.time.wait(200)

    def run(self):
        """Runs the main menu loop.

        This loop keeps the menu running, listens for events like button presses,
        and updates the screen. It also handles quitting and selecting a game path.
        """
        while self.running == True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if self.button5.pressed:
                    sys.exit()
                if self.button1.pressed and any([self.button2.pressed,self.button3.pressed,self.button4.pressed]):
                    self.running = False
                    self.music.stop()
                    return [self.button2.pressed,self.button3.pressed,self.button4.pressed]

            self.main_menu()
            self.check_pressed_music()
            
            pygame.display.update()


class Button:
    """Represents a button that can be drawn on the screen and interacted with."""
    def __init__(self, text_input, pos, width, height, screen, text_font):
        """Initializes the button with its position, size, text, font, and screen.

        Args:
            text_input (str): The text to be displayed on the button.
            pos (tuple[int, int]): The position of the button on the screen (top-left corner).
            width (int): The width of the button.
            height (int): The height of the button.
            screen (pygame.Surface): The surface where the button will be drawn.
            text_font (pygame.font.Font): The font used to render the text on the button.
        """
        self.screen = screen
        self.button_rect = pygame.Rect(pos, (width, height))
        self.border_radius = 15
        self.text_input = text_input
        self.text_font = text_font
        self.pressed = False
        self.hovering = False
        
        # Button colors
        self.bg_color = (30, 30, 60)  # Dark blue
        self.border_color = (100, 100, 200)  # Light blue
        self.hover_color = (40, 40, 80)  # Slightly lighter than bg_color
        self.pressed_color = (60, 20, 60)  # Purple when pressed
        
        self.update_text_color()

    def update_text_color(self):
        """Updates the text color based on the button's pressed state."""
        if self.pressed:
            self.text = self.text_font.render(self.text_input, True, (255, 128, 0))  # Orange
        else:
            self.text = self.text_font.render(self.text_input, True, (220, 220, 255))  # Light blue/white

        self.text_rect = self.text.get_rect(center=self.button_rect.center)

    def draw(self):
        """Draws the button on the screen with a fancier style."""
        # Check if mouse is hovering over button
        mouse_pos = pygame.mouse.get_pos()
        self.hovering = self.button_rect.collidepoint(mouse_pos)
        
        # Choose the right color based on state
        if self.pressed:
            button_color = self.pressed_color
        elif self.hovering:
            button_color = self.hover_color
        else:
            button_color = self.bg_color
        
        # Draw the button with rounded corners
        pygame.draw.rect(self.screen, button_color, self.button_rect, border_radius=self.border_radius)
        
        # Draw the border
        pygame.draw.rect(self.screen, self.border_color, self.button_rect, width=2, border_radius=self.border_radius)
        
        # Add gradient effect (lighter at the top, darker at the bottom)
        gradient = pygame.Surface((self.button_rect.width - 4, self.button_rect.height//2 - 2), pygame.SRCALPHA)
        gradient.fill((255, 255, 255, 30))  # Very light transparent white
        self.screen.blit(gradient, (self.button_rect.x + 2, self.button_rect.y + 2))
        
        # Draw text
        self.screen.blit(self.text, self.text_rect)

    def is_pressed(self):
        """Detects if the button is clicked by the mouse.

        Checks if the mouse cursor is over the button and if the left mouse 
        button is pressed. If so, toggles the button's pressed state.
        """
        mouse_pos = pygame.mouse.get_pos()
        if self.button_rect.collidepoint(mouse_pos):
            if pygame.mouse.get_pressed()[0]:
                self.pressed = not self.pressed
                self.update_text_color()
                pygame.time.wait(200)

    def set_pressed(self, state):
        """Sets the pressed state of the button.

        Args:
            state (bool): The new pressed state of the button.
        """
        self.pressed = state
        self.update_text_color()

    def all_in_one(self):
        """Handles the entire button process: drawing and checking if it is pressed."""
        self.draw()
        self.is_pressed()