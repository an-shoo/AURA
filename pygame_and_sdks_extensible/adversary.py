import pygame
from terrain import *
from settings import *

class BaseEnemy(pygame.sprite.Sprite):
    """Represents an enemy character that can move towards the player and detect collisions."""
    def __init__(self, position, group, player, block_group):
        """Initializes the enemy with position, sprite group, player target, and block group.

        Args:
            position (tuple[int, int]): The initial position of the enemy.
            group (pygame.sprite.Group): The group the enemy belongs to.
            player (pygame.sprite.Sprite): The player that the enemy will target.
            block_group (pygame.sprite.Group): The group of blocks the enemy can collide with.
        """
        super().__init__(group)
        #self.image = pygame.Surface((16,16))
        #self.rect = self.image.get_rect(topleft = position)
        #self.image.fill('green')
        self.player = player
        self.image = pygame.image.load('images/enemy/monster.png').convert_alpha()
        self.rect = self.image.get_rect(topleft = position)
        self.enemy_pos = pygame.Vector2(self.rect.center)
        self.enemy_saw_player = False

        self.direction = pygame.Vector2()
        self.block_group = block_group
        self.speed = 1

        self.attack_damage = 200
        self.health = 200


    def movement(self):
        """Moves the enemy towards the player if they are within a certain range."""
        distance = ((self.player.rect.centerx - self.rect.centerx)**2 + (self.player.rect.centery - self.rect.centery)**2)**(1/2)
        if distance < 300 or self.enemy_saw_player == True:
            self.enemy_saw_player = True
            player_pos = pygame.Vector2(self.player.rect.center)
            enemy_pos = pygame.Vector2(self.rect.center)

            self.direction = (player_pos - enemy_pos).normalize()

            self.rect.x += self.direction.x * self.speed
            self.check_collisions(self.block_group, 'x')
            self.rect.y += self.direction.y * self.speed
            self.check_collisions(self.block_group, 'y')
    
    def check_collisions(self, blocks , dir):
        """Checks for collisions between the enemy and blocks along a given axis.

        Args:
            blocks (pygame.sprite.Group): The group of blocks to check collisions with.
            dir (str): The direction to check for collisions ('x' or 'y').
        """
        if dir == 'x':
            coll = pygame.sprite.spritecollide(self ,blocks,False)
            if coll:
                if self.direction.x > 0:
                    self.rect.x = coll[0].rect.left - self.rect.width
                if self.direction.x < 0:
                    self.rect.x = coll[0].rect.right

        if dir == 'y':
            coll = pygame.sprite.spritecollide(self ,blocks,False)
            if coll:
                if self.direction.y > 0:
                    self.rect.y = coll[0].rect.top - self.rect.height
                if self.direction.y < 0:
                    self.rect.y = coll[0].rect.bottom

    def death(self):
        """Checks if the enemy's health is zero or below, and kills the enemy if true."""
        if self.health <= 0:
            self.kill()

    def update(self):
        """Updates the enemy's movement and checks for death."""
        self.movement()
        self.death()


