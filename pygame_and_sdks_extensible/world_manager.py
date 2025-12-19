import pygame
from settings import *
from character import *
from terrain import * 
from adversary import *
import numpy as np



class LevelBase():
    """
    This class handles the setup and behavior of a single level in the game.
    It manages the creation of blocks, enemies, items, music, and player actions.
    """
    def __init__(self, screen, level_date_table, important_table):
        """
        Initializes the level with a given screen, level data table, and important settings.

        Args:
            screen (pygame.Surface): The display screen for rendering the game.
            level_date_table (list): The table containing the level layout data.
            important_table (list): A table containing flags for special music type condition.
        """
        self.screen = screen
        self.level_number = 0
        self.level_date = level_date_table[self.level_number]
        self.number_of_level = len(level_date_tabel)
        
        # Add ESC key hint text
        self.esc_hint_font = pygame.font.Font('font/Silkscreen-Regular.ttf', 16)
        self.esc_hint_text = self.esc_hint_font.render('Press ESC to return to main menu', True, (180, 180, 180))
        self.esc_hint_rect = self.esc_hint_text.get_rect(bottomright=(W - 10, H - 10))
        self.block_group = pygame.sprite.Group()
        self.sprite_group = Allsprites(self.level_number)
        self.enemy_group = pygame.sprite.Group()
        self.spell_group = pygame.sprite.Group()
        self.enemy_spell_group = pygame.sprite.Group()
        self.potion_group = pygame.sprite.Group()
        self.key_group = pygame.sprite.GroupSingle()

        self.player_direction = pygame.Vector2(1,0)

        self.can_shoot = True
        self.sword = None
        self.attack_cooldown = 500  # Czas między atakami w milisekundach
        self.last_attack_time = pygame.time.get_ticks()

        self.game_state = 'exploration'
        self.end_game = False
        self.important_table = important_table

        self.is_calm = True

        self.have_key = False

        self.is_fading = False
        self.fade_start_time = None
        self.fade_duration = 500

        self.next_time = pygame.time.get_ticks() + 650

        self.setup_level(self.level_date)
        
    def setup_level(self, level_date):
        """
        Sets up the level by processing the level data and creating appropriate game elements 
        such as blocks, enemies, items, music, and special objects.

        Args:
            level_date (list): The layout of the level containing the block and item definitions.
        """

        if self.important_table[0] == True:
            self.linear_music()
        elif self.important_table[1] == True:
            self.adaptive_music()
        elif self.important_table[2] == True:
            self.generative_music()

        self.player_group = pygame.sprite.GroupSingle()
        self.end_group = pygame.sprite.GroupSingle()
        for row_index, row in enumerate(level_date):
            for cell_index, cell in enumerate(row):
                x = cell_index * BLOCK_SIZE
                y = row_index * BLOCK_SIZE
                
                #walls blocks

                if cell == 2:
                    block = Block( 'images/tiles/tile002.png', (x,y),[self.sprite_group])
                    self.block_group.add(block)
                if cell == 3:
                    block = Block( 'images/tiles/tile003.png', (x,y),[self.sprite_group])
                    self.block_group.add(block)
                if cell == 4:
                    block = Block( 'images/tiles/tile004.png', (x,y),[self.sprite_group])
                    self.block_group.add(block)  
                if cell == 5:
                    block = Block( 'images/tiles/tile005.png', (x,y),[self.sprite_group])
                    self.block_group.add(block)
                if cell == 8:
                    block = Block( 'images/tiles/tile008.png', (x,y),[self.sprite_group])
                    self.block_group.add(block)
                if cell == 12:
                    block = Block( 'images/tiles/tile012.png', (x,y),[self.sprite_group])
                    self.block_group.add(block)
                if cell == 13:
                    block = Block( 'images/tiles/tile013.png', (x,y),[self.sprite_group])
                    self.block_group.add(block)
                if cell == 14:
                    block = Block( 'images/tiles/tile014.png', (x,y),[self.sprite_group])
                    self.block_group.add(block)
                if cell == 22:
                    block = Block( 'images/tiles/tile022.png', (x,y),[self.sprite_group])
                    self.block_group.add(block)
                if cell == 23:
                    block = Block( 'images/tiles/tile023.png', (x,y),[self.sprite_group])
                    self.block_group.add(block)
                if cell == 24:
                    block = Block( 'images/tiles/tile024.png', (x,y),[self.sprite_group])
                    self.block_group.add(block)  
                if cell == 32:
                    block = Block( 'images/tiles/tile032.png', (x,y),[self.sprite_group])
                    self.block_group.add(block)
                if cell == 33:
                    block = Block( 'images/tiles/tile033.png', (x,y),[self.sprite_group])
                    self.block_group.add(block)
                if cell == 34:
                    block = Block( 'images/tiles/tile034.png', (x,y),[self.sprite_group])
                    self.block_group.add(block)
                if cell == 35:
                    block = Block( 'images/tiles/tile035.png', (x,y),[self.sprite_group])
                    self.block_group.add(block)
                if cell == 38:
                    block = Block( 'images/tiles/tile038.png', (x,y),[self.sprite_group])
                    self.block_group.add(block)  
                if cell == 45:
                    block = Block( 'images/tiles/tile045.png', (x,y),[self.sprite_group])
                    self.block_group.add(block)  
                if cell == 55:
                    block = Block( 'images/tiles/tile055.png', (x,y),[self.sprite_group])
                    self.block_group.add(block)
                if cell == 65:
                    block = Block( 'images/tiles/tile065.png', (x,y),[self.sprite_group])
                    self.block_group.add(block)
                if cell == 66:
                    block = Block( 'images/tiles/tile066.png', (x,y),[self.sprite_group])
                    self.block_group.add(block)

                #end_level

                if cell == 30:
                    self.end_level = EndLevel((x,y),[self.sprite_group])
                    self.end_group.add(self.end_level)

                #key
                if cell == "k":
                    self.key = Key((x,y),[self.sprite_group])
                    self.key_group.add(self.key)

                #potions

                if cell == "bh":
                    potion = Potion((x,y), 'images/potions/big_health.png', 400, 'health',[self.sprite_group])
                    self.potion_group.add(potion)
                if cell == "sh":
                    potion = Potion((x,y), 'images/potions/small_health.png', 100, 'health',[self.sprite_group])
                    self.potion_group.add(potion)
                if cell == "bm":
                    potion = Potion((x,y), 'images/potions/big_mana.png', 400, 'mana',[self.sprite_group])
                    self.potion_group.add(potion)
                if cell == "sm":
                    potion = Potion((x,y), 'images/potions/small_mana.png', 100, 'mana',[self.sprite_group])
                    self.potion_group.add(potion)

                #player

                if cell == "p":
                    self.player = Player((x,y), self.block_group,[self.sprite_group], self.screen, self.sword_attack, self.hide_sword)
                    self.player_group.add(self.player)

                #enemies

                if cell == "e":
                    enemy = BaseEnemy((x,y),[self.sprite_group], self.player, self.block_group)
                    self.enemy_group.add(enemy)
                if cell == "t":
                    enemy = TowerEnemy((x,y), [self.sprite_group] ,self.player, self.block_group, self.enemy_spell_group)
                    self.enemy_group.add(enemy)
                if cell == "b":
                    enemy = Boss((x,y),[self.sprite_group], self.player, self.block_group, self.enemy_spell_group)
                    self.enemy_group.add(enemy)


        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.block_group)
        self.all_sprites.add(self.potion_group)
        self.all_sprites.add(self.end_group)

    def linear_music(self):
        """Plays the linear background music."""
        self.music = pygame.mixer.Sound('linear/super_mario.mp3')
        self.music.set_volume(0.8)
        self.music.play(loops=-1)

    def adaptive_music(self):
        """Plays the adaptive background music based on the current game state (e.g., exploration, battle)."""
        sound_paths = {
            "exploration": "adaptive/Exploration.mp3",
            "close_to_enemy": "adaptive/Enemy.mp3",
            "battle": "adaptive/Battle.mp3"
        }
        
        self.sounds = {state: pygame.mixer.Sound(path) for state, path in sound_paths.items()}
        self.current_state = self.game_state
        self.music = self.sounds[self.game_state]
        self.music.play(loops=-1)
        self.music.set_volume(0.8)

    def generative_music(self):
        """
        Plays the generative background music based on the current game state (e.g., exploration, battle).
        Function contain implementation of Markov chains based on chord progression
        """
        self.calm_chords_mp3 = {
            'C Major': 'test2/C Major.mp3',
            'Dm7': 'test2/Dm7.mp3',
            'G7': 'test2/G7.mp3',
            'Cmaj7': 'test2/Cmaj7.mp3',
            'Am': 'test2/Am.mp3',
            'Dm': 'test2/Dm.mp3',
            'G Major': 'test2/G Major.mp3',
            'F Major': 'test2/F Major.mp3'
        }

        self.high_tension_chords_mp3 = {
            'G Major': 'test2/G Major.mp3',
            'C Major': 'test2/C Major.mp3',
            'Am': 'test2/Am.mp3',
            'F Major': 'test2/F Major.mp3',
            'E Major': 'test2/E Major.mp3',
            'Dm7': 'test2/Dm7.mp3',
            'G7': 'test2/G7.mp3',
            'Cmaj7': 'test2/Cmaj7.mp3',
            'A7': 'test2/A7.mp3'
        }

        self.calm_transition_matrix = np.array([
            [0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.5, 0.0],  # C Major
            [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # Dm7
            [0.5, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0],  # G7
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # Cmaj7
            [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],  # Am
            [0.0, 0.0, 0.5, 0.0, 0.5, 0.0, 0.0, 0.0],  # Dm
            [0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5],  # G Major
            [0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.5, 0.0],  # F Major
        ])

        self.tension_transition_matrix = np.array([
            [0.0, 0.5, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0],  # G Major
            [0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.5, 0.0, 0.0],  # C Major
            [0.25, 0.0, 0.0, 0.5, 0.0, 0.25, 0.0, 0.0, 0.0],# Am
            [0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.5, 0.0, 0.0],  # F Major
            [0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.5, 0.0],  # E Major
            [0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0],  # Dm7
            [0.5, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0],  # G7
            [0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0],  # Cmaj7
            [0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0],  # A7
        ])


        ################################### SECON VERISON CHODS PROGRESSIOM

        self.LOW_calm_chords_mp3 = {
            'C': 'test3/C.mp3',
            'F': 'test3/F.mp3',
            'G': 'test3/G.mp3',
            'Am': 'test3/Am.mp3',
            'Dm': 'test3/Dm.mp3',
            'Em': 'test3/Em.mp3',
            'A': 'test3/A.mp3',
        }

        self.TURBO_high_tension_chords_mp3 = {
            'Am': 'test3/Am.mp3',
            'G': 'test3/G.mp3',
            'F': 'test3/F.mp3',
            'C': 'test3/C.mp3',
            'E': 'test3/E.mp3',
            'Bb': 'test3/Bb.mp3',
            'Ab': 'test3/Ab.mp3',
            'Cm': 'test3/Cm.mp3',
            'Dm': 'test3/Dm.mp3'
        }

        self.LOW_calm_transition_matrix = np.array([
            [0.0, 0.3, 0.3, 0.1, 0.1, 0.1, 0.1],  # C
            [0.5, 0.0, 0.4, 0.1, 0.0, 0.0, 0.0],  # F
            [0.3, 0.0, 0.0, 0.2, 0.2, 0.0, 0.3],  # G
            [0.3, 0.1, 0.3, 0.0, 0.3, 0.0, 0.0],  # Am
            [0.3, 0.0, 0.7, 0.0, 0.0, 0.0, 0.0],  # Dm
            [0.3, 0.3, 0.4, 0.0, 0.0, 0.0, 0.0],  # Em
            [0.3, 0.3, 0.4, 0.0, 0.0, 0.0, 0.0]   # A
        ])

        self.TURBO_tension_transition_matrix = np.array([
            [0.1, 0.3, 0.2, 0.1, 0.1, 0.0, 0.0, 0.0, 0.2],  # Am
            [0.2, 0.1, 0.2, 0.3, 0.0, 0.0, 0.0, 0.1, 0.1],  # G
            [0.2, 0.2, 0.0, 0.3, 0.0, 0.1, 0.0, 0.0, 0.2],  # F
            [0.0, 0.3, 0.3, 0.1, 0.0, 0.2, 0.0, 0.1, 0.0],  # C
            [0.5, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0],  # E
            [0.0, 0.0, 0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0],  # Bb
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.5, 0.0],  # Ab
            [0.5, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0],  # Cm
            [0.0, 0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]   # Dm
        ])

        self.LOW_calm_chords = ['C', 'F', 'G', 'Am', 'Dm', 'Em', 'A']
        self.TURBO_tension_chords = ['Am', 'G', 'F', 'C', 'E', 'Bb', 'Ab', 'Cm', 'Dm']
        #################################################################################


        self.calm_chords = ['C Major', 'Dm7', 'G7', 'Cmaj7', 'Am', 'Dm', 'G Major', 'F Major']
        self.tension_chords = ['G Major', 'C Major', 'Am', 'F Major', 'E Major', 'Dm7', 'G7', 'Cmaj7', 'A7']

        self.channel1 = pygame.mixer.Channel(0)
        self.channel2 = pygame.mixer.Channel(1)

        self.current_chord_index = 0
        self.current_channel = self.channel1
        
    
    def get_next_chord(self, current_index, transition_matrix):
        """
        Retrieves the next chord index based on the current index and transition matrix probabilities.
        Adds a small uniform epsilon to reduce lock-in to a few states.
        """
        probabilities = transition_matrix[current_index].astype(float)
        # Add epsilon to smooth extremes and re-normalize
        eps = 0.03
        probabilities = probabilities + eps
        probabilities = probabilities / probabilities.sum()
        next_index = np.random.choice(len(probabilities), p=probabilities)
        return next_index

    def play_chord(self, channel, chord_mp3):
        """
        Plays a chord sound through the specified channel.
        
        Args:
            channel (pygame.mixer.Channel): The channel through which to play the sound.
            chord_mp3 (str): The path to the MP3 file of the chord sound.
        """
        channel.play(pygame.mixer.Sound(chord_mp3))
        # Add volume and pan variation per chord to reduce perceived repetition
        base = 0.65 + np.random.rand() * 0.35  # 0.65-1.0
        pan = (np.random.rand() - 0.5) * 0.5   # -0.25 to 0.25
        left = max(0.0, min(1.0, base * (1 - pan)))
        right = max(0.0, min(1.0, base * (1 + pan)))
        channel.set_volume(left, right)

    def music_generator(self):
        """
        Generates and plays music based on the current game state. Transitions between calm and tension-based chords 
        depending on the player's situation in the game (battle, exploration, etc.).
        """
        current_time = pygame.time.get_ticks()
        #print(self.next_time, current_time)
        if current_time >= self.next_time:
            # Choose which bank to use with some cross-over to add variety
            use_low_bank = False
            if self.game_state == 'battle':
                if self.is_calm:
                    self.is_calm = False
                    # Do not hard-reset; just ensure index within bounds
                    self.current_chord_index %= len(self.TURBO_tension_chords)
                # 20% chance to use alternate tension bank (TURBO) vs standard
                use_low_bank = np.random.rand() < 0.2
                if use_low_bank:
                    idx = self.current_chord_index % len(self.TURBO_tension_chords)
                    next_chord_index = self.get_next_chord(idx, self.TURBO_tension_transition_matrix)
                    self.play_chord(self.current_channel, self.TURBO_high_tension_chords_mp3[self.TURBO_tension_chords[next_chord_index]])
                    bank_len = len(self.TURBO_tension_chords)
                else:
                    idx = self.current_chord_index % len(self.tension_chords)
                    next_chord_index = self.get_next_chord(idx, self.tension_transition_matrix)
                    self.play_chord(self.current_channel, self.high_tension_chords_mp3[self.tension_chords[next_chord_index]])
                    bank_len = len(self.tension_chords)
            elif self.game_state == 'close_to_enemy':
                if self.is_calm:
                    self.is_calm = False
                    self.current_chord_index %= len(self.tension_chords)
                # 15% chance to borrow from TURBO bank
                use_low_bank = np.random.rand() < 0.15
                if use_low_bank:
                    idx = self.current_chord_index % len(self.TURBO_tension_chords)
                    next_chord_index = self.get_next_chord(idx, self.TURBO_tension_transition_matrix)
                    self.play_chord(self.current_channel, self.TURBO_high_tension_chords_mp3[self.TURBO_tension_chords[next_chord_index]])
                    bank_len = len(self.TURBO_tension_chords)
                else:
                    idx = self.current_chord_index % len(self.tension_chords)
                    next_chord_index = self.get_next_chord(idx, self.tension_transition_matrix)
                    self.play_chord(self.current_channel, self.high_tension_chords_mp3[self.tension_chords[next_chord_index]])
                    bank_len = len(self.tension_chords)
            else:
                if not self.is_calm:
                    self.is_calm = True
                    self.current_chord_index %= len(self.calm_chords)
                # 20% chance to use LOW calm bank
                use_low_bank = np.random.rand() < 0.2
                if use_low_bank:
                    idx = self.current_chord_index % len(self.LOW_calm_chords)
                    next_chord_index = self.get_next_chord(idx, self.LOW_calm_transition_matrix)
                    self.play_chord(self.current_channel, self.LOW_calm_chords_mp3[self.LOW_calm_chords[next_chord_index]])
                    bank_len = len(self.LOW_calm_chords)
                else:
                    idx = self.current_chord_index % len(self.calm_chords)
                    next_chord_index = self.get_next_chord(idx, self.calm_transition_matrix)
                    self.play_chord(self.current_channel, self.calm_chords_mp3[self.calm_chords[next_chord_index]])
                    bank_len = len(self.calm_chords)
            
            self.current_chord_index = next_chord_index

                # Switch channels
            self.current_channel = self.channel2 if self.current_channel == self.channel1 else self.channel1

            # Slight timing jitter to reduce rigid periodicity
            jitter = np.random.randint(-120, 120)
            if self.game_state == 'battle' and self.player.current_health <= 400:
                base = 300
            elif self.game_state == 'close_to_enemy':   
                base = 450
            elif self.game_state == 'battle' :  
                base = 400
            else:
                base = 500
            self.next_time = max(200, current_time + base + jitter)

            #print(self.game_state)
            

    def check_state(self):
        """
        Checks if the game state has changed and updates the background music accordingly. 
        Fades out the current music and fades in the new music for the new state.
        """
        if self.current_state != self.game_state:
            if self.music:
                self.music.fadeout(self.fade_duration)
            
            self.music = self.sounds[self.game_state]
            self.music.play(loops=-1)
            self.music.set_volume(0)  # Start silent and fade in
            self.is_fading = True
            self.fade_start_time = pygame.time.get_ticks()
            self.current_state = self.game_state


    def update_volume(self):
        """Updates the volume of the background music to create a fade-in effect based on elapsed time."""
        if self.is_fading:
            elapsed_time = pygame.time.get_ticks() - self.fade_start_time
            fraction = min(elapsed_time / self.fade_duration, 1.0)

            new_volume = fraction * 0.8  # Assuming max volume is 0.8
            self.music.set_volume(new_volume)

            if elapsed_time >= self.fade_duration:
                self.is_fading = False
                self.music.set_volume(0.8)  # Ensure volume is set to full after fade-in completes



    def bullet_enemy_collision(self):
        """
        Checks for collisions between player spells and enemies. 
        Reduces the health of enemies hit by a spell.
        """
        if self.spell_group:
            for spell in self.spell_group:
                coll = pygame.sprite.spritecollide(spell, self.enemy_group, False)
                if coll:
                    for enemy in coll:
                        enemy.health -= 101
                        #print(enemy.health)
                    spell.kill()

    def spell_player_collision(self):
        """
        Checks for collisions between enemy spells and the player. 
        Reduces the player's health if hit by an enemy spell.
        """
        if self.enemy_spell_group:
            for spell in self.enemy_spell_group:
                coll = pygame.sprite.spritecollide(spell, self.player_group, False)
                if coll:
                    self.player.current_health -= 200
                    spell.kill()

    def sword_enemy_collision(self):
        """
        Checks for collisions between the player's sword and enemies. 
        Kills enemies that are hit by the sword.
        """
        if self.sword:
            coll = pygame.sprite.spritecollide(self.sword, self.enemy_group, False)
            if coll:
                for enemy in coll:
                    enemy.kill()
                self.player.hide_sword()

    def player_potion_collisons(self):
        """
        Checks for collisions between the player and potions. 
        Grants health or mana based on the potion type.
        """
        coll = pygame.sprite.spritecollide(self.player, self.potion_group, False)
        if coll:
            for potion in coll:
                if potion.type == 'mana':
                    self.player.get_mana(potion.value)
                else:
                    self.player.get_health(potion.value)

                potion.kill()

    def player_enemy_collisons(self):
        """
        Checks for collisions between the player and enemies. 
        Damages the player based on the enemy's attack and kills the enemy.
        """
        coll = pygame.sprite.spritecollide(self.player, self.enemy_group, False)
        if coll:
            for enemy in coll:
                self.player.damage(enemy.attack_damage)

                enemy.kill()

    def take_key(self):
        """
        Checks if the player has collided with the key item. 
        If so, the key is collected, and the player can use it later.
        """
        if self.player.rect.colliderect(self.key):
            self.key.kill()
            self.have_key = True

        if self.have_key:
            #pygame.draw.rect(self.screen, (0,0,255),(100,300, 10, 15))
            self.screen.blit(pygame.image.load('images/tiles/tile092.png').convert_alpha(), (220,15))

    def collide_end(self):
        """
        Checks for collisions between the player and the level's end point. 
        If the player has the key, they can progress to the next level.
        """
        if self.player.rect.colliderect(self.end_level) and self.have_key == True:
            if self.number_of_level <= self.level_number +1:
                self.end_game = True
                return
            else:    
                self.level_number += 1
                for enemy in self.end_group:
                    enemy.kill()

                self.game_state = 'exploration'
                self.is_calm = True
                self.have_key = False
                self.key_group.empty()
                self.all_sprites.empty()
                self.block_group.empty()
                self.enemy_group.empty()
                self.player_group.empty()
                self.enemy_spell_group.empty()
                self.potion_group.empty
                self.end_group.empty()
                self.sprite_group.empty()
                if self.important_table[2] != True:
                    self.music.stop()

                self.next_level()

    def get_mouse_direciton(self):
        """Retrieves the direction from the player to the mouse cursor."""
        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        player_pos = pygame.Vector2(W/2, H/2)
        try:
            # Handle the case where mouse is directly on player position
            if (mouse_pos - player_pos).length() > 0:
                self.player_direction = (mouse_pos - player_pos).normalize()
            else:
                self.player_direction = pygame.Vector2(1, 0)  # Default direction if mouse on player
        except ValueError:
            # Fallback in case of error
            self.player_direction = pygame.Vector2(1, 0)

    def get_distance_to_enemy(self):
        """Calculates and stores the distance from the player to each enemy."""
        self.enemy_dict = {}
        for enemy in self.enemy_group:
            distance = ((self.player.rect.centerx - enemy.rect.centerx)**2 + (self.player.rect.centery - enemy.rect.centery)**2)**(1/2)
            self.enemy_dict[enemy] = distance


    def update_game_state(self):
        """
        Updates the game state based on the distance to the nearest enemy.
        Transitions between exploration, close to enemy, and battle states.
        """
        if self.enemy_dict:
            #print(min(self.enemy_dict.values()))
            if min(self.enemy_dict.values()) < 400 and min(self.enemy_dict.values()) > 200:
                self.game_state = 'close_to_enemy'
            elif min(self.enemy_dict.values()) <= 200:
                self.game_state = 'battle'
            else:
                self.game_state = 'exploration'
        else:
            self.game_state = 'exploration'


    def magic_attack(self):
        """
        Triggers a magic attack when the player clicks the mouse. 
        Ensures that the player has enough mana and that the cooldown has passed.
        """
        if pygame.mouse.get_pressed()[0] and self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_attack_time > self.attack_cooldown and self.player.current_mana >= 100:
                pos = self.player.rect.center + self.player_direction * 20
                spell = Spell(pos, self.player_direction, self.sprite_group, self.block_group)
                self.spell_group.add(spell)
                self.player.usage(100)
                self.last_attack_time = current_time
    
    def sword_attack(self):
        """Triggers a sword attack for the player."""
        self.sword = Sword(self.player, [self.sprite_group])

    def hide_sword(self):
        """Hides the player's sword if it is active."""
        if self.sword:
            self.sword.kill()
            self.sword = None 
        self.sword = None 

    def next_level(self):
        """Sets up the next level and loads its corresponding map."""
        self.level_date = level_date_tabel[self.level_number]
        self.setup_level(self.level_date)
        self.sprite_group.back = pygame.image.load(level_map_table[self.level_number]).convert()


    def update(self):
        """
        Updates the game by processing collisions, checking the game state, and performing actions such as 
        magic and sword attacks, key collection, and level transitions.
        """
        self.get_distance_to_enemy()
        self.get_mouse_direciton()
        self.update_game_state()
        self.bullet_enemy_collision()
        self.spell_player_collision()
        self.sword_enemy_collision()
        self.player_potion_collisons()
        self.player_enemy_collisons()
        
        if self.important_table[1] == True:
            self.check_state()
            self.update_volume()
        elif self.important_table[2] == True:
            self.music_generator()

        self.magic_attack()
        
        # Display ESC key hint
        self.screen.blit(self.esc_hint_text, self.esc_hint_rect)
        
        # Display ESC key hint
        self.screen.blit(self.esc_hint_text, self.esc_hint_rect)
        #self.block_group.draw(self.screen)
        #self.player_group.draw(self.screen)
        #self.end_group.draw(self.screen)
        if self.sword: 
            self.sword.update()
        

        #print(self.have_key)
        self.sprite_group.update()
        self.sprite_group.custom_draw(self.player)
        #self.player.update() -> self.sprite_group.update() już to wykonuje
        self.take_key()
        self.player.health_bar_logic()
        self.player.mana_bar_logic()


        self.collide_end()
        if self.end_game == True or self.player.is_dead == True:
            if self.important_table[2] != True:
                self.music.stop()

            if self.end_game == True:
                return -1

            elif self.player.is_dead == True:
                return -2

