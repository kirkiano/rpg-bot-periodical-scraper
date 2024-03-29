import logging
import random
import asyncio

from exn import RPGException
from action import Action
from .confine import NoConfinement
from message import Place, WaysOut


logger = logging.getLogger('roam')
logger.propagate = False


class RoamingAction(Action):
    """
    Action that lets a bot roam
    """

    class NoValidExit(RPGException):
        def __init__(self, place):
            """
            Args:
                place (Place): the dead end
            """
            super().__init__(f'no valid exit available from {place}')

    def __init__(self, waitleave, action=Action(), confine=NoConfinement()):
        """
        Args:
            waitleave (int): maximum number of seconds to wait before
                             moving to neighbor
            action (Action): action to execute between movements
            confine (Confine): confinement. Defaults to no confinement.
        """
        self.waitleave = waitleave
        self.action = action
        self.confine = confine

    async def __call__(self, bot):
        """
        Args:
            bot (Bot):
        """
        bot.place = (await bot.wait_for(Place)).place
        logger.info(f'{bot.name} is now in {bot.place}')
        self.confine.assert_within_bounds(bot.place)
        bot.exits = (await bot.wait_for(WaysOut)).exits
        await self.action(bot)
        waiting_period = random.uniform(0, self.waitleave)
        await asyncio.sleep(waiting_period)
        await self.take_random_exit(bot)

    async def take_random_exit(self, bot):
        """
        Leave the current place by an exit chosen at random, as long as
        the exit satisfies is_good_exit.
        """
        valid_exits = [e for e in bot.exits if self.confine.is_valid_exit(e)]
        valid_exit = random.choices(valid_exits)
        if valid_exit:
            valid_exit = valid_exit[0]  # shadow!
            logger.debug(f'{bot.name} going {valid_exit.direction} '
                         f'to {valid_exit.neighbor}')
            await bot.take_exit(valid_exit.id)
        else:
            raise RoamingAction.NoValidExit(bot.place)
