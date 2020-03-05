import random
from abc import ABCMeta, abstractmethod
from traceback import print_exc

from .connect import Connection
from common.server_message import Exits


class Bot(object):
    """Abstract class implementing a bot."""
    __metaclass__ = ABCMeta

    def __init__(self, server, credentials, ioloop, verbose=False):
        """
        Args:
            server (Connection.Server): server that this bot should connect to
            credentials (Connection.Credentials): credentials to login to server
            ioloop (asyncio.ioloop):
            verbose (bool):
        """
        super(Bot, self).__init__()
        self.server = server
        self.credentials = credentials
        self.ioloop = ioloop
        self.verbose = verbose
        self.conn = None

    @property
    def name(self):
        return self.credentials.user

    def is_connected(self):
        return bool(self.conn)

    async def connect(self):
        self.conn = await Connection.login(
            server=self.server,
            credentials=self.credentials,
            ioloop=self.ioloop)
        if self.verbose:
            print(f'{self.name} has connected to the RPG server.')

    @abstractmethod
    async def run(self):
        """The bot's main action"""
        pass

    async def connect_and_run_safely(self):
        """
        Safety wrapper for run(). Ensures that a crashing bot does not also
        crash the whole program.
        """
        try:
            await self.connect()
            await self.run()
        except Exception:  # catching all Exceptions is NOT too broad here
            print()
            print(f'{self.name} crashed:')
            print_exc()

    async def take_random_exit(self, is_good_exit=lambda _: True):
        """
        Leave the current place by an exit chosen at random, as long as
        the exit satisfies is_good_exit.
        """
        await self.conn.ways_out()
        exits = (await self.conn.wait_for(Exits)).exits
        valid_exit_ids = [e.id for e in exits if is_good_exit(e)]
        if valid_exit_ids:
            chosen_exit = random.choice(valid_exit_ids)
            await self.conn.take_exit(chosen_exit)