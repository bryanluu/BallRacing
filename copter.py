import pygame
import utilities
import colors
import numpy as np
from enum import Enum
import time
import geometry as geo


class Weapon(Enum):
    MACHINE_GUN = 0
    BOMB = 1
    LASER = 2


class Copter(pygame.sprite.Sprite):
    MACHINE_GUN_RELOAD_TIME = 0.5

    def __init__(self, pos):
        # Call the parent class (Sprite) constructor
        pygame.sprite.Sprite.__init__(self)

        self.strips = utilities.SpriteStripAnim('helicopter-spritesheet.png',
                                                (0, 0, 423, 150), (1, 4),
                                                colorkey=-1,
                                                frames=4,
                                                loop=True)
        self.strips.iter()
        self.update()

        self.rect = self.image.get_rect()
        self.rect.center = pos

        self.angle = 0
        self.weapon = Weapon.MACHINE_GUN
        self.lastShootTime = time.time()
        self.deathSound = utilities.load_sound('bomb.wav')

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def update(self):
        self.image = pygame.transform.scale(self.strips.next(), (85, 30))

    def shoot(self):
        pos = self.rect.center

        if self.weapon == Weapon.MACHINE_GUN:
            ball_speed = 20
            power = 1

            ball = Bullet(pos, geo.Vector2D(power * ball_speed * np.cos(np.radians(self.angle)), -power * ball_speed * np.sin(np.radians(self.angle))))

            pygame.mixer.Sound.play(ball.sound)

        self.lastShootTime = time.time()

        return ball

    def readyToShoot(self):
        return time.time() - self.lastShootTime > self.MACHINE_GUN_RELOAD_TIME

    def shootTowards(self, pos):
        # shoot towards the mouse location
        dr = geo.Vector2D(*pos) - geo.Vector2D(*self.rect.center)
        self.angle = (np.degrees(geo.Vector2D.angle_between(dr, geo.Vector2D(1, 0))))
        return self.shoot()


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


class Projectile(pygame.sprite.Sprite):

    def __init__(self, pos, velocity):
        # Call the parent class (Sprite) constructor
        pygame.sprite.Sprite.__init__(self)

        self.v = velocity
        self.initGraphics(pos)

    def initGraphics(self, pos):
        self.image = pygame.Surface((5, 5))
        self.rect = self.image.get_rect()
        self.rect.center = pos

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def pos(self):
        return self.rect.center

    def explode(self):
        return None

    def update(self):
        self.rect.move_ip(*self.v)


class Bullet(Projectile):

    def initGraphics(self, pos):
        self.image = utilities.load_image('ball.png')
        self.image = pygame.transform.scale(self.image, (5, 5))
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.sound = utilities.load_sound('bullet.wav')

    def explode(self):
        pygame.mixer.Sound.play(self.sound)


class Enemy(pygame.sprite.Sprite):
    # Constructor. Pass in the color of the block,
    # and its x and y position
    def __init__(self, y):
        # Call the parent class (Sprite) constructor
        pygame.sprite.Sprite.__init__(self)
        self.y = y
        self.lives = 1

    def update(self):
        pass

    def hurt(self):
        self.lives -= 1
        if self.lives == 0:
            self.kill()


class Bat(Enemy):
    # Constructor. Pass in the color of the block,
    # and its x and y position
    def __init__(self, y, speed):
        # Call the parent class (Sprite) constructor
        Enemy.__init__(self, y)

        # Create an image of the block, and fill it with a color.
        # This could also be an image loaded from the disk.
        self.strips = utilities.SpriteStripAnim('bat.png', (0, 128 - 32, 32, 32), (4, 1), colorkey=-1, frames=3, loop=True)
        self.strips.iter()
        self.image = self.strips.next()

        info = pygame.display.Info()
        screenWidth, screenHeight = info.current_w, info.current_h

        # Fetch the rectangle object that has the dimensions of the image
        # Update the position of this object by setting the values of rect.x and rect.y
        self.rect = self.image.get_rect()
        self.rect.left = screenWidth
        self.rect.top = y
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)
        self.speed = speed

    def update(self):
        self.x -= self.speed
        self.y += np.random.mtrand.standard_normal()
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        self.image = self.strips.next()


class Obstacle(Enemy):
    def __init__(self, top, height):
        # Call the parent class (Sprite) constructor
        Enemy.__init__(self, top)

        info = pygame.display.Info()
        screenWidth = info.current_w

        self.rect = pygame.Rect(screenWidth, top, 2 * Wall.WIDTH, height)

        self.image = pygame.Surface([2 * Wall.WIDTH, height])
        self.color = np.array(colors.GRAY, dtype=int)
        self.image.fill(self.color)

        self.lives = 2

    def update(self):
        self.rect.left -= Wall.SPEED

    def hurt(self):
        Enemy.hurt(self)

        self.color = np.array(np.rint(self.color * 0.9), dtype=int)
        self.image.fill(self.color)
