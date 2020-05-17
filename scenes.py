import pygame
import utilities
import geometry as geo
import colors
import numpy as np
import time
from copter import *
from driving import *

class SceneBase:
    def __init__(self):
        self.next = self
        self.initialized = False

    # only needs to be called once throughout main loop
    def initGraphics(self, screen):
        self.screen = screen
        self.initialized = True

    def ProcessInput(self, events, pressed_keys):
        print("uh-oh, you didn't override this in the child class")

    def Update(self):
        print("uh-oh, you didn't override this in the child class")

    def Render(self):
        print("uh-oh, you didn't override this in the child class")

    def SwitchToScene(self, next_scene):
        self.next = next_scene

    def Terminate(self):
        self.SwitchToScene(None)


class CopterScene(SceneBase):
    GAP_FRACTION = 0.7 # the starting fraction of gap space
    GAP_CLEARANCE = 0.05 # how much clearance the gap has between screen borders
    FLUCTUATION = 3 # how much the gap position fluctuates
    NARROWING_INTERVAL = 5 # how long before the gap narrows
    FLUCTUATION_INTERVAL = 5 # how long before gap increases fluctuation
    MAX_FLUCTUATION = 15 # maximum amount of fluctuation
    BAT_RESPAWN_TIME = 10 # interval between bats


    def __init__(self):
        SceneBase.__init__(self)
        self.v = geo.Vector2D.zero()
        self.a = geo.Vector2D(0, 1)
        self.fly = False
        self.rng = np.random.default_rng()
        self.starttime = time.time()
        self.lastnarrow = self.starttime
        self.lastfluct = self.starttime
        self.highscore = self.loadScore('score.save')
        self.projectiles = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        self.score = 0
        self.timeOfLastAdd = {}
        self.timeOfLastAdd['bats'] = self.starttime

    def initGraphics(self, screen):
        SceneBase.initGraphics(self, screen)

        info = pygame.display.Info()
        screenWidth, screenHeight = info.current_w, info.current_h

        self.copter = Copter([screenWidth / 4, screenHeight / 2])

        # generate walls
        self.gap_height = self.GAP_FRACTION * screenHeight
        self.gap_pos = self.rng.random() \
            * (screenHeight * (1 - 2 * self.GAP_CLEARANCE - self.GAP_FRACTION)) \
            + screenHeight * (self.GAP_CLEARANCE + 0.5 * self.GAP_FRACTION)

        self.walls = pygame.sprite.Group()

        for i in range(int(np.ceil(screenWidth/Wall.WIDTH))+2):
            self.gap_pos += self.FLUCTUATION * self.rng.standard_normal()
            self.gap_pos = min(max(self.gap_pos, self.gap_height/2 + self.GAP_CLEARANCE * screenHeight),
                               (1 - self.GAP_CLEARANCE) * screenHeight - self.gap_height/2)
            top = Wall(0, round(self.gap_pos - self.gap_height/2))
            bottom = Wall(round(self.gap_pos + self.gap_height/2), screenHeight - round(self.gap_pos + self.gap_height/2))
            top.rect.left = i*Wall.WIDTH
            bottom.rect.left = i*Wall.WIDTH
            self.walls.add(top)
            self.walls.add(bottom)

        self.scoreText = pygame.font.Font('freesansbold.ttf', 20)
        self.highscoreText = pygame.font.Font('freesansbold.ttf', 12)

    def ProcessInput(self, events, pressed_keys):
        for event in events:
            if event.type == pygame.KEYDOWN:
                alt_pressed = pressed_keys[pygame.K_LALT] or \
                              pressed_keys[pygame.K_RALT]
                if event.key == pygame.K_p:
                    self.SwitchToScene(Pause(self))

    def Update(self):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        spacebar = pygame.key.get_pressed()[pygame.K_SPACE]
        self.score = time.time() - self.starttime

        # check if spacebar
        self.fly = spacebar

        info = pygame.display.Info()
        screenWidth, screenHeight = info.current_w, info.current_h

        # fly logic
        if self.fly:
            self.a = geo.Vector2D(0, -1)
        else:
            self.a = geo.Vector2D(0, 1)

        self.v += self.a
        self.copter.rect.move_ip(*self.v)

        # if ceiling is hit
        if self.copter.rect.top < 0:
            self.EndGame()

        # if floor is hit
        if self.copter.rect.bottom > screenHeight:
            self.EndGame()

        for hit_list in pygame.sprite.spritecollide(self.copter, self.walls,
                                                    False, collided=pygame.sprite.collide_rect):
            self.EndGame()
            break

        for hit_list in pygame.sprite.spritecollide(self.copter, self.obstacles,
                                                    False, collided=pygame.sprite.collide_rect):
            self.EndGame()
            break

        for wall in self.walls:
            if wall.rect.right < 0:
                wall.kill()

                # generate new wall
                if wall.rect.top == 0:
                    if (time.time() - self.lastnarrow) >= self.NARROWING_INTERVAL:
                        self.gap_height = max(0.95 * self.gap_height, 3 * self.copter.rect.height)
                        self.lastnarrow = time.time()
                    if (time.time() - self.lastfluct) >= self.FLUCTUATION_INTERVAL:
                        self.FLUCTUATION = min(self.FLUCTUATION + 1, self.MAX_FLUCTUATION)
                        self.lastfluct = time.time()
                    self.gap_pos += self.FLUCTUATION * self.rng.standard_normal()
                    self.gap_pos = min(max(self.gap_pos, self.gap_height/2 + self.GAP_CLEARANCE * screenHeight),
                                       (1 - self.GAP_CLEARANCE) * screenHeight - self.gap_height/2)
                    new = Wall(0, round(self.gap_pos - self.gap_height/2))
                else:
                    new = Wall(round(self.gap_pos + self.gap_height/2), screenHeight - round(self.gap_pos + self.gap_height/2))
                self.walls.add(new)

        self.walls.update()

        # add obstacles
        self.addObstacles()
        self.obstacles.update()
        for ob in self.obstacles:
            # if obstacle flies off-screen, delete it
            if ob.rect.left > screenWidth \
                    or ob.rect.right < 0 \
                    or ob.rect.top > screenHeight \
                    or ob.rect.bottom < 0:
                ob.kill()

        if click[0]:
            if self.copter.weapon == Weapon.MACHINE_GUN:
                if time.time() - self.copter.lastShootTime > self.copter.MACHINE_GUN_RELOAD_TIME:
                    dr = geo.Vector2D(*mouse) - geo.Vector2D(*self.copter.rect.center)
                    self.copter.angle = (np.degrees(geo.Vector2D.angle_between(dr, geo.Vector2D(1, 0))))
                    bullet = self.copter.shoot()

                    self.projectiles.add(bullet)

        for p in self.projectiles:
            # if projectile flies off-screen
            if p.rect.left > screenWidth \
                    or p.rect.right < 0 \
                    or p.rect.top > screenHeight \
                    or p.rect.bottom < 0:
                p.kill()

            self.checkProjectileHit(p)

        self.projectiles.update()

    def Render(self):
        self.screen.fill((255, 255, 255))
        self.copter.draw(self.screen)
        self.obstacles.draw(self.screen)
        self.walls.draw(self.screen)
        self.projectiles.draw(self.screen)

        scoreSurf = self.scoreText.render("Time: {0:.2f}".format(self.score), True, (0, 0, 0))
        scoreRect = scoreSurf.get_rect()
        scoreRect.left, scoreRect.top = 50, 50
        self.screen.blit(scoreSurf, scoreRect)

        scoreSurf = self.highscoreText.render("High-score: {0:.2f}".format(self.highscore), True, (0, 0, 0))
        scoreRect = scoreSurf.get_rect()
        scoreRect.left, scoreRect.top = 50, 75
        self.screen.blit(scoreSurf, scoreRect)

        self.drawCrossHairs()

        pygame.display.flip()

    def drawCrossHairs(self):
        mouse = pygame.mouse.get_pos()
        pressed = pygame.mouse.get_pressed()

        offset = 5
        length = 10
        if pressed[0]:
            pygame.draw.line(self.screen, colors.RED, (mouse[0], mouse[1] - offset), (mouse[0], mouse[1] - length))
            pygame.draw.line(self.screen, colors.RED, (mouse[0], mouse[1] + offset), (mouse[0], mouse[1] + length))
            pygame.draw.line(self.screen, colors.RED, (mouse[0] - offset, mouse[1]), (mouse[0] - length, mouse[1]))
            pygame.draw.line(self.screen, colors.RED, (mouse[0] + offset, mouse[1]), (mouse[0] + length, mouse[1]))
        else:
            pygame.draw.line(self.screen, colors.BLACK, (mouse[0], mouse[1] - offset), (mouse[0], mouse[1] - length))
            pygame.draw.line(self.screen, colors.BLACK, (mouse[0], mouse[1] + offset), (mouse[0], mouse[1] + length))
            pygame.draw.line(self.screen, colors.BLACK, (mouse[0] - offset, mouse[1]), (mouse[0] - length, mouse[1]))
            pygame.draw.line(self.screen, colors.BLACK, (mouse[0] + offset, mouse[1]), (mouse[0] + length, mouse[1]))

    def EndGame(self):
        if self.score > self.highscore:
                self.saveScore('score.save')
        self.SwitchToScene(Start())

    def saveScore(self, filename):
        with open(filename, 'w') as f:
            f.write("High-score,{0:.2f}".format(time.time()-self.starttime))

    def loadScore(self, filename):
        try:
            with open(filename, 'r') as f:
                scoreline = f.readline()
                score = scoreline.split(',')[1]
        except:
            score = 0
            print("No save data found.")

        return float(score)

    def checkProjectileHit(self, projectile):
        collided_objects = pygame.sprite.spritecollide(projectile, self.walls, False, collided=pygame.sprite.collide_rect)
        for obj in collided_objects:
            # self.explosions.append((projectile.explode(), projectile.pos()))
            projectile.kill()

        collided_objects = pygame.sprite.spritecollide(projectile, self.obstacles, True, collided=pygame.sprite.collide_rect)
        for obj in collided_objects:
            # self.explosions.append((projectile.explode(), projectile.pos()))
            projectile.kill()

            if type(obj) is Bat:
                self.starttime -= 5

    def addObstacles(self):
        if time.time() - self.timeOfLastAdd['bats'] > self.BAT_RESPAWN_TIME:
            self.BAT_RESPAWN_TIME *= 0.95
            roof, ground = self.gap_pos - self.gap_height/2, self.gap_pos + self.gap_height/2
            y = self.rng.random()*0.8*self.gap_height + 0.1*roof
            bat = Bat(y, Wall.SPEED*1.2)
            self.obstacles.add(bat)
            self.timeOfLastAdd['bats'] = time.time()


