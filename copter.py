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
    ONE_UP = 3  # increases lives by 1
    NUMBER_POWERUPS = 4  # number of valid powerups


class Weapon(Enum):
    MACHINE_GUN = 0
    LASER = 1


class Copter(utilities.DrawSprite):
    MACHINE_GUN_RELOAD_TIME = 0.5
    BOOSTED_MACHINE_GUN_RELOAD_TIME = 0.3
    DEFAULT_AMMO = np.inf
    DEFAULT_WEAPON = Weapon.MACHINE_GUN
    SHIELD_LOOP_TIME = 0.7  # time between transparency loops
    INVINCIBILITY_TIME = 1  # time of invincibility after copter is hurt
    WEIGHT = 0.8  # affects acceleration
    ENGINE_STARTUP_TIME = 0.5  # time for the engine to rev up

    def __init__(self, pos):
        # Call the parent class (Sprite) constructor
        utilities.DrawSprite.__init__(self)

        self.angle = 0
        self.weapon = self.DEFAULT_WEAPON
        self.lastShootTime = 0
        self.ammo = self.DEFAULT_AMMO
        self.powerupText = pygame.font.SysFont('arial', 12)
        self.lives = 3
        self.lastHurtTime = 0

        self.power = None
        self.powerActive = False
        self.lastPowerupTime = 0

        self.v = geo.Vector2D.zero()
        self.a = geo.Vector2D.zero()
        self.flying = False
        self.controlled = True
        self.lastFlyTime = 0

        self.strips = utilities.SpriteStripAnim('helicopter-spritesheet.png',
                                                (0, 0, 423, 150), (1, 4),
                                                frames=1,
                                                loop=True)
        self.strips.iter()
        self.image = self.strips.next()
        self.setCopterImage()
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.surface = pygame.Surface([self.rect.width + 20,
                                      self.rect.height + 20],
                                      flags=pygame.SRCALPHA)
        self.surface.fill(colors.TRANSPARENT)

    def draw(self, screen):
        self.surface.fill(colors.TRANSPARENT)

        self.setCopterImage()

        imageRect = self.image.get_rect()
        imageRect.x = 20
        self.surface.blit(self.image, imageRect)

        if self.lives <= 5:
            heartStr = "♥" * self.lives
        else:
            heartStr = "♥ x {0}".format(self.lives)
        heartSurf = self.powerupText.render(heartStr, False, (255, 0, 0))
        heartRect = heartSurf.get_rect()
        heartRect.x, heartRect.y = 20, imageRect.height + 5
        self.surface.blit(heartSurf, heartRect)

        if self.ammo != np.inf and self.ammo > 0:
            ammoSurf = self.powerupText.render("{0:>3}".format(self.ammo),
                                               False, (0, 0, 0))
            ammoRect = ammoSurf.get_rect()
            ammoRect.x, ammoRect.y = 0, 5
            self.surface.blit(ammoSurf, ammoRect)

        if self.hasPower(PowerupType.SHIELD):
            height = 20 * max(self.power.timeLeft, 0)\
                / self.power.startTimeLeft
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

        if not self.invincible():
            self.controlled = True

        # flying logic
        if self.controlled:
            if self.flying:
                self.a = geo.Vector2D(0, -self.WEIGHT)
            else:
                self.a = geo.Vector2D(0, self.WEIGHT)
        else:
            self.a = geo.Vector2D.zero()
            self.v = geo.Vector2D.zero()

        self.v += self.a
        self.rect.move_ip(*self.v)

    def setCopterImage(self):
        if not self.controlled:
            self.strips.frames = 2
            nextImage = self.strips.next()
        else:
            if self.flying:
                T = time.time() - self.lastFlyTime
                if T < self.ENGINE_STARTUP_TIME:
                    # t goes from 0 to 1
                    t = T / self.ENGINE_STARTUP_TIME
                    start = 2
                    end = 1
                    # linear ramp from start to end
                    frames = round(utilities.ramp(start, end, t))
                    self.strips.frames = frames
                nextImage = self.strips.next()
            else:
                nextImage = self.image  # stop animation

        self.image = pygame.transform.scale(nextImage, (85, 30))

        if self.invincible():
            alpha = 100
            self.image.set_alpha(alpha)
        elif self.hasPower(PowerupType.SHIELD):
            # T is the time since last loop
            T = (time.time() - self.lastPowerupTime)\
                % self.SHIELD_LOOP_TIME
            # t goes from 0 to 1 in a loop
            t = T / self.SHIELD_LOOP_TIME
            # construct linear seesaw of alpha values for copter
            alpha = utilities.seesaw(100, 255, t)
            print(alpha)
            self.image.set_alpha(alpha)
        else:
            # set opaque
            self.image.set_alpha(255)

    def shoot(self):
        if self.ammo <= 0:
            self.removePower()

        pos = self.gunLocation()

        if self.weapon == Weapon.MACHINE_GUN:
            ball_speed = 20
            power = 1

            ball = Bullet(pos,
                          geo.Vector2D(power * ball_speed * np.cos(np.radians(self.angle)),
                                       -power * ball_speed * np.sin(np.radians(self.angle))))

        elif self.weapon == Weapon.LASER:
            info = pygame.display.Info()
            screenWidth, screenHeight = info.current_w, info.current_h

            ball = Laser(pos,
                         geo.Vector2D(2 * screenWidth * np.cos(np.radians(self.angle)),
                                      -2 * screenHeight * np.sin(np.radians(self.angle))))

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
        self.angle = (np.degrees(geo.Vector2D.angle_between(dr,
                                                            geo.Vector2D(1,
                                                                         0))))
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
            self.powerActive = True
            self.lastPowerupTime = time.time()
            self.power.startTimeLeft = self.power.timeLeft
            if self.hasPower(PowerupType.GUN_BOOST):
                if lastWeapon != Weapon.MACHINE_GUN\
                        or lastAmmo == self.DEFAULT_AMMO:
                    self.ammo = self.power.ammo
                else:
                    self.ammo = lastAmmo + self.power.ammo
            elif self.hasPower(PowerupType.LASER):
                self.weapon = Weapon.LASER
                if lastWeapon != Weapon.LASER or lastAmmo == self.DEFAULT_AMMO:
                    self.ammo = self.power.ammo
                else:
                    self.ammo = lastAmmo + self.power.ammo
            elif self.hasPower(PowerupType.ONE_UP):
                self.lives += 1
                self.removePower()

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

    # takes a life
    def hurt(self):
        if self.invincible():
            return False
        if not self.dead():
            self.lives -= 1
            self.lastHurtTime = time.time()
            self.controlled = False
        if self.dead():
            self.kill()
            return True
        else:
            return False

    def dead(self):
        return self.lives == 0

    def invincible(self):
        return time.time() - self.lastHurtTime < self.INVINCIBILITY_TIME

    def fly(self):
        if not self.flying:
            self.flying = True
            self.controlled = True
            self.lastFlyTime = time.time()

    def drop(self):
        self.flying = False

    def explode(self):
        pygame.mixer.Sound.play(self.deathSound)

        strips = utilities.SpriteStripAnim('explosion.png',
                                           (0, 0, 256, 256),
                                           (8, 7),
                                           frames=1)
        strips.iter()

        return strips


