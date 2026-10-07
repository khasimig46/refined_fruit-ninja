import math
import os
import random
import pygame

from .fruit import Fruit


# ---------------------------------------------------------
# Colors
# ---------------------------------------------------------
WHITE = (255, 255, 255)
BOMB_BLACK = (30, 30, 30)
RED = (220, 60, 60)
YELLOW = (240, 200, 60)

FRUIT_COLORS = [
    (220, 60, 60),
    (230, 140, 40),
    (230, 200, 40),
    (90, 180, 90)
]


class GameEngine:

    def __init__(self, width, height):

        self.width = width
        self.height = height

        # -------------------------------------------------
        # Game objects
        # -------------------------------------------------
        self.fruits = []

        # Mouse blade trail
        self.trail = []
        self.previous_mouse_pos = None

        # -------------------------------------------------
        # Difficulty settings
        # -------------------------------------------------
        self.difficulties = {

            "easy": {
                "spawn_interval": 70,
                "bomb_chance": 0.08,
                "speed_scale": 0.90
            },

            "medium": {
                "spawn_interval": 55,
                "bomb_chance": 0.15,
                "speed_scale": 1.00
            },

            "hard": {
                "spawn_interval": 40,
                "bomb_chance": 0.25,
                "speed_scale": 1.10
            }
        }

        self.difficulty = "medium"

        # -------------------------------------------------
        # Game state
        # -------------------------------------------------
        self.spawn_interval = 55
        self._spawn_timer = 0

        self.bomb_chance = 0.15
        self.speed_scale = 1.0

        self.lives = 3
        self.score = 0

        self.game_over = False

        # -------------------------------------------------
        # Fonts
        # -------------------------------------------------
        self.font = pygame.font.SysFont("Arial", 28)
        self.title_font = pygame.font.SysFont(
            "Arial",
            50,
            bold=True
        )

        self.small_font = pygame.font.SysFont(
            "Arial",
            22
        )

        # -------------------------------------------------
        # Initialize sounds
        # -------------------------------------------------
        self.sounds = {}

        self._initialize_audio()
        self._load_sounds()

    # =====================================================
    # AUDIO
    # =====================================================

    def _initialize_audio(self):

        """
        Initialize pygame mixer.
        """

        try:

            if not pygame.mixer.get_init():
                pygame.mixer.init()

            print("Audio initialized successfully.")

        except pygame.error as error:

            print("Audio initialization failed:")
            print(error)

    def _load_sounds(self):

        """
        Load all game sound files.

        Expected structure:

        game/
            game_engine.py
            assets/
                sounds/
                    slice.wav
                    bomb.wav
                    game_over.wav
        """

        sound_directory = os.path.join(
            os.path.dirname(
                os.path.abspath(__file__)
            ),
            "assets",
            "sounds"
        )

        print()
        print("Sound directory:")
        print(sound_directory)
        print()

        sound_files = {

            "slice": "slice.wav",
            "bomb": "bomb.wav",
            "game_over": "game_over.wav"
        }

        for sound_name, filename in sound_files.items():

            path = os.path.join(
                sound_directory,
                filename
            )

            print(
                f"Loading {sound_name} sound:"
            )

            print(path)

            if not os.path.exists(path):

                print(
                    f"ERROR: {filename} was not found!"
                )

                self.sounds[sound_name] = None

                continue

            try:

                sound = pygame.mixer.Sound(path)

                # Maximum volume
                sound.set_volume(1.0)

                self.sounds[sound_name] = sound

                print(
                    f"{sound_name} sound loaded successfully."
                )

            except pygame.error as error:

                print(
                    f"ERROR loading {filename}:"
                )

                print(error)

                self.sounds[sound_name] = None

        print()

    def _play_sound(self, sound_name):

        """
        Play a sound effect.
        """

        sound = self.sounds.get(sound_name)

        if sound is None:

            print(
                f"Sound '{sound_name}' is not loaded."
            )

            return

        try:

            sound.play()

            print(
                f"Playing sound: {sound_name}"
            )

        except pygame.error as error:

            print(
                f"Could not play sound '{sound_name}':"
            )

            print(error)

    # =====================================================
    # RESET / DIFFICULTY
    # =====================================================

    def reset_game(self, difficulty="medium"):

        """
        Reset everything for a new game.
        """

        if difficulty not in self.difficulties:

            difficulty = "medium"

        self.difficulty = difficulty

        settings = self.difficulties[difficulty]

        # Apply difficulty settings
        self.spawn_interval = settings[
            "spawn_interval"
        ]

        self.bomb_chance = settings[
            "bomb_chance"
        ]

        self.speed_scale = settings[
            "speed_scale"
        ]

        # Reset game data
        self.fruits = []

        self._spawn_timer = 0

        self.lives = 3
        self.score = 0

        self.game_over = False

        # Reset mouse information
        self.trail = []
        self.previous_mouse_pos = None

    # =====================================================
    # SPAWN
    # =====================================================

    def spawn_fruit(self):

        x = random.randint(
            60,
            self.width - 60
        )

        vy = (
            -random.uniform(13, 16)
            * self.speed_scale
        )

        vx = random.uniform(
            -2,
            2
        )

        gravity = 0.35

        # Decide fruit or bomb
        if random.random() < self.bomb_chance:

            kind = "bomb"

        else:

            kind = "fruit"

        fruit = Fruit(
            x,
            self.height + 30,
            vx,
            vy,
            gravity,
            kind=kind
        )

        if kind == "bomb":

            fruit.color = BOMB_BLACK

        else:

            fruit.color = random.choice(
                FRUIT_COLORS
            )

        self.fruits.append(fruit)

    # =====================================================
    # EVENTS
    # =====================================================

    def handle_event(self, event):

        # ---------------------------------------------
        # Mouse movement
        # ---------------------------------------------

        if event.type == pygame.MOUSEMOTION:

            self._handle_motion(
                event.pos
            )

        # ---------------------------------------------
        # Mouse button
        # ---------------------------------------------

        elif event.type == pygame.MOUSEBUTTONDOWN:

            self.previous_mouse_pos = event.pos

        # ---------------------------------------------
        # Keyboard
        # ---------------------------------------------

        elif event.type == pygame.KEYDOWN:

            if self.game_over:

                self._handle_game_over_key(
                    event.key
                )

    # =====================================================
    # MOUSE / BLADE
    # =====================================================

    def _handle_motion(self, pos):

        # Do not slice while game is over
        if self.game_over:

            self.previous_mouse_pos = pos

            self._update_trail(pos)

            return

        # -------------------------------------------------
        # First mouse position
        # -------------------------------------------------

        if self.previous_mouse_pos is None:

            self._check_point(pos)

        else:

            # Check complete movement between
            # previous and current mouse position.
            self._check_swipe(
                self.previous_mouse_pos,
                pos
            )

        # Save current position
        self.previous_mouse_pos = pos

        self._update_trail(pos)

    def _update_trail(self, pos):

        self.trail.append(pos)

        if len(self.trail) > 15:

            self.trail.pop(0)

    # =====================================================
    # FAST SWIPE COLLISION
    # =====================================================

    def _check_point(self, point):

        """
        Check if the current mouse position
        is inside a fruit/bomb.
        """

        mouse_x, mouse_y = point

        for fruit in self.fruits:

            if fruit.sliced:
                continue

            dx = mouse_x - fruit.x
            dy = mouse_y - fruit.y

            distance_squared = (
                dx * dx +
                dy * dy
            )

            radius = fruit.radius

            if distance_squared <= radius * radius:

                self._slice(fruit)

                # Bomb immediately ends game
                if self.game_over:
                    break

    def _check_swipe(self, start, end):

        """
        Check the COMPLETE mouse movement segment.

        This solves the fast-swipe problem.

        Old method:

            previous frame -> nothing
            current frame  -> nothing

        even though the mouse actually passed
        directly across the fruit.

        New method:

            Start -------------------- End
                    Fruit
                      X

        The entire line is checked.
        """

        for fruit in self.fruits:

            if fruit.sliced:
                continue

            distance = self._point_to_segment_distance(
                fruit.x,
                fruit.y,
                start,
                end
            )

            # Small extra tolerance makes slicing
            # more reliable.
            collision_radius = (
                fruit.radius + 5
            )

            if distance <= collision_radius:

                self._slice(fruit)

                # Bomb has been hit.
                # Stop processing this swipe.
                if self.game_over:
                    break

    @staticmethod
    def _point_to_segment_distance(
        px,
        py,
        start,
        end
    ):

        """
        Calculate shortest distance between:

            Point P

        and

            Line segment A -> B
        """

        ax, ay = start
        bx, by = end

        # Segment vector
        ab_x = bx - ax
        ab_y = by - ay

        # Point relative to A
        ap_x = px - ax
        ap_y = py - ay

        # Length squared
        ab_length_squared = (
            ab_x * ab_x +
            ab_y * ab_y
        )

        # If mouse didn't move
        if ab_length_squared == 0:

            return math.hypot(
                px - ax,
                py - ay
            )

        # Projection of AP onto AB
        t = (
            ap_x * ab_x +
            ap_y * ab_y
        ) / ab_length_squared

        # Keep projection inside segment
        t = max(
            0.0,
            min(1.0, t)
        )

        # Closest point on segment
        closest_x = (
            ax +
            t * ab_x
        )

        closest_y = (
            ay +
            t * ab_y
        )

        # Distance from fruit to closest point
        return math.hypot(
            px - closest_x,
            py - closest_y
        )

    # =====================================================
    # SLICE
    # =====================================================

    def _slice(self, fruit):

        if fruit.sliced:
            return

        fruit.sliced = True

        # ---------------------------------------------
        # Bomb
        # ---------------------------------------------

        if fruit.kind == "bomb":

            self._play_sound("bomb")

            self.game_over = True

            self._play_sound("game_over")

        # ---------------------------------------------
        # Fruit
        # ---------------------------------------------

        else:

            self.score += 1

            self._play_sound("slice")

    # =====================================================
    # INPUT
    # =====================================================

    def handle_input(self):

        # Game is mouse driven.
        pass

    # =====================================================
    # UPDATE
    # =====================================================

    def update(self):

        # Stop updating after game over
        if self.game_over:

            return

        # -------------------------------------------------
        # Spawn
        # -------------------------------------------------

        self._spawn_timer += 1

        if self._spawn_timer >= self.spawn_interval:

            self._spawn_timer = 0

            self.spawn_fruit()

        # -------------------------------------------------
        # Update fruits
        # -------------------------------------------------

        still_alive = []

        for fruit in self.fruits:

            fruit.update()

            # Already sliced
            if fruit.sliced:

                continue

            # Fruit/bomb left screen
            if fruit.off_screen(self.height):

                # Missing a fruit costs one life.
                if fruit.kind == "fruit":

                    self.lives -= 1

                continue

            still_alive.append(fruit)

        self.fruits = still_alive

        # -------------------------------------------------
        # Lives reached zero
        # -------------------------------------------------

        if self.lives <= 0:

            self.lives = 0

            self._trigger_game_over()

    def _trigger_game_over(self):

        if self.game_over:

            return

        self.game_over = True

        self._play_sound("game_over")

    # =====================================================
    # GAME OVER INPUT
    # =====================================================

    def _handle_game_over_key(self, key):

        # Easy
        if key == pygame.K_e:

            self.reset_game("easy")

        # Medium
        elif key == pygame.K_m:

            self.reset_game("medium")

        # Hard
        elif key == pygame.K_h:

            self.reset_game("hard")

        # Exit
        elif key == pygame.K_ESCAPE:

            pygame.event.post(
                pygame.event.Event(
                    pygame.QUIT
                )
            )

    # =====================================================
    # RENDER
    # =====================================================

    def render(self, screen):

        # -------------------------------------------------
        # Draw fruits and bombs
        # -------------------------------------------------

        for fruit in self.fruits:

            color = getattr(
                fruit,
                "color",
                WHITE
            )

            pygame.draw.circle(
                screen,
                color,
                (
                    int(fruit.x),
                    int(fruit.y)
                ),
                fruit.radius
            )

        # -------------------------------------------------
        # Draw blade trail
        # -------------------------------------------------

        if len(self.trail) >= 2:

            pygame.draw.lines(
                screen,
                WHITE,
                False,
                self.trail,
                3
            )

        # -------------------------------------------------
        # Score
        # -------------------------------------------------

        score_text = self.font.render(
            f"Score: {self.score}",
            True,
            WHITE
        )

        screen.blit(
            score_text,
            (10, 10)
        )

        # -------------------------------------------------
        # Lives
        # -------------------------------------------------

        lives_text = self.font.render(
            f"Lives: {self.lives}",
            True,
            WHITE
        )

        screen.blit(
            lives_text,
            (
                self.width - 130,
                10
            )
        )

        # -------------------------------------------------
        # Difficulty
        # -------------------------------------------------

        difficulty_text = self.small_font.render(
            f"Difficulty: {self.difficulty.title()}",
            True,
            WHITE
        )

        screen.blit(
            difficulty_text,
            (10, 45)
        )

        # -------------------------------------------------
        # Game Over
        # -------------------------------------------------

        if self.game_over:

            self._render_game_over(
                screen
            )

    # =====================================================
    # GAME OVER SCREEN
    # =====================================================

    def _render_game_over(self, screen):

        # Transparent dark overlay
        overlay = pygame.Surface(
            (
                self.width,
                self.height
            ),
            pygame.SRCALPHA
        )

        overlay.fill(
            (0, 0, 0, 210)
        )

        screen.blit(
            overlay,
            (0, 0)
        )

        # ---------------------------------------------
        # GAME OVER
        # ---------------------------------------------

        title = self.title_font.render(
            "GAME OVER",
            True,
            RED
        )

        title_rect = title.get_rect(
            center=(
                self.width // 2,
                160
            )
        )

        screen.blit(
            title,
            title_rect
        )

        # ---------------------------------------------
        # Score
        # ---------------------------------------------

        score_text = self.font.render(
            f"Final Score: {self.score}",
            True,
            WHITE
        )

        score_rect = score_text.get_rect(
            center=(
                self.width // 2,
                230
            )
        )

        screen.blit(
            score_text,
            score_rect
        )

        # ---------------------------------------------
        # Difficulty
        # ---------------------------------------------

        difficulty_text = self.small_font.render(
            f"Difficulty: {self.difficulty.title()}",
            True,
            WHITE
        )

        difficulty_rect = difficulty_text.get_rect(
            center=(
                self.width // 2,
                270
            )
        )

        screen.blit(
            difficulty_text,
            difficulty_rect
        )

        # ---------------------------------------------
        # Replay
        # ---------------------------------------------

        replay_text = self.font.render(
            "Choose Difficulty",
            True,
            YELLOW
        )

        replay_rect = replay_text.get_rect(
            center=(
                self.width // 2,
                330
            )
        )

        screen.blit(
            replay_text,
            replay_rect
        )

        # ---------------------------------------------
        # Options
        # ---------------------------------------------

        options = [
            "E - Easy",
            "M - Medium",
            "H - Hard",
            "ESC - Exit"
        ]

        y = 380

        for option in options:

            text = self.small_font.render(
                option,
                True,
                WHITE
            )

            rect = text.get_rect(
                center=(
                    self.width // 2,
                    y
                )
            )

            screen.blit(
                text,
                rect
            )

            y += 35
