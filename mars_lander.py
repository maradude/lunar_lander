"""
ORDER of implementation:
D:
☑ Rocket sprite
☐ Instruments are rendered in top right corner // MOSTLY DONE
    ☑ BASIC INSTRUMENTS
    ☐ DAMAGE
    ☑ FUEL EMPTY
    ☐ TIME in correct format
    ☐ Score
    ☐ Minor aesthetic stuff
☐ Behaviour for hitting screen edges (bounce, carry-over, crash)
    ☑ Bounce
    ☑ carry-over
    ☑ crash
☐ Crash behaviour (pause, reset instruments [not score and time], reset x&y pos)
    ☑ pause
    ☑ reset function (for all but score and time)
☐ Game over behaviour (3 crashes, go out of run_game loop to game over func)
    ☑ lives
    ☑ game over text
C:
☑ 3 landing pads
☑ Crashing behaviour for pads (orientation or speed wrong)
☑ Landing behaviour (50 points for landing, same resets as crash)
☑ Random control failure (left or right doesn't work for 2sec, alert message)
    - Mostly working
    - Removed thrust failture, due to not being fun

B:
☑ 5 fixed location obstacles (10% damage for hitting)
☑ 100% damage == disable all controls

A:
☐ random meteor storm (5-10 moving sprites, collision causes 25% damage)
☐ Meteors disappear when hitting bottom, left or right side of screen

A1:
- Comments
- Layout refactoring
- Check for potential OOP mistakes or potential improvements
- Design pattern implementaiton potential?
"""
import operator
import random
import sys
import time
from math import sin, cos, radians
from typing import Tuple

import pygame
from pygame.locals import *
from recordclass import recordclass

# Some constants

LEFT = 'Left'
RIGHT = 'Right'
THRUST = 'Thrust'
ALTITUDEMULTIPLIER = 1.42857

