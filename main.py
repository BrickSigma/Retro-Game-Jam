import pygame
import asyncio

# pygame setup
pygame.init()
screen = pygame.display.set_mode((800, 800))
clock = pygame.time.Clock()

async def main():
    rect = pygame.rect.Rect(0, 0, 30, 30)

    running = True
    while running:
        # poll for events
        # pygame.QUIT event means the user clicked X to close your window
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    running = False
                case pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            rect.x -= 3
        elif keys[pygame.K_RIGHT]:
            rect.x += 3
        if keys[pygame.K_UP]:
            rect.y -= 3
        elif keys[pygame.K_DOWN]:
            rect.y += 3

        # Clear the scrren
        screen.fill((255, 255, 255))

        # Game rendering below
        pygame.draw.rect(screen, (255, 0, 0), rect)

        # Update the screen (flip() swaps the backbuffer and framebuffer)
        pygame.display.flip()

        clock.tick(60)  # limits FPS to 60
        await asyncio.sleep(0)  # Needed for web build

    pygame.quit()

asyncio.run(main())