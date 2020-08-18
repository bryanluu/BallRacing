import pygame
from scenes import *
import os

pygame.init()


def run_game(width, height, fps, starting_scene):
    screen = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()

    active_scene = starting_scene
    paused = None

    while active_scene:

        if not active_scene.initialized:
            active_scene.initGraphics(screen)
            active_scene.initialized = True

        pressed_keys = pygame.key.get_pressed()

        # Event filtering
        filtered_events = []
        for event in pygame.event.get():
            quit_attempt = False
            if event.type == pygame.QUIT:
                quit_attempt = True
            elif event.type == pygame.KEYDOWN:
                alt_pressed = pressed_keys[pygame.K_LALT] or \
                              pressed_keys[pygame.K_RALT]
                if event.key == pygame.K_ESCAPE:
                    quit_attempt = True

            if quit_attempt:
                if isinstance(active_scene, DrivingScene)\
                        or isinstance(active_scene, CopterScene)\
                        or isinstance(active_scene, TestScene):
                    paused = active_scene
                    active_scene.SwitchToScene(CheckExit(paused))
                elif isinstance(active_scene, CheckExit):
                    active_scene.SwitchToScene(paused)
                    paused.next = paused
                elif isinstance(active_scene, Pause):
                    active_scene.next = Start()
                else:
                    active_scene.Terminate()
            else:
                filtered_events.append(event)

        active_scene.ProcessInput(filtered_events, pressed_keys)
        active_scene.Update()
        active_scene.Render()

        active_scene = active_scene.next

        pygame.display.flip()
        clock.tick(fps)

#==============================================================================
# The rest is code where you implement your game using the Scenes model

run_game(1000, 800, 60, Start())