class Game:
    pygame.init()
    BASICFONTSIZE = 20
    MEDIUMFONTSIZE = 60
    LARGEFONTSIZE = 100
    BASICFONT = pygame.font.Font('freesansbold.ttf',
                                 BASICFONTSIZE)
    LARGEFONT = pygame.font.Font('freesansbold.ttf',
                                 LARGEFONTSIZE)
    MEDIUMFONT = pygame.font.Font('freesansbold.ttf',
                                 MEDIUMFONTSIZE)

    def __init__(self):
        self.weight: int = 1200
        self.height: int = 750
        self.size: Tuple[int, int] = (self.weight, self.height)
        self._display_surf = pygame.display.set_mode(
            self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self.lander = Lander()
        self.back_ground = Background('resources/mars_background_instr.png',
                                      [0, 0])
        self.clock = pygame.time.Clock()
        self.landing_pads = [LandingPad('pad', 200-158//2, 750-18),
                             LandingPad('pad_tall', 600-158//2, 750-82),
                             LandingPad('pad', 1000-158//2, 750-18)]
        self.env_obstacles = [EnvironmentalObstacle('building_dome', CollidableObject.get_random_x(), CollidableObject.get_random_y()),
                              EnvironmentalObstacle('building_station_NE', CollidableObject.get_random_x(), CollidableObject.get_random_y()),
                              EnvironmentalObstacle('pipe_ramp_NE', CollidableObject.get_random_x(), CollidableObject.get_random_y()),
                              EnvironmentalObstacle('rocks_ore_SW', CollidableObject.get_random_x(), CollidableObject.get_random_y()),
                              EnvironmentalObstacle('satellite_SE', CollidableObject.get_random_x(), CollidableObject.get_random_y())]

    @staticmethod
    def quit():
        pygame.quit()
        sys.exit()

    def check_for_keypress(self):
        pass

    def show_game_over(self):
        pass

    def check_for_quit(self):
        pass

    def place_objects(self):
        pass

    @staticmethod
    def make_text(text, color, top, left, font):
        # taken from: http://inventwithpython.com/pygame/chapter4.html
        # create the Surface and Rect objects for some text.
        text_surf = font.render(text, True, color)
        text_rect = text_surf.get_rect()
        text_rect.topleft = (top, left)
        return text_surf, text_rect

    @staticmethod
    def pause():
        while 1:  # pause game
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                elif event.type == KEYDOWN or event.type == KEYUP:
                    return

    def run_game(self):
        # TODO: make everything before while 1 a function
        self.lander.instruments.reset_velocity()
        broken_time = 0
        while True:
            Background.update_background(self.back_ground)
            for pad in self.landing_pads:
                Background.SCREEN.blit(pad.sprite.image,
                                       pad.sprite.rect)
            self.lander.instruments.display_instruments()

            for obstacle in self.env_obstacles:
                Background.SCREEN.blit(obstacle.sprite.image,
                                       obstacle.sprite.rect)
            if self.lander.lives == 0:
                return
            self.lander.check_for_issues()
            Background.SCREEN.blit(self.lander.sprite.image,
                                   self.lander.sprite.rect)
            if self.lander.thrusting:
                Background.SCREEN.blit(self.lander.thrust_sprite.image,
                                       self.lander.thrust_sprite.rect)

            for obstacle in self.env_obstacles:
                if obstacle.is_collided_with(self.lander.sprite):
                    self.lander.instruments.damage.value += 10
                    self.env_obstacles.remove(obstacle)

            for pad in self.landing_pads:
                if pad.is_collided_with(self.lander.sprite):
                    self.lander.land()

            for event in pygame.event.get():
                # check for closing window
                if event.type == pygame.QUIT:
                    self.quit()
                elif event.type == KEYUP:
                    # check for removal of finger from a significant key
                    # boolean values for actions to make holding keys easier
                    if event.key == K_LEFT or event.key == K_a:
                        self.lander.rotating = False
                    elif event.key == K_RIGHT or event.key == K_d:
                        self.lander.rotating = False
                    elif event.key == K_SPACE:
                        self.lander.thrusting = False

                elif event.type == KEYDOWN:
                    # check for pressing a significant key
                    if event.key == K_LEFT or event.key == K_a:
                        self.lander.rotating = LEFT
                    elif event.key == K_RIGHT or event.key == K_d:
                        self.lander.rotating = RIGHT
                    elif event.key == K_SPACE:
                        self.lander.thrusting = True
                    elif event.key == K_r:
                        self.lander.reset_lander()
                else:  # ran out of fuel
                    self.lander.rotating = False
                    self.lander.thrusting = False

            if not self.lander.control_issue and time.time() - broken_time > 5:
                if random.randint(0, 600) < 10:
                    broken_time = self.lander.generate_control_failure()
            elif len(self.lander.control_issue) == 1:
                time_difference = time.time() - broken_time
                if time_difference >= 2:
                    self.lander.control_issue = []

            if self.lander.rotating in self.lander.control_issue:
                self.lander.rotating = False
            if THRUST in self.lander.control_issue:
                self.lander.thrusting = False
            if self.lander.control_issue:
                self.lander.display_control_error()

            # actually do stuff based on previous flags
            if self.lander.rotating:
                self.lander.steer()
            if self.lander.thrusting:
                power = 0.4  # after some testing this seems good, consider 0.33
                self.lander.instruments.fuel.value -= 5
            else:
                power = 0

            current_vec, thrust_vec = self.lander.calculate_new_vector(power)

            negative_thrust_vector = pygame.math.Vector2(thrust_vec)

            # TODO: add a function for handling lander hitting screen edges
            self.lander.sprite.rect.left += current_vec.x
            self.lander.sprite.rect.top += current_vec.y
            self.lander.instruments.altitude.value = int(
                abs(ALTITUDEMULTIPLIER * self.lander.sprite.rect.top - 1000))

            # makes the roof a bouncy castle
            if self.lander.sprite.rect.top <= 0:
                self.lander.sprite.rect.top += 1
                current_vec.y = -current_vec.y
            # move from left side of screen to right and vice versa
            if self.lander.sprite.rect.left >= 1200:
                self.lander.sprite.rect.left = 0
            elif self.lander.sprite.rect.right <= 0:
                self.lander.sprite.rect.right = 1200

            # display thruster sprite
            if self.lander.thrusting:
                negative_thrust_vector.scale_to_length(25)
                self.lander.rot_center(self.lander.thrust_sprite)
            self.lander.thrust_sprite.rect.center = tuple(
                map(operator.sub, self.lander.sprite.rect.center,
                    negative_thrust_vector))


            self.clock.tick(60)
            pygame.display.update()

    @classmethod
    def game_over(cls):
        message = "GAME OVER"
        MESSAGECOLOR = (255, 0, 0)
        text_surf, text_rect = cls.make_text(message, MESSAGECOLOR,
                                              0, 0, Game.LARGEFONT)
        text_rect.center = 600, 375
        Background.SCREEN.blit(text_surf, text_rect)
        pygame.display.update()
        time.sleep(2)
        cls.pause()


class Background(pygame.sprite.Sprite):
    # class taken from https://stackoverflow.com/a/28005796/9649969

    SCREEN = pygame.display.set_mode((1200, 750))

    def __init__(self, image_file, location):
        pygame.sprite.Sprite.__init__(self)  # call Sprite initializer
        self.image = pygame.image.load(image_file)
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = location

    @classmethod
    def update_background(cls, back_ground):
        cls.SCREEN.fill([255, 255, 255])
        cls.SCREEN.blit(back_ground.image, back_ground.rect)


class CollidableObject:

    def __init__(self, x, y):
        self.x_position: int = x
        self.y_position: int = y

    def is_collided_with(self, other_sprite):
        return self.sprite.rect.colliderect(other_sprite.rect)

    @staticmethod
    def get_random_x(bottom=0):
        """
        :return: a valid random x-coordinate
        """
        return random.randint(bottom, 1150)

    @staticmethod
    def get_random_y():
        """
        :return: a valid random y-coordinate
        """
        return random.randint(150, 550)

class Obstacle(CollidableObject):

    def __init__(self):
        super().__init__("x", "y")
        self.damage: int = None


class EnvironmentalObstacle(Obstacle):

    def __init__(self, sprite, x, y):
        self.damage = 10
        self.sprite = Sprite(f"resources/obstacles/{sprite}.png", (x, y))

class MovingObstacle(Obstacle):
    pass


class MyTimer:
    # from: https://stackoverflow.com/a/39883405/9649969
    def __init__(self):
        self.elapsed = 0.0
        self.running = False
        self.last_start_time = None

    def start(self):
        if not self.running:
            self.running = True
            self.last_start_time = time.time()

    def pause(self):
        if self.running:
            self.running = False
            self.elapsed += time.time() - self.last_start_time
            self.start()

    @staticmethod
    def get_elapsed(timer):
        elapsed = timer.elapsed
        if timer.running:
            elapsed += time.time() - timer.last_start_time
        return elapsed


class Instruments:
    # kinda of a lie, since recordclass is mutable, does work the same way
    instrument_tuple = recordclass('Instrument',
                                   ['value', 'x_position', 'y_position',
                                    'formatting'])

    def __init__(self):
        # convert below values into named tuples, with position and formatting info
        self.time = MyTimer()
        self.time.start()  # this could be done better
        # TODO: FIX Instrument positoning and formatting to match specs
        self.time_now = Instruments.instrument_tuple(self.time, 100, 15,
                                                     MyTimer.get_elapsed)  # min:sec, since start of 3 lives
        self.fuel = Instruments.instrument_tuple(500, 100, 35, None)  # kg?
        self.damage = Instruments.instrument_tuple(0, 100, 55,
                                                   None)  # 100 == game over
        self.altitude = Instruments.instrument_tuple(1000, 275, 15,
                                                     None)  # 0-1000m
        self.x_velocity = Instruments.instrument_tuple(0.0, 275, 35,
                                                       None)  # m/s
        self.y_velocity = Instruments.instrument_tuple(0.0, 275, 55,
                                                       None)  # m/s
        self.score: int = Instruments.instrument_tuple(0, 100, 80,
                                                       None)  # incremented by 50
        self.INSTRUMENTS = [self.time_now, self.fuel, self.damage, self.score,
                            self.altitude, self.x_velocity, self.y_velocity]

    def display_instruments(self):
        # TODO: render all instrument data
        MESSAGECOLOR = (0, 255, 0)
        for instrument in self.INSTRUMENTS:
            if instrument.formatting:
                message = str(instrument.formatting(instrument.value))
            else:
                message = str(instrument.value)[:5]
            if message[0] != '-':
                # this sould be inside the formatting stuff
                message = message[:4]
            message = message.rjust(5)
            text_surf, text_rect = Game.make_text(message, MESSAGECOLOR,
                                                instrument.x_position,
                                                instrument.y_position,
                                                Game.BASICFONT)
            Background.SCREEN.blit(text_surf, text_rect)


    def basic_reset(self):
        self.fuel.value = 500
        self.time.pause()

    def format_instrument(self, instrument):
        pass

    def calculate_velocity(self, angle: int, speed) -> Tuple[float, float]:
        angle = angle % 360
        if angle == 0:
            x_vel, y_vel = speed * 1.0, 0
        elif angle == 90:
            x_vel, y_vel = 0, speed * 1.0
        elif angle == 180:
            x_vel, y_vel = speed * -1, 0
        elif angle == 270:
            x_vel, y_vel = 0, speed * -1.0
        else:
            x_vel = speed * cos(radians(angle))
            y_vel = speed * sin(radians(angle))
        return x_vel, -y_vel

    def get_f_time(self) -> str:
        pass

    def get_f_velocity(self, n: float) -> str:
        pass

    def get_f_integer(self, n: int) -> str:
        pass

    def reset_velocity(self):
        self.x_velocity.value = random.randint(-10, 10) / 10
        self.y_velocity.value = random.randint(0, 10) / 10


class Sprite(pygame.sprite.Sprite):
    # TODO: import all collideable objects images as pygame.sprites
    # class taken from: https://stackoverflow.com/a/28005796/9649969
    def __init__(self, image_file, location):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load(image_file)  # .convert()
        self.ORIGINALIMAGE = self.image.copy()
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = location


class LandingPad(CollidableObject):

    def __init__(self, sprite, x, y):
        super().__init__("x", "y")
        self.sprite = Sprite(f'resources/landingPads/{sprite}.png', (x, y))


class Lander(CollidableObject):

    def __init__(self):
        super().__init__("x", "y")
        self.instruments = Instruments()
        self.sprite = Sprite('resources/lander.png', (CollidableObject.get_random_x(), 0))
        self.thrust_sprite = Sprite('resources/thrust.png', (600, 1))
        self.orientation: int = 90  # angle, 90 is upright, move to lander class
        self.lives: int = 3  # maybe move somewhere else?
        self.rotating = False
        self.thrusting = False
        self.control_issue = []
        self.velocity = pygame.math.Vector2(self.instruments.x_velocity.value,
                                            self.instruments.y_velocity.value)

    def rot_center(self, sprite):
        """rotate an image while keeping its center
        taken from: http://www.pygame.org/wiki/RotateCenter?parent=CookBook"""
        rot_image = pygame.transform.rotate(
            sprite.ORIGINALIMAGE, self.orientation - 90)
        rot_rect = rot_image.get_rect(center=sprite.rect.center)
        sprite.image = rot_image
        sprite.rect = rot_rect

    def thrust(self):
        pass

    def steer(self):
        # implement using orient %= 360 instead
        # takes 2 seconds to spin 360 degrees
        if self.rotating == RIGHT:
            self.orientation -= 1
        elif self.rotating == LEFT:
            self.orientation += 1
        self.orientation %= 360  # to make sure it stays in bounds
        self.rot_center(self.sprite)

    def check_for_issues(self):
        if self.sprite.rect.bottom > 750:  # 750 is image height
            self.crash()
        elif self.instruments.fuel.value <= 0:
            self.control_issue = ["Fuel", THRUST]
        elif self.instruments.damage.value >= 100:
            self.control_issue = ["All", LEFT, RIGHT, THRUST]

    def crash(self):
        # TODO: lander bottom being 1000 == crash
        # TODO: decrement lives on crash, game over after 3
        # TODO: implement lose screen
        Lander.crash_message()
        self.reset_lander()
        self.instruments.damage.value = 0
        self.lives -= 1

    @staticmethod
    def crash_message():
        message = "CRASHED"
        MESSAGECOLOR = (255, 0, 0)
        text_surf, text_rect = Game.make_text(message, MESSAGECOLOR,
                                             0, 0, Game.MEDIUMFONT)
        text_rect.center = 600, 375
        Background.SCREEN.blit(text_surf, text_rect)
        pygame.display.update()
        time.sleep(1)

    def reset_lander(self):
        self.control_issue = []
        self.thrusting = False
        self.rotating = False
        self.sprite.rect.left = Lander.get_random_x(350)
        self.sprite.rect.top = 1
        self.orientation = 90
        self.rot_center(self.sprite)
        self.instruments.reset_velocity()
        self.instruments.basic_reset()
        self.velocity.x = random.randint(-10, 10) / 10
        self.velocity.y = random.randint(0, 10) / 10
        Game.pause()
        self.instruments.time.start()

    def land(self):
        # TODO: bot hitting pad, x & y velocity <= 5, orientation 90±5 == landing
        # TODO: give points, pause game after landing
        x, y = self.velocity
        if x >= 5.0 or y >= 5.0:
            self.crash()
        elif self.orientation not in range(85, 95):  # lander upright
            self.crash()
        else:
            self.instruments.score.value += 50
            Lander.landing_message()
            self.reset_lander()

    @staticmethod
    def landing_message():
        message = "LANDED SAFELY"
        MESSAGECOLOR = (0, 255, 0)
        text_surf, text_rect = Game.make_text(message, MESSAGECOLOR,
                                              0, 0, Game.MEDIUMFONT)
        text_rect.center = 600, 375
        Background.SCREEN.blit(text_surf, text_rect)
        pygame.display.update()
        time.sleep(1)

    def float_in_direction(self, thrust: int):
        # TODO: delete float_in_direction?
        # to deal with moving in one direction and thrust being sent to another
        # http://www.physicsclassroom.com/class/vectors/Lesson-1/Vector-Addition
        zero_velocity_position = self._calculate_new_position(thrust)
        return zero_velocity_position

    def _calculate_new_position(self, dist: int):
        # TODO: delete _calculate_new_position?
        # polar coordinates
        x = dist * cos(radians(self.orientation))
        y = dist * sin(radians(self.orientation))
        new_position = (self.x_position + x, self.y_position + y)
        return new_position

    def hit_ceiling(self):
        # TODO: prevent lander top going above 0, maybe bump with y_vel > 5±2?
        pass

    def pass_over_side(self):
        # TODO: lander position left to right and vice versa when hitting edges
        pass

    def generate_control_failure(self):
        self.control_issue.append(random.choice([LEFT, RIGHT]))
        start_time = time.time()
        return start_time

    def calculate_new_vector(self, power):
        thrust_tuple = self.instruments.calculate_velocity(
            self.orientation, power)
        thrust_vector = pygame.math.Vector2(thrust_tuple)
        gravity_vec = pygame.math.Vector2(0, 0.2)  # may consider 0.1
        self.velocity += gravity_vec + thrust_vector
        self.instruments.x_velocity.value = self.velocity.x
        self.instruments.y_velocity.value = self.velocity.y
        return self.velocity, thrust_vector

    def display_control_error(self):
        MESSAGECOLOR = (255, 0, 0)
        message = f"{self.control_issue[0]} not working"
        text_surf, text_rect = Game.make_text(message, MESSAGECOLOR,
                                              145, 85, Game.BASICFONT)
        Background.SCREEN.blit(text_surf, text_rect)

def main():
    while 1:
        new_game = Game()
        new_game.run_game()
        new_game.game_over()


if __name__ == '__main__':
    main()