class Explosion(utilities.DrawSprite):
    SOUNDFILE = 'bomb.wav'
    SPRITESHEET = 'explosion.png'
    SIZE = (256, 256)
    COUNT = (8, 7)

    def __init__(self, pos):
        # Call the parent class (Sprite) constructor
        utilities.DrawSprite.__init__(self)

        self.sound = utilities.load_sound(self.SOUNDFILE)

        pygame.mixer.Sound.play(self.sound)

        self.strips = utilities.SpriteStripAnim(self.SPRITESHEET,
                                                (0, 0,
                                                 self.SIZE[0],
                                                 self.SIZE[1]),
                                                self.COUNT,
                                                frames=1,
                                                colorkey=-1)
        self.strips.iter()
        self.image = self.strips.next()
        self.rect = self.image.get_rect()
        self.rect.center = pos

    def draw(self, screen):
        self.image = self.strips.next()
        screen.blit(self.image, self.rect)

    def update(self):
        if self.strips.i >= len(self.strips.images):
            self.kill()
        elif self.rect.right < 0:
            self.kill()
        else:
            self.rect.x -= Wall.SPEED


class Wall(utilities.DrawSprite):
    WIDTH = 10
    COLOR = colors.DARK_GREEN
    SPEED = 10

    # Constructor. Pass in the color of the block,
    # and its four corners as y-coords
    # with the order being NW-NE-SE-SW
    def __init__(self, yNW, yNE, ySE, ySW):
        # Call the parent class (Sprite) constructor
        utilities.DrawSprite.__init__(self)

        top = min(yNW, yNE)
        bottom = max(ySW, ySE)
        height = bottom - top

        self.image = pygame.Surface([Wall.WIDTH, height])
        NW, NE, SE, SW = (0, yNW - top),\
            (Wall.WIDTH, yNE - top), (Wall.WIDTH, ySE - top), (0, ySW - top)
        self.rect = pygame.draw.polygon(self.image,
                                        Wall.COLOR,
                                        [NW, NE, SE, SW])
        info = pygame.display.Info()
        screenWidth = info.current_w
        self.rect.x, self.rect.y = screenWidth, top

    def update(self):
        self.rect.left -= Wall.SPEED


