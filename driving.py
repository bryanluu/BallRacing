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

    def draw(self, screen):
        image = pygame.transform.rotate(self.image, np.degrees(-self.angle))
        screen.blit(image, self.rect)

    def update(self):
        self.speed = max(-self.MAX_REV_SPEED, min(self.max_speed, self.speed + self.acceleration))
        self.v = geo.Vector2D.create_from_angle(self.angle, self.speed)
        self.rect.move_ip(*self.v)

    def pos(self):
        return geo.Vector2D(*self.rect.center)
