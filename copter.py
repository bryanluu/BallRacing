import pygame
import utilities
import colors
import numpy as np
from enum import Enum
import time
import geometry as geo


class PowerupType(Enum):
    GUN_BOOST = 0  # grants moderate speed boost to the gun
    SHIELD = 1  # grants temporary immunity to obstacles
    LASER = 2  # grants the ability to shoot a laser
    NUMBER_POWERUPS = 3  # number of valid powerups


class Weapon(Enum):
    MACHINE_GUN = 0
    LASER = 1


class Copter(pygame.sprite.Sprite):
    MACHINE_GUN_RELOAD_TIME = 0.5
    BOOSTED_MACHINE_GUN_RELOAD_TIME = 0.3
    DEFAULT_AMMO = np.inf
    DEFAULT_WEAPON = Weapon.MACHINE_GUN
    SHIELD_LOOP_TIME = 0.7

    def __init__(self, pos):
        # Call the parent class (Sprite) constructor
        pygame.sprite.Sprite.__init__(self)

        self.angle = 0
        self.weapon = self.DEFAULT_WEAPON
        self.lastShootTime = time.time()
        self.deathSound = utilities.load_sound('bomb.wav')
        self.ammo = self.DEFAULT_AMMO
        self.powerupText = pygame.font.SysFont('helvetica', 12)

        self.power = None
        self.powerActive = False
        self.lastPowerupTime = 0

        self.strips = utilities.SpriteStripAnim('helicopter-spritesheet.png',
                                                (0, 0, 423, 150), (1, 4),
                                                colorkey=-1,
                                                frames=1,
                                                loop=True)
        self.strips.iter()
        self.setCopterImage()
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.surface = pygame.Surface([self.rect.width + 20, self.rect.height], flags=pygame.SRCALPHA)
        self.surface.fill((0, 0, 0, 0))

    def draw(self, screen):
        self.surface.fill((0, 0, 0, 0))

        imageRect = self.image.get_rect()
        imageRect.x = 20
        self.surface.blit(self.image, imageRect)

        if self.ammo != np.inf and self.ammo > 0:
            ammoSurf = self.powerupText.render("{0:>3}".format(self.ammo), False, (0, 0, 0))
            ammoRect = ammoSurf.get_rect()
            ammoRect.x, ammoRect.y = 0, 5
            self.surface.blit(ammoSurf, ammoRect)

        if self.hasPower(PowerupType.SHIELD):
            height = 20 * max(self.power.timeLeft, 0) / self.power.startTimeLeft
            timeSurf = pygame.Surface([5, height])
            timeSurf.fill(colors.GREEN)
            timeRect = timeSurf.get_rect()
            timeRect.x, timeRect.y = 0, 5
            self.surface.blit(timeSurf, timeRect)

        surfaceRect = self.surface.get_rect()
        surfaceRect.x, surfaceRect.y = self.rect.x, self.rect.y
        screen.blit(self.surface, self.rect)

    def update(self):
        # powerup logic
        if self.powerActive:
            timeSpentActivated = time.time() - self.lastPowerupTime
            self.power.timeLeft = self.power.startTimeLeft - timeSpentActivated
            if self.power.timeLeft <= 0:
                self.removePower()
        if self.hasPower() and self.power.timeLeft <= 0:
            self.removePower()

        self.setCopterImage()

    def setCopterImage(self):
        self.image = pygame.transform.scale(self.strips.next(), (85, 30))

        if self.hasPower(PowerupType.SHIELD):
            # T is the time since last loop
            T = (time.time() - self.lastPowerupTime)\
                % self.SHIELD_LOOP_TIME
            # t goes from 1 to 0 to 1 during a loop time
            t = abs(T - self.SHIELD_LOOP_TIME / 2)\
                / (self.SHIELD_LOOP_TIME / 2)
            # construct linear ramp of alpha values for copter
            alpha = 255 - (1 - t) * (255 - 100)
            self.image.set_alpha(alpha)

    def shoot(self):
        if self.ammo <= 0:
            self.removePower()

        pos = self.gunLocation()

        if self.weapon == Weapon.MACHINE_GUN:
            ball_speed = 20
            power = 1

            ball = Bullet(pos, geo.Vector2D(power * ball_speed * np.cos(np.radians(self.angle)), -power * ball_speed * np.sin(np.radians(self.angle))))

            pygame.mixer.Sound.play(ball.sound)
        elif self.weapon == Weapon.LASER:
            info = pygame.display.Info()
            screenWidth, screenHeight = info.current_w, info.current_h

            ball = Laser(pos, geo.Vector2D(2 * screenWidth * np.cos(np.radians(self.angle)), -2 * screenHeight * np.sin(np.radians(self.angle))))

            pygame.mixer.Sound.play(ball.sound)

        self.ammo -= 1
        self.lastShootTime = time.time()

        return ball

    def readyToShoot(self):
        reload_time = self.MACHINE_GUN_RELOAD_TIME
        if self.hasPower(PowerupType.GUN_BOOST):
            reload_time = self.BOOSTED_MACHINE_GUN_RELOAD_TIME
        elif self.hasPower(PowerupType.LASER):
            reload_time = 0.5
        return time.time() - self.lastShootTime > reload_time

    def shootTowards(self, pos):
        # shoot towards the mouse location
        dr = geo.Vector2D(*pos) - geo.Vector2D(*self.rect.center)
        self.angle = (np.degrees(geo.Vector2D.angle_between(dr, geo.Vector2D(1, 0))))
        return self.shoot()

    # checks if the copter has a power if none given, or else the given powertype
    def hasPower(self, type=None):
        if type is None:
            return self.power is not None
        else:
            return self.power and self.power.type == type

    # gives power to copter
    def givePower(self, power):
        self.power = power
        if power.activateOnGet:
            self.activatePower()

    # removes power from copter
    def removePower(self):
        self.deactivatePower()
        self.power = None

    # activates powerup if the copter has one
    def activatePower(self):
        lastAmmo = self.ammo  # save ammo before activation
        lastWeapon = self.weapon  # save weapon before activation
        self.deactivatePower()  # reset defaults first
        if self.hasPower():
            if self.hasPower(PowerupType.GUN_BOOST):
                if lastWeapon != Weapon.MACHINE_GUN or lastAmmo == self.DEFAULT_AMMO:
                    self.ammo = self.power.ammo
                else:
                    self.ammo = lastAmmo + self.power.ammo
            if self.hasPower(PowerupType.LASER):
                self.weapon = Weapon.LASER
                if lastWeapon != Weapon.LASER or lastAmmo == self.DEFAULT_AMMO:
                    self.ammo = self.power.ammo
                else:
                    self.ammo = lastAmmo + self.power.ammo
            self.powerActive = True
            self.lastPowerupTime = time.time()
            self.power.startTimeLeft = self.power.timeLeft

    # deactivates powerup if the car has one
    def deactivatePower(self):
        self.weapon = self.DEFAULT_WEAPON
        self.ammo = self.DEFAULT_AMMO
        self.powerActive = False

    # location of gun
    def gunLocation(self):
        gunX = self.rect.right - 10
        gunY = self.rect.bottom
        return gunX, gunY


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

    @staticmethod
    def collided(left, right):
        return pygame.sprite.collide_rect(left, right)


