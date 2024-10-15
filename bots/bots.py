import asyncio
import itertools
import math
from pickle import OBJ
import random
from inspect import signature
from typing import List, Tuple, TYPE_CHECKING

import houdini.data.penguin
from houdini.data.room import Room, RoomWaddle, PenguinIglooRoomCollection
from houdini.handlers.play.igloo import create_first_igloo
from houdini.penguin import Penguin

from .constants import ITEM_TYPE, ROOM_AREAS, ROOM_SPOTS, SAFE_MESSAGES, RoomSpotsController
from .games import SledRacing

if TYPE_CHECKING:
    from houdini.plugins.bots import BotPlugin

class FakeWriter:
    def get_extra_info(self, _):
        return str(random.randbytes(10))
    
    def is_closing(self):
        return False

    def write(self, *args, **kwargs):
        pass

class PenguinBot(Penguin):
    # Class-level constants
    SNOWBALL_MARGIN = 25
    MOVEMENT_SPEED = 75
    DEFAULT_GREETINGS = [SAFE_MESSAGES.HI_THERE, SAFE_MESSAGES.HOW_U_DOING]
    DEFAULT_INTERACTION_DISTANCE = 100
    DEFAULT_SPOT_DISTANCE = 10
    DEFAULT_MAX_SPOT_PROB = 0.75
    VALID_FRAMES = range(18, 27)
    ACTIVITY_CYCLE_RANGE = range(10, 30)
    ACTIVITY_SLEEP_RANGE = range(5, 16)
    SPOT_SLEEP_RANGE = range(30, 120)

    def __init__(self, penguin_id: str, plugin: 'BotPlugin'):
        super().__init__(plugin.server, None, FakeWriter())
        self.penguin_id = penguin_id
        self.plugin = plugin
        self.config = plugin.config
        self.server = plugin.server
        self.penguin_data = None
        self.following_penguin = None
        self.frame = 18
        self._activity_task = None
        self.called = False
        self.talking = False
        self._activity_loop_running = False
        self._activity_task = None

    def load_data(self, data: houdini.data.penguin.Penguin) -> 'PenguinBot':
        self.update(**data.to_dict()) # update with Gino()
        return self

    async def initialize(self):
        self.server.penguins_by_id[self.id] = self
        self.server.penguins_by_username[self.username] = self

        if self.character:
            self.server.penguins_by_character_id[self.character] = self

        await self.open_igloo()
        
        if not self.called:
            await self.randomize_room()
            self.randomize_position()
        
    def begin_activity(self):
        """Starts or restarts the bot's activity loop."""
        self.stop_activity()
        # self.server.logger.info(f"Beginning {self.nickname} Loop")
        self._activity_task = asyncio.create_task(self.activity_loop())

    def stop_activity(self):
        """Stops the bot's activity loop if it's running."""
        if self._activity_task:
            self._activity_task.cancel()
            self._activity_task = None

    async def activity_loop(self):
        """Main loop for periodic bot activities like moving and changing frames."""
        try:
            while True:
                for _ in range(random.choice(self.ACTIVITY_CYCLE_RANGE)):
                    await self.perform_activities()
                await self.move_if_idle()

        except asyncio.CancelledError:
            self.server.logger.info(f"{self.nickname} Loop cancelled")

        except Exception as e:
            self.server.logger.error(f"Error in {self.nickname} Loop: {e}")

    async def perform_activities(self):
        """Performs activities like moving to spots, changing frames, and random movements."""
        await self.maybe_move_to_spot()
        await self.maybe_random_frame()
        await self.maybe_random_move()

    async def maybe_move_to_spot(self):
        """Moves the bot to a room spot if enabled by the plugin config."""
        if self.plugin.ENABLE_SPOT_LOCATIONS and not self.called:
            await self.move_to_spot()

    async def maybe_random_frame(self):
        """Changes the bot's frame to a random valid one if enabled."""
        if self.plugin.ENABLE_RANDOM_FRAME and not self.called:
            await asyncio.sleep(random.choice(self.ACTIVITY_SLEEP_RANGE))
            await self.random_frame()

    async def maybe_random_move(self):
        """Moves the bot randomly if enabled."""
        if self.plugin.ENABLE_RANDOM_MOVEMENT:
            await asyncio.sleep(random.choice(self.ACTIVITY_SLEEP_RANGE))
            await self.random_move()

    async def move_if_idle(self):
        """Moves the bot to a random room if not following another penguin."""
        if self.plugin.ENABLE_RANDOM_MOVEMENT and self.following_penguin is None and not self.called:
            await asyncio.sleep(random.choice(self.ACTIVITY_SLEEP_RANGE))
            await self.randomize_room()

    async def move_to_spot(self):
        """Moves the bot to a free spot in the room if available."""
        spots_controller = ROOM_SPOTS[self.room.id]
        max_occupation_likelihood = self.config.get("spot_max_probability", self.DEFAULT_MAX_SPOT_PROB)
        if random.random() <= min(spots_controller.len_spots() / 3, max_occupation_likelihood):
            with PenguinBotRoomSpots(spots_controller, self) as spot:
                if not self.is_occupied(spot):
                    await self.move_and_sync_special_clothing(spot)

    def is_occupied(self, spot):
        """Checks if the spot is occupied by another penguin."""

        def is_close(position, penguin):
            """Checks if another penguin is too close to the given spot location."""
            distance_needed = self.config.get('spot_distance', self.DEFAULT_SPOT_DISTANCE)
            penguin_distance = math.dist(position, (penguin.x, penguin.y))
            return not isinstance(penguin, self.__class__) and penguin_distance <= distance_needed

        for penguin in self.room.penguins_by_id.values():
            if is_close(spot.position, penguin):
                return True

        return False

    async def move_and_sync_special_clothing(self, spot):
        """Moves to the spot's location and equips clothing."""
        distance = math.dist((self.x, self.y), spot.position)
        self.x, self.y = spot.position
        self.frame = spot.frame
        await self.room.send_xt('sp', self.id, self.x, self.y)
        if spot.clothes:
            self.update_clothing(spot.clothes)
            await self.room_sync_clothing()
        await asyncio.sleep(distance / self.MOVEMENT_SPEED + 2)
        await self.room.send_xt('sf', self.id, self.frame)

    def update_clothing(self, SpotClothes):
        """Updates the bot's clothing (i.e., drum sticks), or unequipped"""
        self.head = SpotClothes.get(ITEM_TYPE.HEAD, 0)
        self.face = SpotClothes.get(ITEM_TYPE.FACE, 0)
        self.neck = SpotClothes.get(ITEM_TYPE.NECK, 0)
        self.body = SpotClothes.get(ITEM_TYPE.BODY, 0)
        self.hand = SpotClothes.get(ITEM_TYPE.HAND, 0)
        self.feet = SpotClothes.get(ITEM_TYPE.FEET, 0)

    async def random_frame(self):
        """Sets a random frame."""
        self.frame = random.choice(self.VALID_FRAMES)
        await self.room.send_xt('sf', self.id, self.frame)

    async def random_move(self):
        """moves to a random position"""
        self.randomize_position()
        await self.room.send_xt('sp', self.id, self.x, self.y)

    async def handle_snowball(self, p, x: int, y: int):
        """Handles the bot's response to snowball throws."""
        if self.is_snowballed(x, y):
            await asyncio.sleep(1)
            await self.snowball_reaction(p)

    def is_snowballed(self, x: int, y: int) -> bool: # uses the bot's XY position and a margin
        return x in range(self.x - self.SNOWBALL_MARGIN, self.x + self.SNOWBALL_MARGIN) and \
               y in range(self.y - self.SNOWBALL_MARGIN, self.y + self.SNOWBALL_MARGIN)

    async def snowball_reaction(self, p):
        """React to a snowball throw based on plugin settings."""
        reactions = [
            (self.laments_snowball, self.config.get('enable_snowball_lament', True)),
            (self.throws_snowball_back, self.config.get('enable_snowball_throwback', True))
        ]
        enabled_reactions = [f for f, e in reactions if e]
        if enabled_reactions:
            await random.choice(enabled_reactions)(p)

    async def laments_snowball(self, _):
        await self.room.send_xt('se', self.id, 4)

    async def throws_snowball_back(self, p):
        await self.room.send_xt('sb', self.id, p.x, p.y)

    async def handle_safe_message(self, p, message_id: int):
        """Handles safe messages and acts on recieving them"""
        if not self.meets_interaction_distance(p):
            p.logger.info("Less than minimum distance")
            return
        p.logger.info(f"A safe message has been recieved {message_id}")
        message_reactions = {
            SAFE_MESSAGES.HELLO: (self.give_greeting, lambda: not self.called),
            SAFE_MESSAGES.FOLLOW_ME: (self.follow, self.config.get('enable_follow_mode', True)),
            SAFE_MESSAGES.GO_AWAY: (self.stop_following, self.config.get('enable_follow_mode', True)),
            SAFE_MESSAGES.WHERE: (self.random_move, self.config.get('enable_random_movement_on_demand', True))}
        reaction, is_enabled = message_reactions.get(message_id, (None, False))
        if reaction and is_enabled:
            await reaction(p) if len(signature(reaction).parameters) > 0 else await reaction()

    async def give_greeting(self):

        '''Sends a random greeting message to the room'''
        self.logger.info(f"{self.username} is greeting the room")
        await self.room.send_xt('ss', self.id, random.choice(self.config.get('greeting_messages', self.DEFAULT_GREETINGS)))

    async def go_player_room(self, p, room: Room):
        self.x, self.y = p.x, p.y
        await self.join_room(room)

    async def goto_coordinates(self, p, x: int, y: int):
        b = self
        angle = math.atan2(b.y - y, b.x - x) # angle between the player's and the bot's coordinates
        min_distance = 40 # how far behind bots should follow players
        b.x = int(x + min_distance * math.cos(angle)) # offsetts in the X and Y direction
        b.y = int(y + min_distance * math.sin(angle)) 
        b.frame = 1
        b.toy = None
        p.logger.info(f"{b.username} Following {p.username} to {b.x}, {b.y}")
        await asyncio.sleep(0.5)
        await b.room.send_xt('sp', b.id, b.x, b.y)

    async def follow(self, p):
        """Begins to follow a penguin."""
        if not self.following_penguin:
            self.following_penguin = p
            await self.room.send_xt('ss', self.id, SAFE_MESSAGES.OK)
            await self.goto_coordinates(p, p.x, p.y)

    async def stop_following(self):
        """Stops following a penguin."""
        if self.following_penguin:
            self.following_penguin = None
            await self.room.send_xt('ss', self.id, SAFE_MESSAGES.SEE_U_LATER)
            await asyncio.sleep(2)
            await self.randomize_room()

    async def handle_disconnected(self):
        """Removes the bot from the server and cancels its activity task."""
        del self.server.penguins_by_id[self.id]
        del self.server.penguins_by_username[self.username]
        if self.character in self.server.penguins_by_character_id:
            del self.server.penguins_by_character_id[self.character]
        await self.room.remove_penguin(self)
        self._activity_task.cancel()
        self.close_igloo()
        self.server.logger.info(f'{self.username} disconnected')

    def meets_interaction_distance(self, p) -> bool:
        return math.dist((self.x, self.y), (p.x, p.y)) < self.config.get(
            'interaction_distance', self.DEFAULT_INTERACTION_DISTANCE)
            
    async def room_sync_clothing(self):
        """sends clothing data to other clients in the room"""
        if not self.room:
            return
        clothing_data = {
            'upc': self.color, 'uph': self.head, 'upf': self.face,
            'upn': self.neck, 'upb': self.body, 'upa': self.hand,
            'upe': self.feet, 'upl': self.flag, 'upp': self.photo}
        for update, item_id in clothing_data.items():
            await self.room.send_xt(update, self.id, item_id)

    def randomize_position(self):
        """Randomly assigns a new position to the bot in the room."""
        self.random_position_in_room(ROOM_AREAS[self.room.id])

    def random_position_in_room(self, points: List[Tuple[int, int]]): # This treats the polygon (formed by the room’s boundaries) as being made up of multiple triangles for unpredictable positioning.
        """Generates a random position within the room area."""
        triangles = [(points[0], a, b) for a, b in itertools.pairwise(points[1:])]
        triangles_areas = [self.area_of_triangle(t) for t in triangles]
        (x1, y1), (x2, y2), (x3, y3) = random.choices(triangles, weights=triangles_areas)[0] # Larger triangles have a higher chance of being selected.
        self.x, self.y = self.coordinates_in_triangle(x1, y1, x2, y2, x3, y3)

    def area_of_triangle(self, triangle: Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]) -> float:
        """Calculates the area of a triangle."""
        (x1, y1), (x2, y2), (x3, y3) = triangle
        return 0.5 * abs(x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))

    def coordinates_in_triangle(self, x1, y1, x2, y2, x3, y3) -> Tuple[int, int]: # Generates random numbers to interpolate between the triangle's vertices, ensuring points are uniformly distributed inside the triangle
        """Generates a random point inside a triangle."""
        r1, r2 = random.random(), random.random()
        s1 = math.sqrt(r1)
        x = int(x1 * (1 - s1) + x2 * (1 - r2) * s1 + x3 * r2 * s1)
        y = int(y1 * (1 - s1) + y2 * (1 - r2) * s1 + y3 * r2 * s1)
        return x, y

    async def randomize_room(self):
        """Moves to a random room based on plugin configuration."""
        config_rooms = self.config.get('bot_rooms', self.plugin.room_ids)
        available_rooms = [self.server.rooms[x] for x in config_rooms if self.room is None or x != self.room.id]

        room_weights = self.config.get('room_weights', {})
        room_weights = [room_weights.get(str(x.id), 1) for x in available_rooms]

        await self.join_room(random.choices(available_rooms, weights=room_weights)[0])

    async def enter_waddle(self, PLAYER: Penguin, waddle: RoomWaddle):
        """Joins a waddle game if configured."""
        if waddle.id in self.config.get('waddle_ids', self.plugin.waddle_ids):

            self.server.logger.info(f'{self.username} scheduled to join waddle {waddle.id}')

            await asyncio.sleep(self.config.get('waddle_join_delay', self.plugin.waddle_join_delay))

            if PLAYER.waddle != waddle:
                self.server.logger.info(f"Penguin {PLAYER.username} no longer in waddle room, aborting...")
                return

            previous_room = self.room
            await waddle.add_penguin(self)

            if waddle.game == 'sled':
                game = SledRacing(self)
                await game.play(waddle.id, random.choice(list(game.waddles[waddle.id].keys())))

            if previous_room:
                await self.join_room(previous_room)

    async def open_igloo(self):
        self.igloo_rooms = await PenguinIglooRoomCollection.get_collection(self.id)
        await create_first_igloo(self, self.id)
        igloo = self.igloo_rooms[self.igloo]
        await igloo.update(
            type=random.choice(list(self.server.igloos.keys())),
            location=random.choice(list(self.server.locations.keys()))
        ).apply()
        self.server.open_igloos_by_penguin_id[self.id] = igloo

    def close_igloo(self):
        if self.id in self.server.open_igloos_by_penguin_id:
            del self.server.open_igloos_by_penguin_id[self.id]