class Allsprites(pygame.sprite.Group):
    """
    A class extending pygame.sprite.Group that manages all sprites on the screen,
    allowing them to be drawn and offset relative to the player's position.
    """
    def __init__(self, lev_number):
        """
        Initializes the sprite group and sets the level background based on the level number.

        Parameters:
            lev_number (int): The level number that determines which background will be loaded.
        """
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.half_width = self.display_surface.get_size()[0] // 2
        self.half_height = self.display_surface.get_size()[1] // 2
        self.offset = pygame.math.Vector2()
        self.back = pygame.image.load(level_map_table[lev_number]).convert()
        self.back_rect = self.back.get_rect(topleft = (0,0))
        
    def custom_draw(self,player):
        """
        Draws all sprites on the screen, offsetting them relative to the player's position.
        The background is also drawn to follow the player's position in the game world.

        Parameters:
            player (pygame.sprite.Sprite): The player object whose position will determine
                                           the offset of all objects on the screen.
        """
        self.offset.x = player.rect.centerx - self.half_width
        self.offset.y = player.rect.centery - self.half_height
        
        back_offset = self.back_rect.topleft - self.offset
        self.display_surface.blit(self.back,back_offset)

        for sprite in sorted(self.sprites(),key = lambda sprite: sprite.rect.centery):
            offset_pos = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image,offset_pos)