class Start(SceneBase):
    def __init__(self):
        SceneBase.__init__(self)

        self.options = ['Drive', 'Copter', 'Quit']
        self.buttons = pygame.sprite.Group()

    def initGraphics(self, screen):
        SceneBase.initGraphics(self, screen)

        info = pygame.display.Info()
        screenWidth, screenHeight = info.current_w, info.current_h

        font = pygame.font.Font('freesansbold.ttf', 20)

        for i, option in enumerate(self.options):
            rect = pygame.Rect(int(screenWidth/2) - 50, int(screenHeight/2) - 100 + i*50, 100, 30)
            passive_color = colors.BLACK
            active_color = colors.RED

            if i == 0:
                def action():
                    self.SwitchToScene(DrivingScene())
            elif i == 1:
                def action():
                    self.SwitchToScene(CopterScene())
            else:
                def action():
                    self.Terminate()

            button = Button(rect, action, font, active_color, option, colors.WHITE, passive_color, option, colors.WHITE)

            self.buttons.add(button)

    def ProcessInput(self, events, pressed_keys):
        pass

    def Update(self):
        self.buttons.update()

    def Render(self):
        self.screen.fill(colors.WHITE)
        self.buttons.draw(self.screen)
        pygame.display.flip()


class Button(pygame.sprite.Sprite):
    def __init__(self, rect, action, font, active_color, active_text, active_textcolor, passive_color, passive_text, passive_textcolor):
        # Call the parent class (Sprite) constructor
        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.Surface((rect[2], rect[3]))

        self.rect = rect

        self.font = font

        self.action = action

        self.active_color = active_color
        self.active_text = active_text
        self.active_textcolor = active_textcolor
        self.passive_color = passive_color
        self.passive_text = passive_text
        self.passive_textcolor = passive_textcolor

    def update(self):
        mouse = pygame.mouse.get_pos()
        pressed = pygame.mouse.get_pressed()

        if self.rect.x <= mouse[0] <= self.rect.x + self.rect.w and self.rect.y <= mouse[1] <= self.rect.y + self.rect.h:
            self.image.fill(self.active_color)
            self.renderButtonText(self.active_text, self.active_textcolor)

            if pressed[0]:
                self.action()
        else:
            self.image.fill(self.passive_color)
            self.renderButtonText(self.passive_text, self.passive_textcolor)

    def renderButtonText(self, text, color):
        textsurf = self.font.render(text, True, color)
        textrect = textsurf.get_rect()
        # Put text in the middle of button
        textrect.left = self.rect.width/2 - textrect.width/2
        textrect.top = self.rect.height/2 - textrect.height/2
        self.image.blit(textsurf, textrect)