class PenguinBotRoomSpots:

    def __init__(self, spots_controller: RoomSpotsController, bot: 'PenguinBot') -> None:
        self.controller = spots_controller
        self.bot = bot
        self.clothes = {} # store the bot's original clothing

    def __enter__(self):
        self.spot = next(x.pop(0) for x in self.controller.spots if x)
        self.clothes = {
            ITEM_TYPE.HEAD: self.bot.head,
            ITEM_TYPE.FACE: self.bot.face,
            ITEM_TYPE.NECK: self.bot.neck,
            ITEM_TYPE.BODY: self.bot.body,
            ITEM_TYPE.HAND: self.bot.hand,
            ITEM_TYPE.FEET: self.bot.feet,
        }
        return self.spot

    def __exit__(self, exc_type, exc_val, exc_tb): # On exiting the context manager (or 'with'), the bot's clothing is restored
        self.bot.head = self.clothes[ITEM_TYPE.HEAD]
        self.bot.face = self.clothes[ITEM_TYPE.FACE]
        self.bot.neck = self.clothes[ITEM_TYPE.NECK]
        self.bot.body = self.clothes[ITEM_TYPE.BODY]
        self.bot.hand = self.clothes[ITEM_TYPE.HAND]
        self.bot.feet = self.clothes[ITEM_TYPE.FEET]
        self.controller.spots[self.spot.priority - 1].append(self.spot)
