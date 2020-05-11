import pygame
import utilities
import geometry as geo
import colors
import numpy as np
from copter import *
import time

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
        pass

    def Update(self):
        click = pygame.mouse.get_pressed()[0]
        spacebar = pygame.key.get_pressed()[pygame.K_SPACE]

        # check if spacebar/mouse
        self.fly = spacebar or click

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

    def Render(self):
        self.screen.fill((255, 255, 255))
        self.copter.draw(self.screen)
        self.walls.draw(self.screen)

        scoreSurf = self.scoreText.render("Time: {0:.2f}".format((time.time() - self.starttime)), True, (0, 0, 0))
        scoreRect = scoreSurf.get_rect()
        scoreRect.left, scoreRect.top = 50, 50
        self.screen.blit(scoreSurf, scoreRect)

        scoreSurf = self.highscoreText.render("High-score: {0:.2f}".format(self.highscore), True, (0, 0, 0))
        scoreRect = scoreSurf.get_rect()
        scoreRect.left, scoreRect.top = 50, 75
        self.screen.blit(scoreSurf, scoreRect)


        pygame.display.flip()

    def EndGame(self):
        dt = time.time() - self.starttime
        if dt > self.highscore:
                self.saveScore('score.save')
                self.highscore = dt
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


class Start(SceneBase):
    def __init__(self):
        SceneBase.__init__(self)

        self.options = ['Start', 'Quit']
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


