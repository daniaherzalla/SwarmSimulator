"""Drone class."""
import math
import pygame
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import lognorm

from . import utils
from . import params
from . import assets


class Drone(pygame.sprite.Sprite):
    """A normal drone.

    Parameters
    ----------
    pos : np.array
    vel : np.array
    """

    image_file = 'drone2_resized.png'
    id_counter = 0  # Class attribute to keep track of the number of drone instances

    def __init__(self, pos=None, vel=None, mass=20, image_size=(70, 70)):  # (60,65)
        super().__init__()
        if pos is None:
            pos = np.zeros(2)
        if vel is None:
            vel = np.zeros(2)

        # Load and scale the image
        original_image, self.rect = assets.image_with_rect(self.image_file)
        self.base_image = pygame.transform.scale(original_image, image_size)
        self.image = self.base_image
        self.rect = self.image.get_rect()

        self.pos = pos
        self.vel = vel
        self.mass = mass
        self.steering = np.zeros(2)
        self.wandering_angle = utils.randrange(-np.pi, np.pi)
        self.is_jammed: bool = False  # brainstorming: if within distance d of obj jammer then jam det true

        # Assign a unique ID to the drone
        self.id = Drone.id_counter
        Drone.id_counter += 1

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, pos):
        self._pos = pos
        self.rect.center = (pos[0], pos[1])

    @property
    def vel(self):
        return self._vel

    @vel.setter
    def vel(self, vel):
        self._vel = vel

    def steer(self, force, alt_max=None):
        """Add a force to the current steering force"""
        # limit the steering each time we add a force
        if alt_max is not None:
            self.steering += utils.truncate(force / self.mass, alt_max)
        else:
            self.steering += utils.truncate(
                force / self.mass, params.DRONE_MAX_FORCE)

    def jamming_detected(self):
        """Handle jamming detection."""
        self.is_jammed = True
        # Load the red drone image
        jammed_drone_image = pygame.image.load("assets/img/jammed_drone.png").convert_alpha()
        # Scale the image to match the original drone's size
        jammed_drone_image = pygame.transform.scale(jammed_drone_image, (70,70))
        # Set the new image as the drone's image
        self.image = jammed_drone_image

    def reset_jamming(self):
        if self.is_jammed:
            self.is_jammed = False
            # Load the original black drone image
            self.image = self.base_image

    def update(self):
        self.vel = utils.truncate(
            self.vel + self.steering, params.DRONE_MAX_SPEED)
        self.pos = self.pos + self.vel

    def display(self, screen, debug=False):
        screen.blit(self.image, self.rect)

        if debug:
            pygame.draw.line(
                screen, pygame.Color("red"),
                tuple(self.pos), tuple(self.pos + 2 * self.vel))
            pygame.draw.line(
                screen, pygame.Color("blue"), tuple(self.pos),
                tuple(self.pos + 30 * self.steering))

    def reset_frame(self):
        self.steering = np.zeros(2)


class FogDrone(Drone):
    """A drone that others drones want to follow."""
    image_file = 'drone2_resized.png'

    def __init__(self, pos=None, vel=None, mass=20, screen=None):
        super().__init__(pos, vel, mass)
        self.jammed_drones_rssi_sans_noise = []
        self.drones_rssi_sans_noise = []
        self.drones_gps_coords = []
        self.drones_rssi = []
        self.drones_status = []
        self.jammed_drones_gps_coords = []
        self.jammed_drones_rssi = []
        self.swarm_snapshots = []
        self.screen = screen

        # Load and scale the image
        original_image, self.rect = assets.image_with_rect(self.image_file)
        self.base_image = pygame.transform.scale(original_image, (100, 100))
        self.image = self.base_image
        self.rect = self.image.get_rect()

    def collect_swarm_data(self, swarm_snapshots):
        # Save swarm_snapshots list of dicts: key is snapshot num, val is list of lists (drones' data [pos, rssi, status])
        self.swarm_snapshots = swarm_snapshots

        # Loop through snapshots, within each, save jammed drones data
        # TODO: need to track per drone the data collected, prob need a dict with unique key per drone and add to that - done

        for snapshot in swarm_snapshots:  # for each dict in the list
            for key, drones_dict in snapshot.items():  # value is now a dict with drone IDs as keys
                for drone_id, drone_data in drones_dict.items():  # iterate through the drone data dictionary
                    # [pos, vel, wandering_angle, rssi, jamming_status]
                    pos = drone_data[0]
                    vel = drone_data[1]
                    wandering_angle = drone_data[2]
                    rssi = drone_data[3]
                    is_jammed = drone_data[4]

                    self.drones_gps_coords.append(pos)
                    self.drones_rssi.append(rssi)
                    self.drones_status.append(is_jammed)
                    if is_jammed == 'jammed':
                        self.jammed_drones_gps_coords.append(pos)
                        self.jammed_drones_rssi.append(rssi)

        if len(self.drones_gps_coords) >= params.NUM_SAMPLES:
            self.jammed_drones_rssi_sans_noise = self.jammed_drones_rssi
            self.drones_rssi_sans_noise = self.drones_rssi
            return True
        else:
            # print(f"collected {len(self.jammed_drones_gps_coords)} samples")
            return False


    def transform_data(self, data):
        """combined snapshots - movement"""
        # Flatten the data
        flattened_data = []
        for snapshot in data:
            for snapshot_key, drones in snapshot.items():
                for drone_id, values in drones.items():
                    entry = {
                        'node_positions': values[0],  # This should be a list of arrays
                        'node_velocity': values[1],
                        'wandering_angle': values[2],
                        'node_noise': values[3],
                        'node_states': values[4]
                    }
                    flattened_data.append(entry)

        # Create DataFrame
        df = pd.DataFrame(flattened_data)

        # Combine all data into a single row dictionary
        combined_data = {
            'node_positions': list(df['node_positions']),
            'node_velocity': list(df['node_velocity']),
            'wandering_angle': list(df['wandering_angle']),
            'node_noise': list(df['node_noise']),
            'node_states': list(df['node_states'])
        }

        # Wrap combined_data in a list to create a single-row DataFrame
        overall_aggregated = pd.DataFrame([combined_data])

        return overall_aggregated

    def reset_data_collected(self):
        self.jammed_drones_rssi_sans_noise = []
        self.drones_rssi_sans_noise = []
        self.drones_gps_coords = []
        self.drones_rssi = []
        self.drones_status = []
        self.jammed_drones_gps_coords = []
        self.jammed_drones_rssi = []
        self.swarm_snapshots = []