class Projectile(utilities.DrawSprite):

    def __init__(self, pos, velocity):
        # Call the parent class (Sprite) constructor
        utilities.DrawSprite.__init__(self)

        self.v = velocity
        self.initGraphics(pos)
        self.lastPos = pos

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
        self.lastPos = self.pos()
        self.rect.move_ip(*self.v)

    @staticmethod
    def collided(projectile, other):
        overlap = pygame.sprite.collide_mask(projectile, other)

        if not overlap:
            topline = geo.Vector2D(*other.rect.topleft)\
                - geo.Vector2D(*projectile.lastPos)
            bottomline = geo.Vector2D(*other.rect.bottomleft)\
                - geo.Vector2D(*projectile.lastPos)

            aimedAtOther = geo.Vector2D.angle_between(projectile.v, topline)\
                < 0 < geo.Vector2D.angle_between(projectile.v, bottomline)

            validPos = projectile.lastPos[0] <= other.rect.right\
                and projectile.pos()[0] >= other.rect.left

            passedThrough = aimedAtOther and validPos

        return overlap or passedThrough


class Bullet(Projectile):

    def initGraphics(self, pos):
        self.image = utilities.load_image('ball.png')
        self.image = pygame.transform.scale(self.image, (5, 5))
        self.image.set_colorkey(colors.WHITE)
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.sound = utilities.load_sound('bullet.wav')


class Laser(Projectile):
    LASER_TIME = 0.2

    def initGraphics(self, pos):
        self.rect = pygame.Rect(pos, (1, 1))
        self.sound = utilities.load_sound('laser.wav')
        self.shootTime = time.time()
        self.expire = False

    def update(self):
        if time.time() - self.shootTime > self.LASER_TIME:
            Projectile.kill(self)

    def draw(self, screen):
        t = (time.time() - self.shootTime) / self.LASER_TIME
        t = utilities.bound(0, t, 1)
        thickness = round((1 - t) * 3)
        color = colors.RED
        pygame.draw.line(screen, color, self.rect.topleft,
                         (geo.Vector2D(*self.pos()) + self.v).tuple(),
                         thickness)

    def kill(self):
        pass

    @staticmethod
    def collided(laser, other):

        topline = geo.Vector2D(*other.rect.topleft)\
            - geo.Vector2D(*laser.pos())
        bottomline = geo.Vector2D(*other.rect.bottomleft)\
            - geo.Vector2D(*laser.pos())

        if geo.Vector2D.angle_between(laser.v, topline)\
                < 0 < geo.Vector2D.angle_between(laser.v, bottomline):
            return True
        else:
            return False