class Bullet(Projectile):

    def initGraphics(self, pos):
        self.image = utilities.load_image('ball.png')
        self.image = pygame.transform.scale(self.image, (5, 5))
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.sound = utilities.load_sound('bullet.wav')


class Laser(Projectile):
    LASER_TIME = 0.2

    def initGraphics(self, pos):
        self.rect = pygame.Rect(pos, (1, 1))
        self.sound = utilities.load_sound('laser.wav')
        self.shootTime = time.time()

    def update(self):
        pass

    def draw(self, screen):
        t = (time.time() - self.shootTime) / self.LASER_TIME
        t = utilities.bound(0, t, 1)
        thickness = int((1 - t) * 3)
        color = colors.RED
        pygame.draw.line(screen, color, self.rect.topleft,
                         (geo.Vector2D(*self.pos()) + self.v).tuple(), thickness)

    @staticmethod
    def collided(left, right):

        topline = geo.Vector2D(*right.rect.topleft) - geo.Vector2D(*left.pos())
        bottomline = geo.Vector2D(*right.rect.bottomleft)\
            - geo.Vector2D(*left.pos())

        if geo.Vector2D.angle_between(left.v, topline)\
                < 0 < geo.Vector2D.angle_between(left.v, bottomline):
            return True
        else:
            return False


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

    def dead(self):
        return self.lives <= 0


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
    MIN_HEIGHT = 20

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
    DEFAULT_AMMO = np.inf  # default ammo of powerup
    DEFAULT_DURATION = np.inf  # default duration of powerup

    def __init__(self, top, type):
        # Call the parent class (Sprite) constructor
        pygame.sprite.Sprite.__init__(self)

        info = pygame.display.Info()
        screenWidth = info.current_w

        self.rect = pygame.Rect(screenWidth, top,
                                self.SIDE_LENGTH, self.SIDE_LENGTH)

        self.image = pygame.Surface([self.SIDE_LENGTH, self.SIDE_LENGTH])
        self.lastLoop = time.time()

        self.setType(type)

    def setType(self, type):
        self.type = type
        self.ammo = self.DEFAULT_AMMO
        self.duration = self.DEFAULT_DURATION
        self.activateOnGet = True

        if type == PowerupType.GUN_BOOST:
            self.color = colors.BLUE
            self.ammo = 10
        elif type == PowerupType.SHIELD:
            self.color = colors.YELLOW
            self.duration = 10
        elif type == PowerupType.LASER:
            self.color = colors.RED
            self.ammo = 1

        self.timeLeft = self.duration
        self.startTimeLeft = self.timeLeft

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
