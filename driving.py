import pygame
import utilities
import colors
import numpy as np
from enum import Enum
import time
import geometry as geo


class Car(pygame.sprite.Sprite):
    MAX_FWD_SPEED = 10
    MAX_REV_SPEED = 5
    DEFAULT_MAX_FWD_SPEED = 10
    DEFAULT_MAX_REV_SPEED = 5
    BOOST_FWD_SPEED = 15
    BOOST_REV_SPEED = 7

    def __init__(self, pos):
        pygame.sprite.Sprite.__init__(self)

        self.rect = pygame.Rect(0, 0, 20, 20)
        self.rect.center = pos

        self.image = pygame.Surface([20, 20])
        self.image.fill(colors.RED)

        self.angle = 0
        self.speed = 0
        self.max_speed = self.MAX_FWD_SPEED
        self.acceleration = 0
        self.v = geo.Vector2D.create_from_angle(self.angle, self.speed)

        self.lastPowerupTime = 0

    def draw(self, screen):
        image = pygame.transform.rotate(self.image, np.degrees(-self.angle))
        screen.blit(image, self.rect)

    def update(self):
        self.speed = max(-self.MAX_REV_SPEED, min(self.max_speed, self.speed + self.acceleration))
        self.v = geo.Vector2D.create_from_angle(self.angle, self.speed)
        self.rect.move_ip(*self.v)

    def pos(self):
        return geo.Vector2D(*self.rect.center)


class Powerup(pygame.sprite.Sprite):
    LOOP_TIME = 2 # time that the powerup loops through shades
    def __init__(self, pos):
        pygame.sprite.Sprite.__init__(self)

        self.rect = pygame.Rect(0, 0, 10, 10)
        self.rect.center = pos

        self.image = pygame.Surface([10, 10])
        self.color = None
        self.lastLoop = time.time()

    def update(self):
        t = time.time() - self.lastLoop
        color = np.array(self.color)
        if (t > self.LOOP_TIME):
            self.lastLoop = time.time()
        else:
            color = (1-0.3*(1-abs(t-self.LOOP_TIME/2)/(self.LOOP_TIME/2)))*color
        self.image.fill(color)

    def draw(self, screen):
        screen.blit(self.image, self.rect)


class SpeedBoost(Powerup):
    def __init__(self, pos):
        Powerup.__init__(self, pos)
        self.color = colors.GREEN


class Grass(pygame.sprite.Sprite):
    def __init__(self, pos, width, height):
        pygame.sprite.Sprite.__init__(self)

        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = pos
        self.image = pygame.Surface([width, height])
        self.image.fill(colors.DARK_GREEN)

class Barrier(pygame.sprite.Sprite):
    def __init__(self, pos, width, height):
        pygame.sprite.Sprite.__init__(self)

        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = pos
        self.image = pygame.Surface([width, height])
        self.image.fill((50, 50, 50))