class TowerEnemy(pygame.sprite.Sprite):
    """Represents a enemy that can cast spells towards the player and stands in one position."""
    def __init__(self, position, group, player, blocks, e_spell_group):
        """Initializes the tower enemy with position, sprite group, player target, blocks, and spell group.

        Args:
            position (tuple[int, int]): The initial position of the enemy.
            group (pygame.sprite.Group): The group the enemy belongs to.
            player (pygame.sprite.Sprite): The player that the enemy will target.
            blocks (pygame.sprite.Group): The group of blocks the enemy can collide with.
            e_spell_group (pygame.sprite.Group): The group for managing spells cast by the enemy.
        """
        super().__init__(group)
        self.group = group
        #self.image = pygame.Surface((16,16))
        #self.rect = self.image.get_rect(topleft = position)
        #self.image.fill('green')
        self.image = pygame.image.load('images/enemy/wizzard.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (34,30))
        self.rect = self.image.get_rect(topleft = position)
        self.enemy_pos = pygame.Vector2(self.rect.center)
        self.attack_damage = 500
        self.player = player
        self.blocks = blocks
        self.e_spell_group = e_spell_group
        self.attack_cooldown = 3000  # Czas między atakami w milisekundach
        self.last_attack_time = pygame.time.get_ticks()
        self.health = 100


    def get_spell_direction(self):
        """Calculates the direction in which the enemy will cast its spell."""
        player_pos = pygame.Vector2(self.player.rect.center)    
        self.spell_direction = (player_pos - self.enemy_pos).normalize()

    def cast_spell(self):
        """Casts a spell towards the player if the attack cooldown has elapsed."""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_attack_time > self.attack_cooldown:
            spell = Spell(self.rect.center, self.spell_direction, self.group, self.blocks)
            self.e_spell_group.add(spell)
            self.last_attack_time = current_time

    def death(self):
        """Checks if the enemy's health is zero or below, and kills the enemy if true."""
        if self.health <= 0:
            self.kill()

    def update(self):
        """Updates the enemy's spell direction, casts a spell, and checks for death."""
        self.get_spell_direction()
        self.cast_spell()
        self.death()

class Boss(pygame.sprite.Sprite):
    """Represents a boss enemy that can move, cast spells, and has health. 
    The boss's behavior changes based on its health."""
    def __init__(self, position, group, player, blocks, e_spell_group):
        """Initializes the boss with position, sprite group, player target, blocks, and spell group.

        Args:
            position (tuple[int, int]): The initial position of the boss.
            group (pygame.sprite.Group): The group the boss belongs to.
            player (pygame.sprite.Sprite): The player the boss targets.
            blocks (pygame.sprite.Group): The group of blocks the boss can collide with.
            e_spell_group (pygame.sprite.Group): The group that stores the spells cast by the boss.
        """
        super().__init__(group)
        #self.image = pygame.Surface((16,16))
        #self.rect = self.image.get_rect(topleft = position)
        #self.image.fill('blue')
        self.player = player
        self.image = pygame.image.load('images/enemy/imp.png').convert_alpha()
        self.rect = self.image.get_rect(topleft = position)
        self.enemy_pos = pygame.Vector2(self.rect.center)
        self.enemy_saw_player = False
        self.health = 900
        self.direction = pygame.Vector2()
        self.blocks = blocks
        self.speed = 1
        self.group = group
        self.e_spell_group = e_spell_group

        self.attack_cooldown = 3000  # Czas między atakami w milisekundach
        self.last_attack_time = pygame.time.get_ticks()

        self.attack_damage = 1000

    def movement(self):
        """Moves the boss towards the player if the player is within a certain range."""
        distance = ((self.player.rect.centerx - self.rect.centerx)**2 + (self.player.rect.centery - self.rect.centery)**2)**(1/2)
        if distance < 300 or self.enemy_saw_player == True:
            self.enemy_saw_player = True
            player_pos = pygame.Vector2(self.player.rect.center)
            enemy_pos = pygame.Vector2(self.rect.center)

            self.direction = (player_pos - enemy_pos).normalize()

            self.rect.x += self.direction.x * self.speed
            self.check_collisions(self.blocks, 'x')
            self.rect.y += self.direction.y * self.speed
            self.check_collisions(self.blocks, 'y')
    
    def check_collisions(self, blocks , dir):
        """Checks for collisions between the enemy and blocks along a given axis.

        Args:
            blocks (pygame.sprite.Group): The group of blocks to check collisions with.
            dir (str): The direction to check for collisions ('x' or 'y').
        """
        if dir == 'x':
            coll = pygame.sprite.spritecollide(self ,blocks,False)
            if coll:
                if self.direction.x > 0:
                    self.rect.x = coll[0].rect.left - self.rect.width
                if self.direction.x < 0:
                    self.rect.x = coll[0].rect.right

        if dir == 'y':
            coll = pygame.sprite.spritecollide(self ,blocks,False)
            if coll:
                if self.direction.y > 0:
                    self.rect.y = coll[0].rect.top - self.rect.height
                if self.direction.y < 0:
                    self.rect.y = coll[0].rect.bottom

    def cast_spell(self, spell_tab):
        """Casts a spell towards the player if the attack cooldown has elapsed."""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_attack_time > self.attack_cooldown:
            for index in range(len(spell_tab)):
                spell = Spell(self.rect.center, pygame.Vector2(spell_tab[index][0], spell_tab[index][1]), self.group, self.blocks)
                self.e_spell_group.add(spell)
            self.last_attack_time = current_time
    
    def death(self):
        """Checks if the enemy's health is zero or below, and kills the enemy if true."""
        if self.health <= 0:
            self.kill()

    def update(self):
        """Updates the boss's movement, checks for death, and casts spells."""
        self.movement()
        self.death()

        if self.health > 600:
            self.cast_spell([[1,0], [-1,0],[0,1],[0,-1]])
        elif self.health > 300 and self.health <= 600:
            self.cast_spell([[-0.75 , 0.75], [0.75 , -0.75],[-0.75, -0.75],[0.75 , 0.75]])
        elif self.health <= 300:
            self.cast_spell([[-0.75 , 0.75], [0.75 , -0.75],[-0.75, -0.75],[0.75 , 0.75], [1,0], [-1,0],[0,1],[0,-1]])