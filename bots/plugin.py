import asyncio
import json
import os
import random
import secrets

from collections import defaultdict

import bcrypt

from houdini import handlers
from houdini.data.item import PenguinItem
from houdini.data.penguin import Penguin
from houdini.data.plugin import PenguinAttribute
from houdini.data.room import Room, RoomWaddle
from houdini.crypto import Crypto
from houdini.handlers import XTPacket
from houdini.commands import UnknownCommandException, has_command_prefix
from houdini.houdini import Houdini
from houdini import commands, permissions
from houdini.plugins import IPlugin

from . import fantasynames as names
from .bots import PenguinBot
from .constants import ITEM_TYPE
from .languagemodel.create import PersonaFileCreator
from .languagemodel import converse


# handling friend requests

# mascot messages and conversations

# flexibility and backstories

# ice hockey

# other multiplayer games

# stage plays reenactments

# elemental ninja swarms

# ice berg digging swarms

# disco swarms

class BotPlugin(IPlugin):
    
    author = "Brosquinha and Walinski"
    description = "Bots 2.0"
    version = "1.0.0"

    config_file = os.path.join(os.path.dirname(__file__), 'config.json')

    items_categorized = defaultdict(list)  

    # Defaults
    room_ids = [
        100, 110, 111, 120, 121, 130, 300, 310, 320, 330, 340, 200, 220,
        230, 801, 802, 800, 400, 410, 411, 809, 805, 810, 806, 808, 807
    ]
    waddle_ids = [100, 101, 102, 103]
    waddle_join_delay = 10

    accounts = []
    active_bots = []
    spawned = []

    ENABLE_SPOT_LOCATIONS = True
    ENABLE_RANDOM_FRAME = True
    ENABLE_RANDOM_MOVEMENT = True

    def __init__(self, server: Houdini): # initial Houdini server instance variables

        self.server = server

        for _, item in self.server.items.items():  # Items structured into lists by their type
            self.items_categorized[item.type].append(item)

        # Load plugin config settings
        with open(self.config_file) as f:
            self.config: dict = json.load(f)

        self.dash_static_key = self.config.get('dash_static_key', 'houdini')
        self.email_domain = self.config.get('email_domain', 'email.com')
        self.active_rooms = self.config.get('active_rooms', self.room_ids)

        self.has_inventory = True
        self.rotation_enabled = True
        self.greeting_enabled = True

        self.rotation_interval = range(60, 180)
        self.beginning_population = 0

        PersonaFileCreator.load_personas()

    async def ready(self):

        if self.server.config.type != 'world':
            return

        self.server.logger.info("Bots 2.0 Loaded!")

        await self.register_permissions()

        existing_bots = await PenguinAttribute.select('penguin_id').where(PenguinAttribute.name == "BOT").gino.all()
        self.accounts = await Penguin.query.where(Penguin.id.in_([b[0] for b in existing_bots])).gino.all()

        asyncio.create_task(self.populate(self.beginning_population))

        if self.rotation_enabled:
            asyncio.create_task(self._rotation())

    async def register_permissions(self):
        await self.server.permissions.register('bots.restyle')
        await self.server.permissions.register('bots.bpop')
        await self.server.permissions.register('bots.bpurge')
        await self.server.permissions.register('bots.spawn')
        await self.server.permissions.register('bots.brmv')
        await self.server.permissions.register('bots.bconfig')

    async def populate(self, new_population: int):

        ACTIVE_COUNT = len(self.active_bots)

        if new_population < ACTIVE_COUNT:
            # Remove bots to match the new population
            bots_leaving = random.sample(self.active_bots, ACTIVE_COUNT - new_population)
            for BOT in bots_leaving:
                await BOT.handle_disconnected()
                self.active_bots.remove(BOT) # no need to update houdini population
        elif new_population > ACTIVE_COUNT:
            increase = new_population - ACTIVE_COUNT
            bots_sample = random.sample(self.accounts, min(increase, len(self.accounts)))

            if len(bots_sample) < increase:
                # Create additional bots
                extra_accounts = increase - len(bots_sample)
                new_bots = await self.create_bots(extra_accounts)
                bots_sample += new_bots

            for BOT in [PenguinBot(b.id, self).load_data(b) for b in bots_sample]:
                self.active_bots.append(BOT)
                await BOT.initialize()
                BOT.begin_activity()
        else:
            return
        await self.update_houdini()

    async def update_houdini(self):
        await self.server.redis.hset('houdini.population', self.server.config.id, len(self.server.penguins_by_id)) 
        self.server.logger.info(f'Server {self.server.config.id} population: {len(self.server.penguins_by_id)}')

    @commands.command('bpop')
    @permissions.has_or_moderator('bots.bpop')
    async def change_bots_population(self, p, new_population: int):
        asyncio.create_task(self.populate(new_population))

    @commands.command('bpurge')
    @permissions.has_or_moderator('bots.bpurge')
    async def remove_all_bots(self, p):
        for penguin in list(self.server.penguins_by_username.values()): # use a copy to avoid dictionary changed size during iteration
            if isinstance(penguin, PenguinBot):
                await penguin.handle_disconnected()
                if penguin in self.active_bots:
                    self.active_bots.remove(penguin)
        if self.accounts:
            ids = [account.id for account in self.accounts]
            await Penguin.delete.where((Penguin.id.in_(ids)) & (Penguin.character == None)).gino.status()
            self.accounts = []

    def random_name(self):
        name_generators = [
            names.elf,
            names.dwarf,
            names.hobbit,
            names.french,
            names.anglo,
            names.human,
        ]
        random_name = random.choice(name_generators)()
        self.server.logger.info(f"{random_name} has been created")
        return random_name

    async def create_bots(self, bots_needed: int):

        existing_names = await Penguin.select('username').gino.all()

        password = self.config.get('bots_password') or secrets.token_urlsafe(32)
        hashed_password = self._hash_password(password)

        unique_names = []
        bots = []

        while len(unique_names) < bots_needed:
            name = self.random_name()
            if name not in existing_names and name not in unique_names:
                unique_names.append(name)  
                bots.append(await self.create_penguin_bot(name, hashed_password))
                await asyncio.sleep(0.2)

        return bots
 
    def _hash_password(self, password: str) -> str:
        """Hash the password using bcrypt and Houdini's crypto functions."""
        hashed_password = Crypto.hash(password).upper()
        hashed_password = Crypto.get_login_hash(hashed_password, rndk=self.dash_static_key)
        return bcrypt.hashpw(hashed_password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')   

    async def create_penguin_bot(self, name: str, hashed_password: str) -> Penguin:
        """Create a single penguin and assign attributes, items, and inventory."""
        email = f'{name.lower()}@{self.email_domain}'
        return await self._create_penguin_in_db(name, email, hashed_password)
    
    async def _create_penguin_in_db(self, name, email, hashed_password):
        """Create the penguin in the database and assign attributes."""
        try:
            async with self.server.db.transaction():
                color = random.randrange(2, 14)
                penguin = await Penguin.create(
                    username=name.lower()[:12], nickname=name, password=hashed_password,
                    email=email, color=int(color), approval_en=True, active=True
                )
                await PenguinAttribute.create(penguin_id=penguin.id, name="BOT", value="true")
                await PenguinItem.create(penguin_id=penguin.id, item_id=int(color))
                await self.assign_clothing(penguin)
                self.accounts.append(penguin)
                return penguin
        except Exception as e:
            self.server.logger.warn(f'Skipping creation of {name}: {e}')
            return None

    async def assign_clothing(self, penguin):
        if self.has_inventory:
            await penguin.update(**{
                'head': random.choice(self.items_categorized[ITEM_TYPE.HEAD]).id,
                'face': random.choice(self.items_categorized[ITEM_TYPE.FACE]).id,
                'neck': random.choice(self.items_categorized[ITEM_TYPE.NECK]).id,
                'body': random.choice(self.items_categorized[ITEM_TYPE.BODY]).id,
                'hand': random.choice(self.items_categorized[ITEM_TYPE.HAND]).id,
                'feet': random.choice(self.items_categorized[ITEM_TYPE.FEET]).id,
                'flag': random.choice(self.items_categorized[ITEM_TYPE.FLAG]).id,
                'photo': random.choice(self.items_categorized[ITEM_TYPE.PHOTO]).id
            }).apply()

    async def _penguin(self, username: str):
        penguin_id = await Penguin.select('id').where(Penguin.username == username).gino.first()
        if penguin_id:
            penguin_id = int(penguin_id[0])
            return self.server.penguins_by_id.get(penguin_id) # is added to the server registry
        return None

    @commands.command('restyle') # replicate player clothing
    @permissions.has_or_moderator('bots.restyle')
    async def replicate_clothing(self, p, name: str = ""):
        if (BOT := await self._penguin(name.lower())) and isinstance(BOT, PenguinBot):
            await BOT.update(**{ # The data/Penguin class inherits from db.Model, which has the `update()` method for Python Gino() with PostgreSQL. For persistence storage of your fashion designs.
                'color': p.color,
                'head': p.head,
                'face': p.face,
                'neck': p.neck,
                'body': p.body,
                'hand': p.head,
                'feet': p.feet,
                'flag': p.flag,
                'photo': p.photo
            }).apply()
            await BOT.room_sync_clothing()

    @commands.command('spawn')
    @permissions.has_or_moderator('bots.spawn')
    async def make_custom_bots(self, p, *args: str):
        
        name = ' '.join(args)

        m = await Penguin.query.where(Penguin.username == name.lower()).gino.first()

        if m:

            p.logger.info(f"{p.nickname}: A rare {m.nickname} has appeared in {p.room.name}")

            BOT = PenguinBot(m.id, self).load_data(m)
            BOT.called = True

            if m.username not in {BOT.username for BOT in self.accounts} or (m.id not in self.server.penguins_by_id):

                attributed = await PenguinAttribute.query.where(PenguinAttribute.penguin_id == m.id).gino.first()

                if not attributed:
                    await PenguinAttribute.create(penguin_id=m.id, name="BOT", value="true")

                await BOT.initialize()
                self.accounts.append(BOT)
                self.active_bots.append(BOT)
                self.spawned.append(BOT)
                await self.update_houdini()

            await BOT.go_player_room(p, p.room)
            BOT.begin_activity()
            
        else:
            p.logger.info(f"{p.nickname}: There is no penguin named '{name}'")

    @commands.command('brmv')
    @permissions.has_or_moderator('bots.brmv')
    async def remove_custom_bots(self, p, *name: str):

        name = ' '.join(name)
        name = name.lower()

        if (m := await self._penguin(name)):
            p.logger.info(f"{p.nickname} has despawned {m.nickname}")

            if m.username in {BOT.username for BOT in self.accounts}:
                    self.spawned.remove(m)
                    await m.handle_disconnected()
                    await self.update_houdini()
                    self.active_bots = [b for b in self.active_bots if b.id != m.id]
                    self.accounts = [b for b in self.accounts if b.id != m.id]
                    await PenguinAttribute.delete.where(
                        (PenguinAttribute.penguin_id == m.id) & (PenguinAttribute.name == "BOT")
                    ).gino.status()

    @commands.command('bconfig') # add more if required
    @permissions.has_or_moderator('bots.bconfig')
    async def config_setting(self, p, *setting: str):

        setting = ' '.join(setting)
        setting = setting.lower()

        p.logger.info(f"setting {setting}")

        settings_map = { # maps queries to actual settings
            'random greeting': 'greeting_enabled',
            'random frames': 'ENABLE_RANDOM_FRAME',
            'random spots': 'ENABLE_SPOT_LOCATIONS',
            'random movements': 'ENABLE_RANDOM_MOVEMENT',
        }
        if setting in settings_map:
            attribute = settings_map[setting]
            setattr(self, attribute, not getattr(self, attribute))
            p.logger.info(f"{attribute} is now {'enabled' if getattr(self, attribute) else 'disabled'}")
        else:
            p.logger.info(f"Setting '{setting}' Invalid. Available settings: {', '.join(settings_map.keys())}")

    async def _rotation(self):
        """Rotate bots in and out of the game periodically."""
        while True:
            await asyncio.sleep(random.choice(self.rotation_interval))
            await self._rotate_active_bots()

    async def _rotate_active_bots(self):
        """Handles disconnects and reconnects bots - replacing active bots."""
        if len(self.accounts) > 2 and len(self.active_bots) > 2:
            bots_can_join = [BOT for BOT in self.accounts if BOT.id not in self.server.penguins_by_id]
            
            if not bots_can_join:
                self.server.logger.info("No available bots to join. Skipping rotation.")
                return
            
            b_joining = random.choice(bots_can_join)
            b_joining = PenguinBot(b_joining.id, self).load_data(b_joining)
            
            bots_can_leave = [BOT for BOT in self.active_bots if not BOT.called]

            if not bots_can_leave:
                self.server.logger.info("No active bots can leave.")
                return

            b_leaving = random.choice(bots_can_leave)
            self.active_bots = [bot for bot in self.active_bots if bot.id != b_leaving.id]
            await b_leaving.handle_disconnected()
            await b_joining.initialize()
            b_joining.begin_activity()
            self.active_bots.append(b_joining)

    def being_followed(self, p, b):
        return b.following_penguin is not None and b.following_penguin.id == p.id

    @handlers.handler(XTPacket('j', 'jr'))
    async def on_player_join_room(self, p, room: Room, *_):
        """Handle bots joining - finding players and greeting players"""
        Tasks = []
        for b in self.active_bots:
            if self.being_followed(p,b):
                Tasks.append(b.go_player_room(p, room))
            elif p.room.id == b.room.id and self.greeting_enabled and len(p.room.penguins_by_id) < 4 and not b.called:
                Tasks.append(b.give_greeting())
        if Tasks:
            await asyncio.gather(*Tasks)

    @handlers.handler(XTPacket('u', 'sp'))
    async def handle_player_movements(self, p, x: int, y: int):
        Tasks = []
        for b in self.active_bots:
            if p.room and b.room and self.being_followed(p,b) and p.room.id == b.room.id:
                Tasks.append(b.goto_coordinates(p, x, y))
        if Tasks:
            await asyncio.gather(*Tasks)

    @handlers.handler(XTPacket('u', 'sb'))
    async def handle_player_snowball(self, p, x: int, y: int):
        """Handle bots reacting to snowball"""
        await asyncio.gather(*(bot.handle_snowball(p, x, y) for bot in self.active_bots))

    @handlers.handler(XTPacket('u', 'ss'))
    async def handle_player_safe_message(self, p, message_id: int):
        """Handle bots reacting to safe messages."""
        await asyncio.gather(*(bot.handle_safe_message(p, message_id) for bot in self.active_bots))

    @handlers.handler(XTPacket('jw', ext='z'))
    async def handle_player_join_waddle(self, p, waddle_id: int): # sled racing
        if waddle_id not in p.room.waddles:
            return
        waddle: RoomWaddle = p.room.waddles[waddle_id]

        try:
            bots_chosen = random.sample(self.active_bots, waddle.seats - 1)
            await asyncio.gather(*(bot.enter_waddle(p, waddle) for bot in bots_chosen))

        except ValueError:
            self.server.logger.error("More bots are needed to join a session")

    @handlers.handler(XTPacket('m', 'sm'))
    @handlers.cooldown(.5)
    async def handle_LLM_query(self, p, _id: int, message: str):

        if _id != p.id:
            return await p.close()

        if p.muted:
            for penguin in p.room.penguins_by_id.values():
                if not penguin.moderator:         
                    return

        if p.server.chat_filter_words:
            tokens = message.lower().split()
            if next((c for w, c in p.server.chat_filter_words.items() if w in tokens), None):
                return

        try:
            if has_command_prefix(p.server.config.command_prefix, message):
                return

            else:
                participants = []
                for b in self.spawned:
                    reason = None
                    if b.room.id != p.room.id:
                        reason = f"{b.nickname}: {b.room.id} is not in the same room as {p.nickname}: {p.room.id}."
                    elif b.talking:
                        reason = f"{b.nickname} is currently talking."
                    elif b.nickname not in PersonaFileCreator.personas.keys():
                        reason = f"{b.nickname} does not have a persona."
                    if reason:
                        p.logger.info(reason)
                    else:
                        participants.append(b)

                p.logger.info(f"eligible participants {[s.nickname for s in participants]}")

                if participants:
                    sample_participants = await converse.do_sample(participants)
                    p.logger.info(f"sample participants {[s.nickname for s in sample_participants]}")
                    await converse.new_conversation(message, sample_participants, p)    

        except UnknownCommandException as e:
            self.server.logger.error(f"UnknownCommandException: {e}")
            return