class DrivingScene(SceneBase):
    POWERUP_DURATION = 2
    DEFAULT_MAX_FWD_SPEED = 10
    DEFAULT_MAX_REV_SPEED = 5

    def __init__(self):
        SceneBase.__init__(self)

    # only needs to be called once throughout main loop
    def initGraphics(self, screen):
        SceneBase.initGraphics(self, screen)

        info = pygame.display.Info()
        screenWidth, screenHeight = info.current_w, info.current_h

        self.car = Car((10, screenHeight/2))
        self.powerups = pygame.sprite.Group()
        boost = SpeedBoost([50, 15])
        self.powerups.add(boost)

        self.terrain = pygame.sprite.Group()
        mid_grass = Grass((screenWidth//2, screenHeight//2), 0.8 * screenWidth, 0.8 * screenHeight)
        self.terrain.add(mid_grass)
        mid_barrier = Barrier((screenWidth//2, screenHeight//2), 0.75 * screenWidth, 0.75 * screenHeight)
        self.terrain.add(mid_barrier)

        finishline = FinishLine((0, screenHeight/2), 0.1 * screenWidth, 10)
        self.terrain.add(finishline)

    def ProcessInput(self, events, pressed_keys):
        for event in events:
            if event.type == pygame.KEYDOWN:
                alt_pressed = pressed_keys[pygame.K_LALT] or \
                              pressed_keys[pygame.K_RALT]
                if event.key == pygame.K_SPACE or event.key == pygame.K_p:
                    self.SwitchToScene(Pause(self))

    def Update(self):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()

        info = pygame.display.Info()
        screenWidth, screenHeight = info.current_w, info.current_h


        currentPos = geo.Vector2D(*mouse)
        dr = currentPos - self.car.pos()

        # follow mouse drag
        if click[0]:
            self.car.angle = dr.angle()
            self.car.acceleration = 1
            self.car.max_speed = min(self.car.MAX_FWD_SPEED, dr.length()/5)
        elif click[2]:
            self.car.angle = dr.angle()
            self.car.acceleration = -1
        else:
            if self.car.speed > 0:
                self.car.acceleration = -1
            else:
                self.car.acceleration = 0
                self.car.speed = 0

        powerupsHit = pygame.sprite.spritecollide(self.car, self.powerups, True,
                                                  collided=pygame.sprite.collide_rect)
        for p in powerupsHit:
            if type(p) is SpeedBoost:
                self.car.MAX_FWD_SPEED = self.car.BOOST_FWD_SPEED
                self.car.MAX_REV_SPEED = self.car.BOOST_REV_SPEED
                self.car.lastPowerupTime = time.time()

        if time.time() - self.car.lastPowerupTime > self.POWERUP_DURATION:
            self.car.MAX_FWD_SPEED = self.car.DEFAULT_MAX_FWD_SPEED
            self.car.MAX_REV_SPEED = self.car.DEFAULT_MAX_REV_SPEED

        if self.car.rect.top < 0:
            self.car.rect.top = 0
        if self.car.rect.bottom > screenHeight:
            self.car.rect.bottom = screenHeight
        if self.car.rect.left < 0:
            self.car.rect.left = 0
        if self.car.rect.right > screenWidth:
            self.car.rect.right = screenWidth

        terrainHit = pygame.sprite.spritecollide(self.car, self.terrain, False,
                                                 collided=pygame.sprite.collide_rect)

        for terrain in terrainHit:
            if type(terrain) is Grass:
                self.car.MAX_FWD_SPEED = 5
                self.car.MAX_REV_SPEED = 5
            elif type(terrain) is Barrier:
                if self.car.rect.bottom > terrain.rect.top and self.car.rect.top < terrain.rect.bottom \
                    and (self.car.rect.right <= terrain.rect.left + self.car.v.x or self.car.rect.left >= terrain.rect.right + self.car.v.x):
                    if self.car.v.x > 0:
                        self.car.rect.right = terrain.rect.left
                    if self.car.v.x < 0:
                        self.car.rect.left = terrain.rect.right
                if self.car.rect.right > terrain.rect.left and self.car.rect.left < terrain.rect.right \
                    and (self.car.rect.bottom <= terrain.rect.top + self.car.v.y or self.car.rect.top >= terrain.rect.bottom + self.car.v.y):
                    if self.car.v.y > 0:
                        self.car.rect.bottom = terrain.rect.top
                    if self.car.v.y < 0:
                        self.car.rect.top = terrain.rect.bottom

        self.powerups.update()
        self.car.update()
        self.terrain.update()

    def Render(self):
        self.screen.fill(colors.GRAY)
        self.terrain.draw(self.screen)
        self.powerups.draw(self.screen)
        self.car.draw(self.screen)

        self.drawCrossHairs()

        pygame.display.flip()

    def drawCrossHairs(self):
        mouse = pygame.mouse.get_pos()
        pressed = pygame.mouse.get_pressed()

        offset = 5
        length = 10
        if pressed[0]:
            pygame.draw.line(self.screen, colors.GREEN, (mouse[0], mouse[1] - offset), (mouse[0], mouse[1] - length))
            pygame.draw.line(self.screen, colors.GREEN, (mouse[0], mouse[1] + offset), (mouse[0], mouse[1] + length))
            pygame.draw.line(self.screen, colors.GREEN, (mouse[0] - offset, mouse[1]), (mouse[0] - length, mouse[1]))
            pygame.draw.line(self.screen, colors.GREEN, (mouse[0] + offset, mouse[1]), (mouse[0] + length, mouse[1]))
        elif pressed[2]:
            pygame.draw.line(self.screen, colors.RED, (mouse[0], mouse[1] - offset), (mouse[0], mouse[1] - length))
            pygame.draw.line(self.screen, colors.RED, (mouse[0], mouse[1] + offset), (mouse[0], mouse[1] + length))
            pygame.draw.line(self.screen, colors.RED, (mouse[0] - offset, mouse[1]), (mouse[0] - length, mouse[1]))
            pygame.draw.line(self.screen, colors.RED, (mouse[0] + offset, mouse[1]), (mouse[0] + length, mouse[1]))
        else:
            pygame.draw.line(self.screen, colors.BLACK, (mouse[0], mouse[1] - offset), (mouse[0], mouse[1] - length))
            pygame.draw.line(self.screen, colors.BLACK, (mouse[0], mouse[1] + offset), (mouse[0], mouse[1] + length))
            pygame.draw.line(self.screen, colors.BLACK, (mouse[0] - offset, mouse[1]), (mouse[0] - length, mouse[1]))
            pygame.draw.line(self.screen, colors.BLACK, (mouse[0] + offset, mouse[1]), (mouse[0] + length, mouse[1]))



class Pause(SceneBase):
    def __init__(self, paused):
        SceneBase.__init__(self)
        self.next = self
        self.paused = paused
        self.options = ["Resume", "Quit"]
        self.buttons = pygame.sprite.Group()

    # only needs to be called once throughout main loop
    def initGraphics(self, screen):
        SceneBase.initGraphics(self, screen)
        self.pauseText = pygame.font.Font('freesansbold.ttf', 25)
        font = pygame.font.Font('freesansbold.ttf', 20)

        info = pygame.display.Info()
        screenWidth, screenHeight = info.current_w, info.current_h

        for i, option in enumerate(self.options):
            rect = pygame.Rect(int(screenWidth/2) - 50, int(screenHeight/2) + i*50, 100, 30)
            passive_color = colors.BLACK
            active_color = colors.RED

            if i == 0:
                def action():
                    self.SwitchToScene(self.paused)
                    self.paused.next = self.paused
            else:
                def action():
                    self.SwitchToScene(Start())

            button = Button(rect, action, font, active_color, option, colors.WHITE, passive_color, option, colors.WHITE)

            self.buttons.add(button)

    def ProcessInput(self, events, pressed_keys):
        for event in events:
            if event.type == pygame.KEYDOWN:
                alt_pressed = pressed_keys[pygame.K_LALT] or \
                              pressed_keys[pygame.K_RALT]
                if event.key == pygame.K_p:
                    self.SwitchToScene(self.paused)
                    self.paused.next = self.paused


    def Update(self):
        self.buttons.update()

    def Render(self):
        self.screen.fill(colors.WHITE)
        self.screen.set_alpha(100)

        info = pygame.display.Info()
        screenWidth, screenHeight = info.current_w, info.current_h
        promptSurf = self.pauseText.render("PAUSED", True, (0, 0, 0))
        promptRect = promptSurf.get_rect()
        promptRect.center = screenWidth/2, 50
        self.screen.blit(promptSurf, promptRect)

        self.buttons.draw(self.screen)
        pygame.display.flip()
