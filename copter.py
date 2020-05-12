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

        self.rect = pygame.Rect(0, 0, 20, 20)
        self.rect.center = pos

        self.image = pygame.Surface([20, 20])
        self.image.fill(colors.RED)

        self.angle = 0
        self.weapon = Weapon.MACHINE_GUN
        self.lastShootTime = time.time()

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def update(self):
        pass

    def shoot(self):
        pos = self.rect.center

        if self.weapon == Weapon.MACHINE_GUN:
            ball_speed = 40
            power = 1

            ball = Bullet(pos, geo.Vector2D(power * ball_speed * np.cos(np.radians(self.angle)), -power * ball_speed * np.sin(np.radians(self.angle))))

            pygame.mixer.Sound.play(ball.sound)
        elif self.weapon == Weapon.BOMB:
            ball_speed = 30
            power = 1

            ball = Bomb(pos, geo.Vector2D(power * ball_speed * np.cos(np.radians(self.angle)), -power * ball_speed * np.sin(np.radians(self.angle))))

            pygame.mixer.Sound.play(self.cannon_sound)

            self.ammo -= 1

            if self.ammo == 0:
                self.weapon = Weapon.CANNON

        else:
            info = pygame.display.Info()
            screenWidth, screenHeight = info.current_w, info.current_h

            ball = Laser(pos, geo.Vector2D(2*screenWidth*np.cos(np.radians(self.angle)), -2*screenHeight*np.sin(np.radians(self.angle))))

            pygame.mixer.Sound.play(ball.sound)

            self.ammo -= 1

            if self.ammo == 0:
                self.weapon = Weapon.CANNON

        self.lastShootTime = time.time()

        return ball


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



class Bomb(Projectile):
    BOMB_FUSE_TIME = 5
    def initGraphics(self, pos):
        self.strips = utilities.SpriteStripAnim('bomb.png', (0, 0, 60, 60), (12, 1), colorkey=-1, frames=5)
        self.strips.iter()
        self.image = self.strips.next()
        self.image = pygame.transform.scale(self.image, (5, 5))
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.sound = utilities.load_sound('bomb.wav')
        self.start = time.time()
        self.kill_on_explode = False

    def explode(self):
        pygame.mixer.Sound.play(self.sound)

        return self.strips

    @staticmethod
    def collided(left, right):
        x, y, w, h = left.rect
        x2, y2, w2, h2 = right.rect

        radius = 30

        if x + radius > x2 and x - radius < x2 + w2 and y + radius > y2 and y - radius < y2 + h2:
            if left.kill_on_explode or time.time() - left.start > Bomb.BOMB_FUSE_TIME:
                return True
        else:
            return False


class Bullet(Projectile):

    def initGraphics(self, pos):
        self.image = utilities.load_image('ball.png')
        self.image = pygame.transform.scale(self.image, (5, 5))
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.sound = utilities.load_sound('bullet.wav')

    def explode(self):
        pygame.mixer.Sound.play(self.sound)


class Laser(Projectile):
    LASER_TIME = 0.2
    def initGraphics(self, pos):
        self.rect = pygame.Rect(*pos, 1, 1)
        self.sound = utilities.load_sound('laser.wav')

    def draw(self, screen):
        pygame.draw.line(screen, colors.RED, self.rect.topleft, (geo.Vector2D(*self.pos()) + self.v).tuple())

    @staticmethod
    def collided(left, right):

        topline = geo.Vector2D(*right.rect.topleft) - geo.Vector2D(*left.pos())
        bottomline = geo.Vector2D(*right.rect.bottomleft) - geo.Vector2D(*left.pos())

        if geo.Vector2D.angle_between(left.v, topline) < 0 < geo.Vector2D.angle_between(left.v, bottomline):
            return True
        else:
            return False

    def update(self):
        pass


class Enemy(pygame.sprite.Sprite):
    # Constructor. Pass in the color of the block,
    # and its x and y position
    def __init__(self, y):
        # Call the parent class (Sprite) constructor
        pygame.sprite.Sprite.__init__(self)
        self.y = y

    def update(self):
        pass


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
        self.rect = pygame.Rect(screenWidth, self.y, 32, 32)
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)
        self.speed = speed

    def update(self):
        self.x -= self.speed
        self.y += np.random.mtrand.standard_normal()
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        self.image = self.strips.next()
