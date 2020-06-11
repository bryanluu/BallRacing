import pygame
import utilities
import colors
import numpy as np
from enum import Enum
import time
import geometry as geo


class PowerupType(Enum):
    SPEED_BOOST = 0  # grants moderate speed boost
    SLOWDOWN = 1  # slows max speed
    RANDOMIZER = 2  # randomizes speed
    POWER_WHEELS = 3  # terrain has no effect on speed
    REVERSER = 4  # wheels go in reverse direction
    CONTROLLED_BOOST = 5  # a controlled boost
    NUMBER_POWERUPS = 6  # number of valid powerups


class Car(pygame.sprite.Sprite):
    MAX_FWD_SPEED = 7
    MAX_REV_SPEED = 5
    DEFAULT_MAX_FWD_SPEED = 7
    DEFAULT_MAX_REV_SPEED = 5
    BOOST_FWD_SPEED = 12
    BOOST_REV_SPEED = 7
    SLOWED_FWD_SPEED = 4
    SLOWED_REV_SPEED = 4
    MAX_RANDOM_SPEED = 15
    MIN_RANDOM_SPEED = 5
    RANDOM_SPREAD = 3
    TRAIL_LENGTH = 10

    def __init__(self, pos, color, isCPU=False):
        pygame.sprite.Sprite.__init__(self)

        # initialize RNG for randomizer
        self.rng = np.random.default_rng()
        self.color = color

        self.car_img = utilities.load_image("car.png", -1)
        self.car_img = pygame.transform.scale(self.car_img, (30, 15))
        pygame.transform.threshold(self.car_img, self.car_img,
                                    colors.WHITE, set_color=self.color,
                                    threshold=(1,1,1,0), inverse_set=True)
        self.image = self.car_img.copy()

        self.rect = self.image.get_rect()
        self.rect.center = pos

        self.isCPU = isCPU  # whether the car is computer controlled

        self.angle = -np.pi/2
        self.speed = 0
        self.maxSpeed = self.MAX_FWD_SPEED
        self.acceleration = 0
        self.v = geo.Vector2D.create_from_angle(self.angle,
                                                self.speed)  # angle in radians

        self.lastPowerupTime = 0
        self.power = None
        self.slowed = False
        self.trail = []
        self.powerActive = False

        self.checkpoint = 0
        self.laps = 0

    def draw(self, screen):
        # draw trail
        if len(self.trail) > 1:
            pygame.draw.aalines(screen, self.power.color, False, self.trail)

        if(self.hasPower()):
            # find the shade of the color using a linear ramp
            color = np.array(self.power.color)
            color = (1 - 0.3 * (self.power.duration
                                - self.power.timeLeft)
                                / self.power.duration) * color
            self.power.image.fill(color)

            # draw powerup on car
            self.power.rect.center = [self.rect.width / 2,
                                      self.rect.height / 2]
            self.image.blit(self.power.image, self.power.rect)

        # rotate car using angle in degrees and draw car
        image = pygame.transform.rotate(self.image,
                                        np.degrees(-self.angle))
        screen.blit(image, self.rect)

    def update(self):
        # powerup logic
        if self.powerActive:
            timeSpentActivated = time.time() - self.lastPowerupTime
            self.power.timeLeft = self.power.startTimeLeft - timeSpentActivated
            if self.power.timeLeft <= 0:
                self.deactivatePower()
                self.removePower()
        if self.hasPower() and self.power.timeLeft <= 0:
            self.removePower()

        # speed logic
        if self.powerActive \
            and (self.hasPower(PowerupType.SPEED_BOOST)
            or self.hasPower(PowerupType.CONTROLLED_BOOST)):
            if not self.slowed:
                self.MAX_FWD_SPEED = self.BOOST_FWD_SPEED
                self.MAX_REV_SPEED = self.BOOST_REV_SPEED
            else:
                self.MAX_FWD_SPEED = self.DEFAULT_MAX_FWD_SPEED
                self.MAX_REV_SPEED = self.DEFAULT_MAX_REV_SPEED
        elif self.powerActive and self.hasPower(PowerupType.RANDOMIZER):
            if not self.slowed:
                # randomize speed according to a standard normal
                self.MAX_FWD_SPEED = utilities.bound(self.MIN_RANDOM_SPEED,
                                                     self.rng.standard_normal()
                                                     * self.RANDOM_SPREAD
                                                     + self.MAX_FWD_SPEED,
                                                     self.MAX_RANDOM_SPEED)
                self.MAX_REV_SPEED = self.BOOST_REV_SPEED
            else:
                self.MAX_FWD_SPEED = self.SLOWED_FWD_SPEED
                self.MAX_REV_SPEED = self.SLOWED_REV_SPEED
        elif self.powerActive and self.hasPower(PowerupType.POWER_WHEELS):
            self.MAX_FWD_SPEED = self.DEFAULT_MAX_FWD_SPEED
            self.MAX_REV_SPEED = self.DEFAULT_MAX_REV_SPEED
        else:
            if self.slowed or (self.powerActive and self.hasPower(PowerupType.SLOWDOWN)):
                self.MAX_FWD_SPEED = self.SLOWED_FWD_SPEED
                self.MAX_REV_SPEED = self.SLOWED_REV_SPEED
            else:
                self.MAX_FWD_SPEED = self.DEFAULT_MAX_FWD_SPEED
                self.MAX_REV_SPEED = self.DEFAULT_MAX_REV_SPEED

        if self.powerActive and self.hasPower():
            self.trail.append([self.rect.center[0], self.rect.center[1]])
            while (len(self.trail) > self.TRAIL_LENGTH):
                self.trail.pop(0)
        else:
            self.trail = []

        # driving logic
        self.speed = max(-self.MAX_REV_SPEED,
                         min(self.maxSpeed, self.speed + self.acceleration))
        self.v = geo.Vector2D.create_from_angle(self.angle,
                                                self.speed)  # angle in radians
        self.rect.move_ip(*self.v)

    def pos(self):
        return geo.Vector2D(*self.rect.center)

    def driveTowards(self, dest):
        dr = dest - self.pos()
        self.angle = dr.angle()  # angle in radians

        if self.powerActive and self.hasPower(PowerupType.REVERSER):
            self.acceleration = -1
        else:
            self.acceleration = 1

        self.maxSpeed = min(self.MAX_FWD_SPEED, dr.length() / 5)

    def driveAwayFrom(self, point):
        dr = point - self.pos()
        self.angle = dr.angle()  # angle in radians

        if self.powerActive and self.hasPower(PowerupType.REVERSER):
            self.acceleration = 1
        else:
            self.acceleration = -1

        self.maxSpeed = min(self.MAX_REV_SPEED, dr.length() / 5)

    def idle(self):
        if self.speed > 0:
            self.acceleration = -1
        else:
            self.acceleration = 0
            self.speed = 0

    # checks if the car has a power if none given, or else the given powertype
    def hasPower(self, type=None):
        if type is None:
            return self.power
        else:
            return self.power and self.power.type == type

    # activates powerup if the car has one
    def activatePower(self):
        if self.hasPower():
            self.powerActive = True
            self.lastPowerupTime = time.time()
            self.power.startTimeLeft = self.power.timeLeft

    # deactivates powerup if the car has one
    def deactivatePower(self):
        if self.hasPower(PowerupType.CONTROLLED_BOOST):
            self.powerActive = False
        else:
            return  # don't allow activation externally for now

    # gives power to car
    def givePower(self, power):
        self.power = power
        if self.isCPU:
            self.activatePower()
        elif power.type == PowerupType.SLOWDOWN:
            self.activatePower()
        elif power.type == PowerupType.REVERSER:
            self.activatePower()
        elif power.type == PowerupType.SPEED_BOOST:
            self.activatePower()

    # removes power from car
    def removePower(self):
        self.image = self.car_img.copy()
        self.power = None
        self.powerActive = False


