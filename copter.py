import pygame
import utilities
import colors


class Wall(pygame.sprite.Sprite):
    WIDTH = 10
    COLOR = colors.DARK_GREEN
    SPEED = 10

    # Constructor. Pass in the color of the block,
    # and its x and y position
    def __init__(self, top, height):
        # Call the parent class (Sprite) constructor
        pygame.sprite.Sprite.__init__(self)

        info = pygame.display.Info()
        screenWidth = info.current_w

        self.rect = pygame.Rect(screenWidth, top, Wall.WIDTH, height)

        self.image = pygame.Surface([Wall.WIDTH, height])
        self.image.fill(Wall.COLOR)

    def update(self):
        self.rect.left -= Wall.SPEED