class Enemy(utilities.DrawSprite):
    AWARD = 0

    # Constructor. Pass in the color of the block,
    # and its x and y position
    def __init__(self, y):
        # Call the parent class (Sprite) constructor
        utilities.DrawSprite.__init__(self)
        self.y = y
        self.lives = 1

    def update(self):
        pass

    # takes a life from the enemy, kills it if no lives left
    def hurt(self):
        if not self.dead():
            self.lives -= 1
        if self.dead():
            self.kill()
            return True
        else:
            return False

    def destroy(self):
        while not self.dead():
            self.hurt()

    def dead(self):
        return self.lives == 0


class Bat(Enemy):
    AWARD = 5  # award in seconds after kill
    CLEARANCE = 5  # space between bat and nearest wall

    # Constructor. Pass in the color of the block,
    # and its x and y position
    def __init__(self, y):
        # Call the parent class (Sprite) constructor
        Enemy.__init__(self, y)

        # Create an image of the block, and fill it with a color.
        # This could also be an image loaded from the disk.
        self.strips = utilities.SpriteStripAnim('bat.png',
                                                (0, 128 - 32, 32, 32),
                                                (4, 1),
                                                colorkey=-1,
                                                frames=3,
                                                loop=True)
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
        self.speed = Wall.SPEED * 1.2

    def fly(self, roof, ground):
        self.y = utilities.bound(roof + self.CLEARANCE,
                                 self.y + np.random.normal(),
                                 ground - self.rect.height - self.CLEARANCE)
        self.rect.y = int(self.y)

    def update(self):
        self.x -= self.speed
        self.rect.x = int(self.x)
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

        self.color = np.array(np.rint(self.color * 0.8), dtype=int)
        self.image.fill(self.color)


class Balloon(Enemy):
    AWARD = 5

    def __init__(self, top):
        # Call the parent class (Sprite) constructor
        Enemy.__init__(self, top)
        self.pop_sound = utilities.load_sound('balloon_pop.wav')

        info = pygame.display.Info()
        screenWidth = info.current_w

        choice = np.random.choice([0, 0, 0, 1, 1, 2])

        # Create an image of the block, and fill it with a color.
        # This could also be an image loaded from the disk.
        if choice == 0:
            self.image = utilities.load_image('green_balloon.png')
            self.floatspeed = 1
            self.AWARD = 5
        elif choice == 1:
            self.image = utilities.load_image('blue_balloon.png')
            self.floatspeed = 1.5
            self.AWARD = 7
        elif choice == 2:
            self.image = utilities.load_image('red_balloon.png')
            self.floatspeed = 2
            self.AWARD = 10
        self.image = pygame.transform.scale(self.image, (15, 30))
        self.image.set_colorkey(colors.WHITE)

        # Fetch the rectangle object that has the dimensions of the image
        # Update the position of this object by setting the values of rect.x and rect.y
        self.rect = self.image.get_rect()
        self.rect.y = top
        self.rect.x = screenWidth
        self.lives = 1

    def update(self):
        self.y += min(-0.1, np.random.normal(-self.floatspeed, 0.5))
        # move upwards
        self.rect.y = int(self.y)
        self.rect.x -= Wall.SPEED

        # balloon is off-screen
        if self.rect.y < -self.rect.h:
            self.kill()

    def hurt(self):
        Enemy.hurt(self)
        if self.dead():
            pygame.mixer.Sound.play(self.pop_sound)


class Powerup(utilities.DrawSprite):
    SIDE_LENGTH = 15  # length of side
    DEFAULT_LOOP_TIME = 2  # time to loop through shades
    DEFAULT_AMMO = np.inf  # default ammo of powerup
    DEFAULT_DURATION = np.inf  # default duration of powerup

    def __init__(self, top, type):
        # Call the parent class (Sprite) constructor
        utilities.DrawSprite.__init__(self)

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
        elif type == PowerupType.ONE_UP:
            self.color = colors.GREEN

        self.timeLeft = self.duration
        self.startTimeLeft = self.timeLeft

    def update(self):
        T = (time.time() - self.lastLoop)
        color = np.array(self.color)
        if T > self.DEFAULT_LOOP_TIME:
            self.lastLoop = time.time()
        t = T / self.DEFAULT_LOOP_TIME
        # find the shade of the color using a linear seesaw
        color = utilities.seesaw(0.7 * color, color, t)
        self.image.fill(color)
        self.rect.left -= Wall.SPEED

