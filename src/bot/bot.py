import logging
import traceback

from exn import RPGException
from server.connection import Connection  # noqa: F401
from message import Welcome, GameOver
from action import Action
from request import Say, TakeExit


logger = logging.getLogger('bot')
logger.propagate = False


class Bot(object):
    """
    Abstract class implementing a bot.
    """

    @staticmethod
    async def create(connection, action=Action()):
        """
        Convenience that waits for server's Welcome before
        constructing a scraping bot. See __init__'s docstring.

        Diversity of bot behavior is achieved by varying action,
        which takes the bot itself as argument. This arrangment,
        which amounts to an inversion of dependency, is cleaner,
        and may also be more flexible, than the alternative of
        subtyping this class (Bot), as it keeps separate the state
        of Bot from the state of Action.

        Args:
            connection: see __init__
            action (Action): the action to be performed during each
                             iteration of the bot's loop.

        Returns:
            Bot
        """
        welcome = await connection.wait_for(Welcome)
        return Bot(connection, welcome.name, action)

    def __init__(self, connection, name, action):
        """
        Args:
            connection (Connection):
            name (str):
            action (Action): the bot's action
        """
        super().__init__()
        connection.username = name
        self._conn = connection
        self._action = action
        self._place = None
        self._exits = []

    @property
    def name(self):
        return self._conn.username

    @property
    def place(self):
        """
        Returns (Place): current place, or None if not yet Welcomed
        """
        return self._place

    @place.setter
    def place(self, place):
        self._place = place

    def is_connected(self):
        return bool(self._conn)

    async def run(self):
        try:
            while True:
                await self._action(self)
        except GameOver as e:
            logger.info(f'{self.name} detected game-over: {e}')

    async def run_safely(self):
        """
        Safety wrapper for run(). Ensures that a crashing bot does not also
        crash the whole program.
        """
        logger.info(f'{self.name} is now running')
        try:
            await self.run()
        except Exception as e:  # for safety, catch all exceptions
            verb = 'failed' if isinstance(e, RPGException) else 'crashed'
            logger.fatal(f'{self.name} {verb}: {e}')
            traceback.print_exception(e)

    #######################################################
    # requests

    async def take_exit(self, eid):
        await self._conn.send_request(TakeExit(eid))

    async def say(self, speech):
        await self._conn.send_request(Say(speech))

    async def wait_for(self, cls):
        return await self._conn.wait_for(cls)