class Powerup(pygame.sprite.Sprite):
    DEFAULT_LOOP_TIME = 2  # default time that the powerup loops through types
    DEFAULT_LOOP_SPREAD = 0.5  # spread of loop times
    MIN_LOOP_TIME = 0.5  # minimum loop time
    MAX_LOOP_TIME = 3.5 # maximum loop time
    DEFAULT_DURATION = 2  # time that the powerup lasts for

    def __init__(self, pos, type, switch=True):
        pygame.sprite.Sprite.__init__(self)

        # initialize RNG for randomizer
        self.rng = np.random.default_rng()

        self.rect = pygame.Rect(0, 0, 10, 10)
        self.rect.center = pos

        self.image = pygame.Surface([10, 10])
        self.switchTo(type)
        self.switch = switch
        self.lastLoop = time.time()

    def update(self):
        t = time.time() - self.lastLoop
        color = np.array(self.color)
        if (t > self.loopTime):
            if self.switch:
                newType = PowerupType(int(self.rng.random() * PowerupType.NUMBER_POWERUPS.value))
                self.switchTo(newType)
                self.loopTime = utilities.bound(self.MIN_LOOP_TIME,
                                                 self.loopTime + self.rng.standard_normal() * self.loopSpread,
                                                 self.MAX_LOOP_TIME)
            self.lastLoop = time.time()

        else:
            # find the shade of the color using a linear seesaw
            color = (1-0.3*(1-abs(t-self.loopTime/2)/(self.loopTime/2)))*color
        self.image.fill(color)

    # switch powerup type
    def switchTo(self, type):
        self.type = type
        self.duration = self.DEFAULT_DURATION
        self.loopTime = self.DEFAULT_LOOP_TIME
        self.loopSpread = self.DEFAULT_LOOP_SPREAD

        if type == PowerupType.SPEED_BOOST:
            self.color = colors.GREEN
        elif type == PowerupType.SLOWDOWN:
            self.color = colors.YELLOW
        elif type == PowerupType.RANDOMIZER:
            self.color = colors.PURPLE
            self.duration = 1.5 * self.DEFAULT_DURATION
        elif type == PowerupType.POWER_WHEELS:
            self.color = colors.BLUE
            self.duration = 2 * self.DEFAULT_DURATION
        elif type == PowerupType.REVERSER:
            self.color = colors.RED
            self.loopTime = self.DEFAULT_LOOP_TIME / 2  # half as likely
            self.loopSpread = self.DEFAULT_LOOP_SPREAD / 2
        elif type == PowerupType.CONTROLLED_BOOST:
            self.color = colors.ORANGE
            self.duration = self.DEFAULT_DURATION / 2
            self.loopTime = self.DEFAULT_LOOP_TIME * 0.8
        else:
            raise Exception("Invalid powerup!")

        self.timeLeft = self.duration
        self.startTimeLeft = self.timeLeft

    def draw(self, screen):
        screen.blit(self.image, self.rect)

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
        self.image.fill(colors.DARK_GRAY)


