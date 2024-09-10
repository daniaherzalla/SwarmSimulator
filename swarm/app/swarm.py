"""Swarm class."""
import csv
import importlib
import os
import random
import time

import pygame
import math
import numpy as np
import pickle

from matplotlib import pyplot as plt

from . import params, utils
from .drone import Drone, FogDrone
from .obstacle import Obstacle
from . import gui


class Swarm(pygame.sprite.Sprite):
    """Represents a set of drones that obey to certain behaviours."""
    def __init__(self, screen):
        super().__init__()
        self.screen = screen
        self.start_time = time.time()
        self.respawn = False

        # Sprites
        self.normal_drones = pygame.sprite.Group()
        self.leader_drone = pygame.sprite.GroupSingle()
        self.drones = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        self.kinds = ['Drone', 'Obstacle']
        self.add_kind = 'Drone'

        # Swarm environment
        self.behaviours = {
            'wander': False,
            'follow leader': True,
            'align': False,
            'separate': True,
            'move towards': True,
            'avoid geofence': False
        }

        self.temp_message = pygame.sprite.GroupSingle()


    def randomize_behaviours(self):
        for key in self.behaviours.keys():
            self.behaviours[key] = random.choice([True, False])
            if key == 'separate':  # always require separation
                self.behaviours[key] = True

        # Ensure that either 'wander' or 'follow leader' is always True and mutually exclusive
        if not self.behaviours['wander'] and not self.behaviours['follow leader']:
            self.behaviours[random.choice(['wander', 'follow leader'])] = True

        if self.behaviours['wander']:
            self.behaviours['follow leader'] = False
        elif self.behaviours['follow leader']:
            self.behaviours['wander'] = False

    def switch_element(self):
        self.kinds = np.roll(self.kinds, -1)
        self.add_kind = self.kinds[0]

    def add_element(self, pos):
        """Add a drone at pos.

        The type of drone is the current add_kind value.
        """
        # Dynamic initialization that gives each UAV a random vertical speed within a specified range
        angle = np.pi * (2 * np.random.rand() - 1)
        vel = params.DRONE_MAX_SPEED * np.array([np.cos(angle), np.sin(angle)])

        if self.add_kind == 'Fog-drone':
            if pos is None:
                pos = np.array([params.SCREEN_CENTER[0], params.SCREEN_CENTER[1]])
            self.leader_drone.add(FogDrone(pos=np.array(pos), vel=vel, screen=self.screen))
            self.drones.add(self.leader_drone)
        elif self.add_kind == 'Drone':
            if pos is None:
                pos = np.array([params.SCREEN_CENTER[0], params.SCREEN_CENTER[1]])
            self.normal_drones.add(Drone(pos=np.array(pos), vel=vel))
            self.drones.add(self.normal_drones)
        elif self.add_kind == 'Obstacle':
            self.obstacles.add(Obstacle())

    def remain_in_screen(self):
        # Wrap around horizontally
        for drone in self.drones:
            if drone.pos[0] > params.SCREEN_WIDTH:
                drone.pos[0] = 0
            elif drone.pos[0] < 0:
                drone.pos[0] = params.SCREEN_WIDTH

            # Wrap around vertically
            if drone.pos[1] > params.SCREEN_HEIGHT:
                drone.pos[1] = 0
            elif drone.pos[1] < 0:
                drone.pos[1] = params.SCREEN_HEIGHT


    def seek_single(self, target_pos, drone):
        # Calculate wrap-around distances along each dimension
        direct_distances = target_pos - drone.pos
        wrap_around_distances = np.where(direct_distances > 0, direct_distances - params.SCREEN_WIDTH, params.SCREEN_WIDTH + direct_distances)

        # Choose shorter distances (consider wrap-around)
        effective_distances = np.where(abs(direct_distances) < abs(wrap_around_distances), direct_distances, wrap_around_distances)

        # Normalize the effective distance vector for seeking
        effective_vector = utils.normalize(effective_distances) * params.DRONE_MAX_SPEED
        steering = effective_vector - drone.vel
        drone.steer(steering, alt_max=params.DRONE_MAX_FORCE / 50)

    def move_towards(self, target_drone):
        """Make a specific drone move towards a target position."""
        pos_x = random.randint(0, params.SCREEN_WIDTH)
        pos_y = random.randint(0, params.SCREEN_HEIGHT)
        target_pos = (pos_x, pos_y)
        self.seek_single(target_pos, target_drone)

    def seek(self, target_drone):
        """Make all normal drones seek to go to a target."""
        for drone in self.normal_drones:
            self.seek_single(target_drone, drone)

    def flee_single(self, target_pos, drone):
        too_close = utils.dist2(drone.pos, target_pos) < params.R_FLEE**2
        if too_close:
            steering = (utils.normalize(drone.pos - target_pos) *
                        params.DRONE_MAX_SPEED -
                        drone.vel)
            drone.steer(steering, alt_max=params.DRONE_MAX_FORCE / 10)

    def flee(self, target_drone):
        """Make all normal drones fly away from a target."""
        for drone in self.normal_drones:
            self.flee_single(target_drone, drone)

    def pursue_single(self, target_pos, target_vel, drone):
        t = int(utils.norm(target_pos - drone.pos) / params.DRONE_MAX_SPEED)
        future_pos = target_pos + t * target_vel
        self.seek_single(future_pos, drone)

    def pursue(self, target_drone):
        """Make all normal drones pursue a target drone with anticipation."""
        for drone in self.normal_drones:
            self.pursue_single(target_drone.pos, target_drone.vel, drone)

    def escape_single(self, target_pos, target_vel, drone):
        t = int(utils.norm(target_pos - drone.pos) / params.DRONE_MAX_SPEED)
        future_pos = target_pos + t * target_vel
        self.flee_single(future_pos, drone)

    def escape(self, target_drone):
        """Make all normal drones escape a target drone with anticipation."""
        for drone in self.normal_drones:
            self.escape_single(target_drone.pos, target_drone.vel, drone)

    def wander(self):
        """Make all drones wander around randomly."""
        rands = 2 * np.random.rand(len(self.drones)) - 1
        cos = np.cos([b.wandering_angle for b in self.drones])
        sin = np.sin([b.wandering_angle for b in self.drones])
        z_rands = np.random.uniform(-1, 1, len(self.drones))  # Random changes in altitude
        for i, drone in enumerate(self.drones):
            nvel = utils.normalize(drone.vel)
            # calculate circle center
            circle_center = nvel * params.WANDER_DIST
            # calculate displacement force
            c, s = cos[i], sin[i]
            displacement = np.dot(
                np.array([[c, -s], [s, c]]), nvel * params.WANDER_RADIUS)
            drone.steer(circle_center + displacement)
            drone.wandering_angle += params.WANDER_ANGLE * rands[i]

    def find_most_threatening_obstacle(self, drone, aheads):
        most_threatening = None
        distance_to_most_threatening = float('inf')

        for obstacle in self.obstacles:
            norms = [utils.norm2(obstacle.pos - ahead) for ahead in aheads]
            if all(n > obstacle.radius * obstacle.radius for n in norms):
                continue
            distance_to_object = utils.dist2(drone.pos, obstacle.pos)
            if most_threatening is not None and \
                    distance_to_object > distance_to_most_threatening:
                continue
            most_threatening = obstacle
            distance_to_most_threatening = utils.dist2(drone.pos,
                                                       most_threatening.pos)
        return most_threatening


    def avoid_collision(self):
        """Avoid collisions between drones and obstacles."""
        for drone in self.drones:
            ahead = drone.pos + drone.vel / params.DRONE_MAX_SPEED * \
                params.MAX_SEE_AHEAD
            ahead2 = drone.pos + drone.vel / params.DRONE_MAX_SPEED / 2 * \
                params.MAX_SEE_AHEAD
            most_threatening = self.find_most_threatening_obstacle(
                drone, [ahead, ahead2, drone.pos])
            if most_threatening is not None:
                steering = utils.normalize(ahead - most_threatening.pos)
                steering *= params.MAX_AVOID_FORCE
                drone.steer(steering)

    def avoid_geofence(self, closest_est):
        """Avoid geofence."""
        for drone in self.drones:
            ahead = drone.pos + drone.vel / params.DRONE_MAX_SPEED * \
                params.MAX_SEE_AHEAD_GEOFENCE
            steering = utils.normalize(ahead - closest_est)
            steering *= params.MAX_AVOID_FORCE_GEOFENCE
            drone.steer(steering)

    def separate_single(self, drone):
        number_of_neighbors = 0
        force = np.zeros(2)
        for other_drone in self.drones:
            if drone == other_drone:
                continue
            elif pygame.sprite.collide_rect(drone, other_drone):
                force -= other_drone.pos - drone.pos
                number_of_neighbors += 1
        if number_of_neighbors:
            force /= number_of_neighbors
        drone.steer(utils.normalize(force) * params.MAX_SEPARATION_FORCE)

    def separate(self):
        for drone in self.drones:
            self.separate_single(drone)

    def follow_leader(self, leader):
        """Make all normal drones follow a leader.

        Drones stay at a certain distance from the leader.
        They move away when in the leader's path.
        They avoid cluttering when behind the leader.
        """
        nvel = utils.normalize(leader.vel)
        behind = leader.pos - nvel * params.LEADER_BEHIND_DIST
        ahead = leader.pos + nvel * params.LEADER_AHEAD_DIST
        for drone in self.normal_drones:
            self.seek_single(behind, drone)
            self.escape_single(ahead, leader.vel, drone)

    def align(self):
        """Make all drones to align their velocities."""
        r2 = params.ALIGN_RADIUS * params.ALIGN_RADIUS
        # find the neighbors
        drones = list(self.normal_drones)
        neighbors = [[] for drone in drones]
        for i, drone in enumerate(drones):
            for j, other_drone in enumerate(drones):
                if j in neighbors[i]:
                    continue
                elif drone == other_drone:
                    continue
                elif utils.dist2(drone.pos, other_drone.pos) < r2:
                    neighbors[i].append(j)
                    neighbors[j].append(i)
        for i, drone in enumerate(drones):
            number_of_neighbors = len(neighbors[i])
            if number_of_neighbors:
                desired = np.zeros(2)
                for j in neighbors[i]:
                    desired += drones[j].vel
                drone.steer(desired / number_of_neighbors - drone.vel)

    def swarm(self):
        """Simulate flocking behaviour : alignment + separation + cohesion."""
        self.align()
        for drone in self.drones:
            self.separate_single(drone)

    def update(self, motion_event, click_event):
        # Apply steering behaviours
        if self.leader_drone:
            target = self.leader_drone.sprite
            self.behaviours['follow leader'] and self.follow_leader(target)
            self.behaviours['move towards'] and self.move_towards(target)
        self.behaviours['wander'] and self.wander()
        # Avoid obstacles if present
        if self.obstacles:
            self.avoid_collision()
        self.behaviours['align'] and self.align()
        self.behaviours['separate'] and self.separate()
        self.remain_in_screen()
        # Update all drones
        for drone in self.drones:
            drone.update()


    def display(self, screen):
        for obstacle in self.obstacles:
            obstacle.display(screen)
        for drone in self.drones:
            drone.display(screen)
        for drone in self.drones:
            drone.reset_frame()
        if self.temp_message:
            self.temp_message.sprite.display(self.screen)
        if self.temp_message:
            self.temp_message.sprite.kill()

