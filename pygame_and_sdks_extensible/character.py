import pygame

class Player(pygame.sprite.Sprite):
    """Represents the player character in the game."""
    def __init__(self, position, blocks_player, group, screen, sword_attack, hide_sword):
        """
        Initializes the Player instance.

        Args:
            position (tuple): The initial (x, y) position of the player.
            blocks_player (pygame.sprite.Group): Group of objects that block movement.
            group (pygame.sprite.Group): The sprite group the player belongs to.
            screen (pygame.Surface): The game screen.
            sword_attack (function): The function that handles sword attacks.
            hide_sword (function): The function that hides the sword after an attack.
        """
        super().__init__(group)
        self.group = group
        self.screen = screen
        #self.image = pygame.Surface((16,16))
        #self.rect = self.image.get_rect(topleft = position)
        #self.image.fill('blue')

        self.image = pygame.image.load('images/player/npc.png').convert_alpha()
        self.rect = self.image.get_rect(topleft = position)

        
        self.player_move = pygame.math.Vector2()
        self.facing = 'up'
        self.speed = 3
        self.blocks_player = blocks_player

        self.current_health = 1000
        self.max_health = 1000
        self.health_bar_length = 200
        self.health_ratio = self.max_health/self.health_bar_length

        self.current_mana = 1000
        self.max_mana = 1000
        self.mana_bar_length = 200
        self.mana_ratio = self.max_mana/self.mana_bar_length
        self.attack = False
        self.sword_attack = sword_attack
        self.hide_sword = hide_sword

        self.is_dead = False

    def damage(self, number):
        """
        Reduces the player's health.

        Args:
            amount (int): The amount of damage to apply.
        """
        if self.current_health > 0:
            self.current_health -= number
        if self.current_health <=0:
            self.current_health = 0
            self.is_dead = True

    def get_health(self, number):
        """
        Restores the player's health.

        Args:
            amount (int): The amount of health to restore.
        """
        if self.current_health < self.max_health:
            self.current_health += number
        if self.current_health >= self.max_health:
            self.current_health = self.max_health

    def health_bar_logic(self):
        """Draws the player's health bar on the screen."""
        pygame.draw.rect(self.screen, (255,0,0),(10,10, self.current_health/self.health_ratio, 15))
        pygame.draw.rect(self.screen, (255,255,255), (10,10, self.health_bar_length, 15),2)

    def usage(self, number):
        """
        Reduces the player's mana.

        Args:
            amount (int): The amount of mana to consume.
        """
        if self.current_mana > 0:
            self.current_mana -= number
        if self.current_mana <=0:
            self.current_mana = 0

    def get_mana(self, number):
        """
        Restores the player's mana.

        Args:
            amount (int): The amount of mana to restore.
        """
        if self.current_mana < self.max_mana:
            self.current_mana += number
        if self.current_mana >= self.max_mana:
            self.current_mana = self.max_mana
    
    def mana_regeneration(self):
        """Passive mana regeneration over time."""
        if self.current_mana < self.max_mana:
            self.current_mana += 50
        if self.current_mana >= self.max_mana:
            self.current_mana = self.max_mana

    def mana_bar_logic(self):
        """Draws the player's mana bar on the screen."""
        pygame.draw.rect(self.screen, (0,0,255),(10,30, self.current_mana/self.mana_ratio, 15))
        pygame.draw.rect(self.screen, (255,255,255), (10,30, self.mana_bar_length, 15),2)

    def player_input(self):
        """Handles player input for movement and attacks."""
        keys = pygame.key.get_pressed()

        if keys[pygame.K_s]:
            self.player_move.y = 1
            self.facing = 'down'
        elif keys[pygame.K_w]:
            self.player_move.y = -1
            self.facing = 'up'
        else:
            self.player_move.y = 0

        if keys[pygame.K_d]:
            self.player_move.x = 1
            self.facing = 'right'
        elif keys[pygame.K_a]:
            self.player_move.x = -1
            self.facing = 'left'
        else:
            self.player_move.x = 0

        if keys[pygame.K_SPACE]:
            if not self.attack:
                self.attack = True
                self.sword_attack()
        else:
            if self.attack:
                self.attack = False
                self.hide_sword()
            

        
    def moving(self):
        """Handles player movement and collision detection."""
        self.rect.centerx += self.player_move.x * self.speed
        self.check_collisions(self.blocks_player, 'x')
        self.rect.centery += self.player_move.y * self.speed
        self.check_collisions(self.blocks_player, 'y')

    def check_collisions(self, blocks , dir):
        """
        Checks for collisions with objects.

        Args:
            blocks (pygame.sprite.Group): The group of objects to check collisions against.
            direction (str): The movement direction ('x' or 'y').
        """
        if dir == 'x':
            coll = pygame.sprite.spritecollide(self ,blocks,False)
            if coll:
                if self.player_move.x > 0:
                    self.rect.x = coll[0].rect.left - self.rect.width
                if self.player_move.x < 0:
                    self.rect.x = coll[0].rect.right

        if dir == 'y':
            coll = pygame.sprite.spritecollide(self ,blocks,False)
            if coll:
                if self.player_move.y > 0:
                    self.rect.y = coll[0].rect.top - self.rect.height
                if self.player_move.y < 0:
                    self.rect.y = coll[0].rect.bottom
    
    def update(self):
        """Updates the player's state."""
        self.player_input()
        self.moving()
        
        


class Sword(pygame.sprite.Sprite):
    """Represents the sword weapon used by the player."""
    def __init__(self, player, group):
        """
        Initializes the Sword instance.

        Args:
            player (Player): The player object that wields the sword.
            group (pygame.sprite.Group): The sprite group the sword belongs to.
        """
        super().__init__(group)
        self.player = player
        self.original_image = pygame.image.load('images/weapond/sword.png').convert_alpha()
        self.original_image = pygame.transform.scale(self.original_image, (30, 6))  # Ustawienie skali
        self.image = self.original_image.copy()

        self.update_position()

    def update_position(self):
        """Updates the sword's position and orientation based on the player's facing direction."""
        direction = self.player.facing
        self.image = self.original_image.copy()  # Resetowanie obrazu przed rotacją

        if direction == 'right':
            self.rect = self.image.get_rect(midleft=self.player.rect.midright)
        elif direction == 'left':
            self.image = pygame.transform.rotate(self.image, 180)
            self.rect = self.image.get_rect(midright=self.player.rect.midleft)
        elif direction == 'up':
            self.image = pygame.transform.rotate(self.image, 90)
            self.rect = self.image.get_rect(midbottom=self.player.rect.midtop)
        else:  
            self.image = pygame.transform.rotate(self.image, 270)
            self.rect = self.image.get_rect(midtop=self.player.rect.midbottom)

    def update(self):
        """Updates the sword's position to match the player's movement."""
        self.update_position()