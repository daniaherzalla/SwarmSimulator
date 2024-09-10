import app
import numpy as np
import pygame
import pygame.gfxdraw
import requests
from PIL import Image, ImageEnhance
from io import BytesIO
from .swarm import Swarm
from . import params
from . import gui
from time import time


def callback(*args, **kwargs):
    """Make a no-argument callback from a function."""
    def wrapper(f):
        def wrapped():
            return f(*args, **kwargs)
        return wrapped
    return wrapper


def fetch_map_image(api_key, center, zoom, size=(1800, 1000), brightness_factor=1, opacity_factor=1):
    """Fetch and modify a map image."""
    base_url = "https://maps.googleapis.com/maps/api/staticmap?"
    params = {
        "center": center,
        "zoom": zoom,
        "size": f"{size[0]}x{size[1]}",
        "maptype": "satellite",
        "style": "feature:all|element:labels|visibility:on",
        "key": api_key,
        "scale": 4
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        image = Image.open(BytesIO(response.content))
        image = image.convert('RGBA')  # Ensure image is in RGBA format

        # Enhance brightness
        if brightness_factor != 1.0:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(brightness_factor)

        # Adjust opacity
        if opacity_factor != 1.0:
            alpha = image.split()[3]
            enhancer = ImageEnhance.Brightness(alpha)
            alpha = enhancer.enhance(opacity_factor)
            image.putalpha(alpha)

        return pil_image_to_pygame(image)
    else:
        raise Exception(f"Failed to fetch map image: {response.status_code}")

def pil_image_to_pygame(image):
    """Convert PIL Image to Pygame Surface."""
    mode = image.mode
    size = image.size
    data = image.tobytes()

    return pygame.image.fromstring(data, size, mode).convert_alpha()


class Simulation:
    """Represent a simulation of a swarm."""

    def __init__(self, screen):
        self.running = True
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.swarm = Swarm(self.screen)
        self.to_update = pygame.sprite.Group()
        self.to_display = pygame.sprite.Group()
        self.temp_message = pygame.sprite.GroupSingle()
        self.perf_bar_background = None
        self.scroll_offset = 0  # Initialize scroll offset
        self.max_scroll_offset = 0  # To be calculated based on drone list size
        self.scroll_step = 20  # How much to scroll with each mouse wheel event

        # Load the background image from Google Maps - requires API key
        # self.background_image = self.load_google_map_image()
        # self.background_image = pygame.transform.scale(self.background_image, (params.SCREEN_WIDTH, params.SCREEN_HEIGHT))

        # Load the background image
        self.background_image = pygame.image.load("assets/img/satellitemap.png").convert()  # satellitemap roadmap
        self.background_image = pygame.transform.scale(self.background_image, (params.SCREEN_WIDTH, params.SCREEN_HEIGHT))


    def load_google_map_image(self):
        api_key = ""
        center = "24.438647877895647, 54.613846086933215"  # TII coordinates
        zoom = 15
        image = fetch_map_image(api_key, center, zoom)
        # Save the image to a file (optional)
        pygame.image.save(image, "map.png")  # This is how you save a Pygame surface
        return pygame.transform.scale(image, (params.SCREEN_WIDTH, params.SCREEN_HEIGHT))

    def handle_scroll(self, event):
        """Handle scrolling."""
        if event.type == pygame.MOUSEWHEEL:
            # Adjust scroll offset
            self.scroll_offset -= event.y * self.scroll_step
            # Limit scrolling within bounds
            self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll_offset))

    def draw_safety_dashboard(self, screen, position, size=(250, 350), shadow_offset=3, rounded_corners=10):
        # Calculate position adjustments for the shadow and main box
        adjusted_position = (position[0] - size[0] // 2 - shadow_offset, position[1] - size[1] // 2 - shadow_offset)

        # Shadow
        shadow_color = (50, 50, 50, 180)
        shadow_surface = pygame.Surface((size[0] + shadow_offset * 2, size[1] + shadow_offset * 2), pygame.SRCALPHA)
        shadow_surface.fill((0, 0, 0, 0))
        pygame.draw.rect(shadow_surface, shadow_color, shadow_surface.get_rect(), border_radius=rounded_corners)
        screen.blit(shadow_surface, adjusted_position)

        # Main box
        dashboard_surface = pygame.Surface(size, pygame.SRCALPHA)
        dashboard_color = pygame.Color('white')
        dashboard_color = (dashboard_color.r, dashboard_color.g, dashboard_color.b)
        dashboard_surface.fill((0, 0, 0, 0))
        pygame.draw.rect(dashboard_surface, (*dashboard_color, 200), dashboard_surface.get_rect(), border_radius=rounded_corners)
        screen.blit(dashboard_surface, (position[0] - size[0] // 2, position[1] - size[1] // 2))

        # Scrollable drone list surface
        drone_list_height = len(self.swarm.drones) * 20 + 20  # Calculate required height based on drone count
        scroll_surface = pygame.Surface((size[0], drone_list_height), pygame.SRCALPHA)
        drone_font = params.FONTS['quicksand']

        for i, drone in enumerate(self.swarm.drones):
            color = (255, 0, 0) if drone.is_jammed else (0, 255, 0)
            pygame.gfxdraw.filled_circle(scroll_surface, 25, i * 20 + 5, 6, color)

            if drone.id == 0:
                drone_text = f"FOG DRONE - {'Jammed' if drone.is_jammed else 'OK'}"
            else:
                drone_text = f"DRONE{drone.id:02} - {'Jammed' if drone.is_jammed else 'OK'}"

            drone_surf, drone_rect = drone_font.render(drone_text, (0, 50, 0), size=12)
            drone_rect.topleft = (50, i * 20)
            scroll_surface.blit(drone_surf, drone_rect)

        # Blit only the portion of the scroll surface visible in the dashboard
        screen.blit(scroll_surface, (position[0] - size[0] // 2, position[1] - size[1] // 2 + 100), area=pygame.Rect(0, self.scroll_offset, size[0], size[1] - 120))

        # Update max scroll offset based on content height and dashboard size
        self.max_scroll_offset = max(0, drone_list_height - (size[1] - 120))

        # Load the lock icon
        lock_icon = pygame.image.load('assets/img/lock.png').convert_alpha()  # Adjust the path to your lock icon image
        lock_icon = pygame.transform.scale(lock_icon, (18, 18))  # Adjust size as needed

        # Render the text
        title_font = params.FONTS['hallo-sans-light']
        title_surf, title_rect = title_font.render("Safety Dashboard", (0, 0, 0), size=18)
        title_rect.center = (position[0] - 38, position[1] - size[1] // 2 + 30)
        screen.blit(title_surf, title_rect)

        # Blit the lock icon next to the text
        icon_position = (title_rect.right - 125, title_rect.centery - lock_icon.get_height() // 2)  # larger val, more to left
        screen.blit(lock_icon, icon_position)

        # SRTA status section
        srta_font = params.FONTS['quicksand-bold']
        srta_surf, srta_rect = srta_font.render("SRTA Status", (128, 0, 128), size=14)
        srta_rect.center = (position[0] - 65, position[1] - size[1] // 2 + 60)
        screen.blit(srta_surf, srta_rect)

        # Draw underline
        underline_color = (128, 0, 128)  # Purple color to match the text
        underline_thickness = 1  # Thickness of the underline
        underline_start = (srta_rect.left, srta_rect.bottom + 3)  # Start just below the text
        underline_end = (srta_rect.right, srta_rect.bottom + 3)  # End at the right edge of the text
        pygame.draw.line(screen, underline_color, underline_start, underline_end, underline_thickness)

        # Actions section
        srta_font = params.FONTS['quicksand-bold']
        srta_surf, srta_rect = srta_font.render("Actions", (0, 0, 0), size=14)
        srta_rect.center = (position[0] + 15, position[1] - size[1] // 2 + 60)
        screen.blit(srta_surf, srta_rect)

    def draw_operations_bar(self, screen):
        position = (params.SCREEN_WIDTH // 2, 30)  # Adjusted for a bit lower position
        size = (900, 70)  # Width and height of the rectangle
        rounded_corners = 10
        horizontal_padding = 90  # Padding between text elements
        initial_x = position[0] - 150 // 2 + 20  # Start text from the left side of the box

        # Main box
        dashboard_surface = pygame.Surface(size, pygame.SRCALPHA)
        dashboard_color = pygame.Color('white')
        dashboard_color = (dashboard_color.r, dashboard_color.g, dashboard_color.b)
        pygame.draw.rect(dashboard_surface, (*dashboard_color, 150), dashboard_surface.get_rect(), border_radius=rounded_corners)
        screen.blit(dashboard_surface, (position[0] - size[0] // 2, position[1] - size[1] // 2))

        # Setting up fonts and colors
        title_font = params.FONTS['quicksand-bold']
        regular_font = params.FONTS['quicksand-bold']

        # Operations and Add Action
        ops_text, ops_rect = title_font.render('< OPERATIONS', (0, 0, 0), size=17)
        addAction_text, addAction_rect = title_font.render('+ ADD ACTION', (128, 0, 128), size=17)  # Purple
        ops_rect.topleft = (position[0] - 410, position[1] - 5)
        addAction_rect.topleft = (position[0] - 230, position[1] - 5)
        screen.blit(ops_text, ops_rect)
        screen.blit(addAction_text, addAction_rect)

        # Vertical line between operations and add action
        pygame.draw.line(screen, (160, 160, 160), (position[0] - 250, position[1] - 50), (position[0] - 250, position[1] + 35), 1)

        # Right section for operation details
        details_surface = pygame.Surface((520, 70), pygame.SRCALPHA)
        details_color = (32, 37, 47)  # Slate gray
        pygame.draw.rect(details_surface, details_color, details_surface.get_rect(), border_radius=rounded_corners)
        screen.blit(details_surface, (position[0] - 70, position[1] - 35))

        # Render text surfaces
        operation_text_surf, operation_text_rect = regular_font.render('OPERATION', (255, 255, 255), size=13)
        devices_text_surf, devices_text_rect = regular_font.render('DEVICES', (255, 255, 255), size=13)
        time_text_surf, time_text_rect = regular_font.render('START/END', (255, 255, 255), size=13)
        status_text_surf, status_text_rect = regular_font.render('STATUS', (255, 255, 255), size=13)
        progress_text_surf, progress_text_rect = regular_font.render('PROGRESS', (255, 255, 255), size=13)

        # Set positions and blit text
        operation_text_rect.topleft = (initial_x, position[1] - 15)
        devices_text_rect.topleft = (operation_text_rect.topright[0] + horizontal_padding + 45, position[1] - 15)
        time_text_rect.topleft = (devices_text_rect.topright[0] + horizontal_padding - 35, position[1] - 15)
        status_text_rect.topleft = (initial_x, position[1] + 10)
        progress_text_rect.topleft = (initial_x + 325, position[1] + 10)

        # Draw the texts
        screen.blit(operation_text_surf, operation_text_rect)
        screen.blit(devices_text_surf, devices_text_rect)
        screen.blit(time_text_surf, time_text_rect)
        screen.blit(status_text_surf, status_text_rect)
        screen.blit(progress_text_surf, progress_text_rect)

        # Bold and turquoise adjustments
        bold_font = params.FONTS['quicksand-bold']
        rationalgaze_surf, rationalgaze_rect = bold_font.render('RATIONALGAZE', (0, 206, 209), size=13)  # Turquoise bold
        num_drones_surf, num_drones_rect = bold_font.render(str(len(self.swarm.drones)), (0, 206, 209), size=13)  # Turquoise bold # Add one to num drones to include FogDrone
        start_end_surf, start_end_rect = bold_font.render(f"{params.START_TIME} / {params.END_TIME}", (0, 206, 209), size=13)  # Turquoise bold
        status_surf, status_rect = bold_font.render("EXECUTING", (0, 206, 209), size=13)  # Turquoise bold
        progress_surf, progress_rect = bold_font.render("0%%", (0, 206, 209), size=13)  # Turquoise bold

        # Adjustments for proper alignment
        rationalgaze_rect.midtop = (position[0] + 80, position[1] - 15)
        num_drones_rect.midtop = (position[0] + 230, position[1] - 15)
        start_end_rect.midtop = (position[0] + 390, position[1] - 15)
        status_rect.midtop = (position[0] + 68, position[1] + 10)
        progress_rect.midtop = (position[0] + 390, position[1] + 10)

        screen.blit(rationalgaze_surf, rationalgaze_rect)
        screen.blit(num_drones_surf, num_drones_rect)
        screen.blit(start_end_surf, start_end_rect)
        screen.blit(status_surf, status_rect)
        screen.blit(progress_surf, progress_rect)


    def add_element(self, pos=None):
        self.swarm.add_element(pos)
        if self.temp_message:
            self.temp_message.sprite.kill()
        msg = "Number of "
        if "Drone" in self.swarm.add_kind:
            msg += "drones: {}".format(len(self.swarm.drones))
        elif "Obstacle" in self.swarm.add_kind:
            msg += "obstacles: {}".format(len(self.swarm.obstacles))
        # self.temp_message.add(
        #     gui.TempMessage(pos=(6, 1), text=msg))

    def toggle_behaviour(self, behaviour):
        self.swarm.behaviours[behaviour] = not self.swarm.behaviours[behaviour]

    def update(self, motion_event, click_event):
        self.to_update.update(motion_event, click_event)

    def display(self):
        for sprite in self.to_display:
            sprite.display(self.screen)
            safety_dashboard_position = (params.SCREEN_WIDTH - 170, params.SCREEN_HEIGHT - 800)  # Place it at the top center where "Localization Methods" used to be
            self.draw_safety_dashboard(self.screen, safety_dashboard_position)
            self.draw_operations_bar(self.screen)


    def init_run(self):
        # Event Handling
        self.to_update = pygame.sprite.Group(
            self.swarm,
            gui.ToggleButton(
                pos=(0.2, 8.0),
                text="Entity : ",
                labels=self.swarm.kinds,
                init_label=self.swarm.add_kind,
                action=lambda: self.swarm.switch_element()),
            gui.ToggleButton(
                pos=(0.2, 8.5),
                text="ADD ENTITY",
                action=lambda: self.add_element(params.SCREEN_CENTER))
        )

        # Add fog drone
        self.swarm.add_kind = "Fog-drone"
        self.swarm.add_element((params.SCREEN_CENTER[0], params.SCREEN_CENTER[1]))

        # Add drones
        self.swarm.add_kind = "Drone"
        for _ in range(0, params.NUM_DRONES):
            self.swarm.add_element((params.SCREEN_CENTER[0], params.SCREEN_CENTER[1]))

        # Update sprite groups to include new entities
        self.to_display = pygame.sprite.Group(self.to_update)

    def run(self):
        key_to_function = {
            pygame.K_ESCAPE: lambda self, event: setattr(self, "running", False),
        }
        button_to_function = {
            3: lambda self, event: self.add_element(event.pos),
        }
        self.init_run()
        dt = 0
        while self.running:
            # Event handling should always occur to allow for system events and user inputs
            motion_event, click_event = None, None
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return "PYGAME_QUIT"
                elif event.type == pygame.KEYDOWN and event.key in key_to_function:
                    key_to_function[event.key](self, event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    click_event = event
                    if event.button in button_to_function:
                        button_to_function[event.button](self, event)
                elif event.type == pygame.MOUSEMOTION:
                    motion_event = event
                elif event.type == pygame.MOUSEWHEEL:
                    self.handle_scroll(event)

            # Update logic here, if any, that should run regardless of rendering
            self.update(motion_event, click_event)
            # Rendering-specific operations
            self.clock.tick(params.FPS)
            t = time()

            # Draw the background image
            self.screen.blit(self.background_image, (0, 0))

            # Apply a transparent color overlay
            overlay = pygame.Surface((params.SCREEN_WIDTH, params.SCREEN_HEIGHT))  # Create a new surface to serve as the overlay
            overlay.set_alpha(128)  # Adjust alpha to your preference for transparency
            overlay.fill(pygame.Color('paleturquoise4'))  # Fill the overlay with your color
            self.screen.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)  # Apply the overlay
            self.display()
            if self.temp_message:
                self.temp_message.sprite.display(self.screen)
            pygame.display.flip()
            dt = time() - t

    def quit(self):
        self.running = False

