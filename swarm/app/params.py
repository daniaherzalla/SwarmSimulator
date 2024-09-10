"""Simulation parameters."""
import datetime
import os
import random
import numpy as np
import pygame
import pygame.freetype
import pygame.gfxdraw
from . import assets

pygame.init()

# GUI parameters
CAPTION = 'Swarm Simulator'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE_DIR, 'assets', 'img')
FONTS_DIR = os.path.join(BASE_DIR, 'assets', 'fonts')

# Screen and viewing parameters
SCREEN_HEIGHT, SCREEN_WIDTH = 1020, 1850
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)
SCREEN_CENTER = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
COL = SCREEN_WIDTH // 12
ROW = SCREEN_HEIGHT // 9
FPS = 30
MENU_BACKGROUND = pygame.Color('slate gray')
SIMULATION_BACKGROUND = pygame.Color('dark slate gray')
FONTS = {
    'hallo-sans-light': assets.freetype('hallo-sans-light.otf'),
    'hallo-sans-bold': assets.freetype('hallo-sans-bold.otf'),
    'hallo-sans': assets.freetype('hallo-sans.otf'),
    'quicksand': assets.freetype('quicksand.otf'),
    'quicksand-bold': assets.freetype('quicksand-bold.otf'),
    'quicksand-light': assets.freetype('quicksand-light.otf'),
}
FONT_SIZES = {
    'body': 17,
    'h1': 128,
    'h2': 48,
    'h3': 32,
    'h4': 28,
    'h5': 24,
}
FONT_COLOR_MENU = pygame.Color('white')
FONT_COLOR = pygame.Color('dark slate gray')
BODY_FONT = (FONTS['hallo-sans'], FONT_SIZES['body'], )
H1_FONT = (FONTS['quicksand-light'], FONT_SIZES['h1'])
H2_FONT = (FONTS['hallo-sans'], FONT_SIZES['h2'])
H3_FONT = (FONTS['quicksand'], FONT_SIZES['h3'])
H4_FONT = (FONTS['hallo-sans'], FONT_SIZES['h4'])
H5_FONT = (FONTS['hallo-sans'], FONT_SIZES['h5'])

# Drone steering parameters
DRONE_MAX_FORCE = 10.
DRONE_MAX_SPEED = 4.0
# Drone staying inside the screen box
BOX_MARGIN = 50  # pixels
STEER_INSIDE = 15  # speed impulse when out of margins
# Drone seek parameters
R_SEEK = 100
# Drone flee parameters
R_FLEE = 200
# Drone wandering parameters
WANDER_DIST = 4.5
WANDER_RADIUS = 3.0
WANDER_ANGLE = 1.0  # degrees
# Drone obstacle avoidance parameters
MAX_SEE_AHEAD = 50  # pixels
MAX_AVOID_FORCE = 6.0
# Drone separation parameters
SEPARATION_DIST = 10
MAX_SEPARATION_FORCE = 10.
# Leader following parameters
LEADER_BEHIND_DIST = 10  # pixels
LEADER_AHEAD_DIST = 40
# Obstacles parameters
NUM_OBSTACLES = np.random.randint(1, 10)
# Drones parameters
NUM_DRONES = 5
# Drone alignment parameters
ALIGN_RADIUS = 200
# Drone cohesion parameters
COHERE_RADIUS = 300
# Time
RESPAWN_TIMER = 600  # seconds
current_time = datetime.datetime.now()
START_TIME = current_time.strftime("%H:%M")
END_TIME = (current_time + datetime.timedelta(seconds=RESPAWN_TIMER)).strftime("%H:%M")
# multi-threading parameters
N_CPU = os.cpu_count()
