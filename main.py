import pygame
from game.game_engine import GameEngine

# Initialize pygame
pygame.init()

# Initialize audio separately
try:
    pygame.mixer.init()
    print("Audio initialized successfully.")
except pygame.error as e:
    print("Audio initialization failed:", e)

# Screen dimensions
WIDTH, HEIGHT = 700, 600

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fruit Slice - Pygame Version")

# Colors
DARK_BLUE = (20, 25, 45)

# Clock
clock = pygame.time.Clock()
FPS = 60

# Create game engine
engine = GameEngine(WIDTH, HEIGHT)


def main():
    running = True

    while running:

        SCREEN.fill(DARK_BLUE)

        # Handle events
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            engine.handle_event(event)

        # Handle continuous input
        engine.handle_input()

        # Update game
        engine.update()

        # Draw game
        engine.render(SCREEN)

        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