class Checkpoint(pygame.sprite.Sprite):
    POWERUP_SPAWN_INTERVAL = 5  # mean time between powerup spawns
    POWERUP_SPAWN_RADIUS = 20  # max radius to spawn powerups over

    def __init__(self, pos, width, height, generatesPowerups=False):
        pygame.sprite.Sprite.__init__(self)

        # Random Number Generator
        self.rng = np.random.default_rng()

        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = pos
        self.image = pygame.Surface([width, height])
        # self.image.fill(colors.YELLOW) # uncomment to debug
        self.generatesPowerups = generatesPowerups
        self.powerup = None
        self.timeUntilGeneration = self.rng.exponential(self.POWERUP_SPAWN_INTERVAL)
        self.lastUpdateTime = time.time()

    def update(self):
        if self.generatesPowerups and self.powerup is None:
            if self.timeUntilGeneration <= 0:
                self.generatePowerup()
            else:
                now = time.time()
                self.timeUntilGeneration = self.timeUntilGeneration - (now - self.lastUpdateTime)
                self.lastUpdateTime = now

    # pops the stored powerup
    def getPowerup(self):
        powerup = self.powerup
        self.powerup = None
        return powerup

    # generates a powerup
    def generatePowerup(self):
        spawnPoint = geo.Vector2D(*self.rect.center)
        spawnPoint += geo.Vector2D.create_from_angle(self.rng.random() * 2 * np.pi,
                                                     self.rng.random() * self.POWERUP_SPAWN_RADIUS)
        self.powerup = Powerup(spawnPoint.tuple(),
                               PowerupType(int(self.rng.random() * PowerupType.NUMBER_POWERUPS.value)))
        self.timeUntilGeneration = self.rng.exponential(self.POWERUP_SPAWN_INTERVAL)


class FinishLine(Checkpoint):
    def __init__(self, pos, width, height, horizontal=True):
        Checkpoint.__init__(self, pos, width, height)

        self.horizontal = horizontal

        for i in range(8):
            for j in range(2):
                if horizontal:
                    w, h = width / 8, height / 2
                else:
                    w, h = width / 2, height / 8

                rect = pygame.Rect(i * w, j * h, w, h)
                surf = pygame.Surface([w, h])
                if (i + j) % 2 == 0:
                    surf.fill(colors.BLACK)
                else:
                    surf.fill(colors.WHITE)
                self.image.blit(surf, rect)
