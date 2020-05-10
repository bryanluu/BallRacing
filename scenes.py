import pygame
import utilities
import geometry as geo
import math, random
import time
import colors

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


class BallScene(SceneBase):
    def __init__(self):
        SceneBase.__init__(self)
        self.v = geo.Vector2D.zero()
        self.a = geo.Vector2D(0, 1)
        self.elasticity = 0.8
        self.friction = 0.1

    def initGraphics(self, screen):
        SceneBase.initGraphics(self, screen)

        self.ball = utilities.load_image('ball.png')
        self.ballrect = self.ball.get_rect()
        self.ballrect.left, self.ballrect.top = 0, 0

    def ProcessInput(self, events, pressed_keys):
        pass

    def Update(self):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()

        info = pygame.display.Info()
        screenWidth, screenHeight = info.current_w, info.current_h

        # follow mouse drag
        if click[0]:
            currentPos = geo.Vector2D(*mouse)
            self.v = currentPos - self.lastPos
            self.lastPos = currentPos
            self.ballrect.center = mouse
            if self.ballrect.left < 0:
                self.ballrect.left = 0
            if self.ballrect.right > screenWidth:
                self.ballrect.right = screenWidth
            if self.ballrect.top < 0:
                self.ballrect.top = 0
            if self.ballrect.bottom > screenHeight:
                self.ballrect.bottom = screenHeight
        else:
            self.lastPos = geo.Vector2D(*mouse)
            self.v += self.a
            self.ballrect.move_ip(*self.v)
            if self.ballrect.left < 0:
                self.v.x = -self.v.x * self.elasticity
                self.ballrect.left = 0
            if self.ballrect.right > screenWidth:
                self.v.x = -self.v.x * self.elasticity
                self.ballrect.right = screenWidth
            if self.ballrect.top < 0:
                self.v.y = -self.v.y * self.elasticity
                self.ballrect.top = 0
            if self.ballrect.bottom > screenHeight:
                self.v.y = int(-self.v.y * self.elasticity)
                if self.v.x > 0:
                    self.v.x = int(self.v.x - self.friction)
                elif self.v.x < 0:
                    self.v.x = int(self.v.x + self.friction)

                self.ballrect.bottom = screenHeight

    def Render(self):
        # For the sake of brevity, the title scene is a blank black screen
        self.screen.fill((255, 255, 255))
        self.screen.blit(self.ball, self.ballrect)
        pygame.display.flip()


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
                    self.SwitchToScene(Tanks())
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


