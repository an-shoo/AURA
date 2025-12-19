import pygame
import pygame.math
import math

class Block(pygame.sprite.Sprite):
    """Represents a solid block in the game."""
    def __init__(self, image_value, position,group):
        """Initializes the block.

        Args:
            image_value (str): The file path of the block's image.
            position (tuple[int, int]): The top-left position (x, y) of the block.
            group (pygame.sprite.Group): The sprite group to which the block is added.
        """
        super().__init__(group)
        self.image = pygame.image.load(image_value).convert()
        self.rect = self.image.get_rect(topleft = position)
        

class EndLevel(pygame.sprite.Sprite):
    """Represents the endpoint of a level."""
    def __init__(self, position, group):
        """Initializes the EndLevel object.

        Args:
            position (tuple[int, int]): The top-left position (x, y) of the endpoint.
            group (pygame.sprite.Group): The sprite group to which the endpoint is added.
        """
        super().__init__(group)
        self.image = pygame.image.load('images/tiles/tile030.png').convert()
        self.rect = self.image.get_rect(topleft = position)

class Key(pygame.sprite.Sprite):
    """Represents a collectible key in the game."""
    def __init__(self, position, group):
        """Initializes the Key object.

        Args:
            position (tuple[int, int]): The top-left position (x, y) of the key.
            group (pygame.sprite.Group): The sprite group to which the key is added.
        """
        super().__init__(group)
        self.image = pygame.image.load('images/tiles/tile092.png').convert_alpha()
        self.rect = self.image.get_rect(topleft = position)


class Spell(pygame.sprite.Sprite):
    """Represents a spell that moves in a specified direction.

    The spell moves at a fixed speed and disappears upon collision

    """
    def __init__(self, position,  direction, group, blocks):
        """Initializes the spell.

        Args:
            position (tuple[int, int]): The initial position of the spell (x, y).
            direction (pygame.Vector2): The direction in which the spell moves.
            group (pygame.sprite.Group): The group to which the spell is added.
            blocks (pygame.sprite.Group): The group of objects the spell can collide with.
        """
        super().__init__(group)
        self.image = pygame.image.load('images/spell/FB001.png').convert_alpha()
        self.image = pygame.transform.scale_by(self.image,(0.5))
        self.blocks = blocks
        self.speed = 8
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 1000
        self.direction = direction
        angle = math.degrees(math.atan2(-self.direction.y, self.direction.x))
        self.image = pygame.transform.rotate(self.image, angle)
        self.rect = self.image.get_rect(center=position)

    def spell_wall_collisions(self):
        """Checks if the spell collides with walls.

        If the spell hits an object from the `blocks` group, it is removed.
        """
        coll = pygame.sprite.spritecollide(self, self.blocks, False)
        if coll:
            self.kill()

    def move(self):
        """Moves the spell in the direction of `self.direction`."""
        self.rect.center += self.direction *self.speed
        
    def update(self):
        """Updates the spell's position and checks for collisions."""
        self.move()
        self.spell_wall_collisions()

class Potion(pygame.sprite.Sprite):
    """Represents a potion that the player can collect."""
    def __init__(self, position, image_value, value, type, group):
        """Initializes the Potion object.

        Args:
            position (tuple[int, int]): The top-left position (x, y) of the potion.
            image_value (str): The file path to the potion's image.
            value (int): The effect strength of the potion (e.g., amount of HP restored).
            type (str): The type of potion (e.g., 'health', 'mana').
            group (pygame.sprite.Group): The sprite group to which the potion is added.
        """
        super().__init__(group) 
        self.image = pygame.image.load(image_value).convert_alpha()
        self.rect = self.image.get_rect(topleft = position)
        self.value = value
        self.type = type