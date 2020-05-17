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
    SLOWED_FWD_SPEED = 5
    SLOWED_REV_SPEED = 5
    TRAIL_LENGTH = 10

    def __init__(self, pos, color):
        pygame.sprite.Sprite.__init__(self)

        self.rect = pygame.Rect(0, 0, 20, 20)
        self.rect.center = pos

        self.image = pygame.Surface([20, 20])
        self.image.fill(color)
        self.color = color

        self.angle = 0
        self.speed = 0
        self.max_speed = self.MAX_FWD_SPEED
        self.acceleration = 0
        self.v = geo.Vector2D.create_from_angle(self.angle, self.speed) # angle in radians

        self.lastPowerupTime = 0
        self.boosted = False
        self.slowed = False
        self.trail = []

    def draw(self, screen):
        # draw trail
        if len(self.trail) > 1:
            pygame.draw.aalines(screen, self.color, False, self.trail)

        # draw car
        image = pygame.transform.rotate(self.image, np.degrees(-self.angle)) # angle in radians
        screen.blit(image, self.rect)

    def update(self):
        if self.boosted:
            if not self.slowed:
                self.MAX_FWD_SPEED = self.BOOST_FWD_SPEED
                self.MAX_REV_SPEED = self.BOOST_REV_SPEED
            else:
                self.MAX_FWD_SPEED = self.DEFAULT_MAX_FWD_SPEED
                self.MAX_REV_SPEED = self.DEFAULT_MAX_REV_SPEED
        else:
            if not self.slowed:
                self.MAX_FWD_SPEED = self.DEFAULT_MAX_FWD_SPEED
                self.MAX_REV_SPEED = self.DEFAULT_MAX_REV_SPEED
            else:
                self.MAX_FWD_SPEED = self.SLOWED_FWD_SPEED
                self.MAX_REV_SPEED = self.SLOWED_REV_SPEED

        if self.boosted:
            self.trail.append([self.rect.center[0], self.rect.center[1]])
            while (len(self.trail) > self.TRAIL_LENGTH):
                self.trail.pop(0)
        else:
            self.trail = []

        self.speed = max(-self.MAX_REV_SPEED, min(self.max_speed, self.speed + self.acceleration))
        self.v = geo.Vector2D.create_from_angle(self.angle, self.speed) # angle in radians
        self.rect.move_ip(*self.v)

    def pos(self):
        return geo.Vector2D(*self.rect.center)

    def driveTowards(self, dest):
        dr = dest - self.pos()
        self.angle = dr.angle() # angle in radians
        self.acceleration = 1
        self.max_speed = min(self.MAX_FWD_SPEED, dr.length()/5)

    def driveAwayFrom(self, point):
        dr = point - self.pos()
        self.angle = dr.angle() # angle in radians
        self.acceleration = -1

    def idle(self):
        if self.speed > 0:
            self.acceleration = -1
        else:
            self.acceleration = 0
            self.speed = 0


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

class FinishLine(pygame.sprite.Sprite):
    def __init__(self, pos, width, height, horizontal=True):
        pygame.sprite.Sprite.__init__(self)

        self.rect = pygame.Rect(*pos, width, height)
        self.image = pygame.Surface([width, height])

        for i in range(8):
            for j in range(2):
                if horizontal:
                    w, h = width/8, height/2
                else:
                    w, h = width/2, height/8

                rect = pygame.Rect(i*w, j*h, w, h)
                surf = pygame.Surface([w, h])
                if (i+j)%2 == 0:
                    surf.fill(colors.BLACK)
                else:
                    surf.fill(colors.WHITE)
                self.image.blit(surf, rect)
