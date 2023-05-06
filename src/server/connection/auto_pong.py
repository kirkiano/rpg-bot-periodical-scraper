from abc import ABCMeta, abstractmethod
import asyncio

from message import Ping, GameOver
from request import Pong
from .base import Connection


class AutoPongConnection(Connection):
    """
    Abstract class that responds automatically to pings.
    To achieve this, method enqueue_non_ping_message should
    be run as a separate task. Client code, including subclasses,
    should *not* call recv_message, and should receive messages
    by calling recv_non_ping_message instead.

    The superclass's wait_for is appropriately overriden.
    """

    __metaclass__ = ABCMeta

    @staticmethod
    def create():
        conn = AutoPongConnection()
        task = asyncio.create_task(conn.enqueue_non_ping_messages())
        return conn, task

    def __init__(self):
        """
        This constructor is not meant to be called by any function
        except AutoPongConnection.create.
        """
        super().__init__()
        self._msgs = asyncio.Queue()

    async def enqueue_non_ping_messages(self):
        """
        Filters out incoming Pings, and responds to them with Pongs.
        """
        try:
            while True:
                msg = await self.recv_message()
                if isinstance(msg, Ping):
                    await self.send_request(Pong())
                else:
                    await self._msgs.put(msg)
        except Connection.EOF as e:
            # Enqueuing the exception allows the bot's main task to
            # pick it up and allows this task to conclude gracefully.
            await self._msgs.put(e)

    async def recv_non_ping_message(self):
        msg = await self._msgs.get()
        if isinstance(msg, Connection.EOF):
            raise msg
        else:
            return msg

    async def wait_for(self, cls):
        """
        Like the superclass's wait_for, except cls must not be Ping,
        as a Ping will never be returned.
        """
        while True:
            msg = await self.recv_non_ping_message()
            if isinstance(msg, GameOver):
                raise msg
            elif isinstance(msg, cls):
                return msg

    @property
    @abstractmethod
    def server(self):
        """
        Description of the server to which self is connected (a string)
        """
        raise NotImplementedError('Server.server not implemented')

    @abstractmethod
    async def send_request(self, request):
        """
        Args:
            request (CharRequest)
        Returns: None
        """
        raise NotImplementedError('Server.send_request not implemented')

    @abstractmethod
    async def recv_message(self):
        """
        Get the next CharMessage from the server.

        Returns:
            CharMessage
        """
        # Used by self.handle_next_message. Not meant to be used by clients.
        raise NotImplementedError('Server.recv_message not implemented')
