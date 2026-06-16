"""
Script used for loading the gamepad/joystick
"""

import pygame

joystick: pygame.joystick.JoystickType | None = None

LEFT_X_AXIS = 0
LEFT_Y_AXIS = 1
AXIS_THESHOLD = 0.9

def init():
    global joystick
    pygame.joystick.init()
    if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
    else:
        joystick = None

def get_joystick() -> pygame.joystick.JoystickType | None:
    return joystick