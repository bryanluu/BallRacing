import pygame
import utilities
import colors
import numpy as np
from enum import Enum
import time
import geometry as geo


class PowerupType(Enum):
    GUN_BOOST = 0  # grants moderate speed boost to the gun


class Weapon(Enum):
    MACHINE_GUN = 0


class Copter(pygame.sprite.Sprite):
    MACHINE_GUN_RELOAD_TIME = 0.5
    BOOSTED_MACHINE_GUN_RELOAD_TIME = 0.3
    DEFAULT_AMMO = np.inf

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
        self.ammo = self.DEFAULT_AMMO

        self.power = None
        self.powerActive = False

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def update(self):
        self.image = pygame.transform.scale(self.strips.next(), (85, 30))

    def shoot(self):
        if self.ammo <= 0:
            self.removePower()

        pos = self.rect.center

        if self.weapon == Weapon.MACHINE_GUN:
            ball_speed = 20
            power = 1

            ball = Bullet(pos, geo.Vector2D(power * ball_speed * np.cos(np.radians(self.angle)), -power * ball_speed * np.sin(np.radians(self.angle))))

            pygame.mixer.Sound.play(ball.sound)

        self.ammo -= 1
        self.lastShootTime = time.time()

        return ball

    def readyToShoot(self):
        reload_time = self.MACHINE_GUN_RELOAD_TIME
        if self.hasPower():
            reload_time = self.BOOSTED_MACHINE_GUN_RELOAD_TIME
        return time.time() - self.lastShootTime > reload_time

    def shootTowards(self, pos):
        # shoot towards the mouse location
        dr = geo.Vector2D(*pos) - geo.Vector2D(*self.rect.center)
        self.angle = (np.degrees(geo.Vector2D.angle_between(dr, geo.Vector2D(1, 0))))
        return self.shoot()

    # checks if the copter has a power if none given, or else the given powertype
    def hasPower(self, type=None):
        if type is None:
            return self.power
        else:
            return self.power and self.power.type == type

    # gives power to copter
    def givePower(self, power):
        self.power = power
        self.activatePower()

    # removes power from copter
    def removePower(self):
        self.deactivatePower()
        self.power = None

    # activates powerup if the copter has one
    def activatePower(self):
        if self.hasPower():
            if self.ammo == self.DEFAULT_AMMO:
                self.ammo = self.power.ammo
            else:
                self.ammo += self.power.ammo
            self.powerActive = True

    # deactivates powerup if the car has one
    def deactivatePower(self):
        self.weapon = Weapon.MACHINE_GUN
        self.ammo = self.DEFAULT_AMMO
        self.powerActive = False


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


class Powerup(pygame.sprite.Sprite):
    SIDE_LENGTH = 15  # length of side
    DEFAULT_LOOP_TIME = 2  # time to loop through shades

    def __init__(self, top):
        # Call the parent class (Sprite) constructor
        pygame.sprite.Sprite.__init__(self)

        info = pygame.display.Info()
        screenWidth = info.current_w

        self.rect = pygame.Rect(screenWidth, top,
                                self.SIDE_LENGTH, self.SIDE_LENGTH)

        self.image = pygame.Surface([self.SIDE_LENGTH, self.SIDE_LENGTH])
        self.lastLoop = time.time()
        self.type = PowerupType.GUN_BOOST
        self.color = colors.RED
        self.ammo = 10

    def update(self):
        t = time.time() - self.lastLoop
        color = np.array(self.color)
        if t > self.DEFAULT_LOOP_TIME:
            self.lastLoop = time.time()
        else:
            # find the shade of the color using a linear seesaw
            color = (1-0.3*(1-abs(t-self.DEFAULT_LOOP_TIME/2)/(self.DEFAULT_LOOP_TIME/2)))*color
        self.image.fill(color)
        self.rect.left -= Wall.SPEED
