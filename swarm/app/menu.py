"""Menu screen."""
import pygame
from . import params
from . import assets
from . import gui
from .simulation import Simulation

key_to_function = {
    # insert lambda hooks here
}


class Menu:
    """The menu loop."""

    def __init__(self):
        self.running = True
        self.screen = pygame.display.set_mode(params.SCREEN_SIZE)
        pygame.display.set_icon(assets.image('boids-logo.png'))
        pygame.display.set_caption(params.CAPTION)
        self.clock = pygame.time.Clock()
        self.to_update = pygame.sprite.Group()
        self.to_display = pygame.sprite.Group()

    def update(self, motion_event, click_event):
        self.to_update.update(motion_event, click_event)

    def display(self):
        for sprite in self.to_display:
            sprite.display(self.screen)

    def start_simulation(self):
        s = Simulation(self.screen)
        if s.run() == "PYGAME_QUIT":
            self.quit()

    def main(self):
        self.start_simulation()

    def quit(self):
        self.running = False
