import logging

from exn import RPGException
from action import Action


logger = logging.getLogger('speech')
logger.propagate = False


class BlabbingAction(Action):
    """
    Action that blabs, ie, says things without any regard to
    whether anyone is present to hear it.
    """

    class NoMoreSayings(RPGException):
        def __init__(self):
            super().__init__('No more sayings')

    def __init__(self, get_sayings):
        """
        Args:
            get_sayings: async function that returns a list of dicts,
                         each of which has a field 'id' and a field
                         'title'. The latter is what is spoken.
        """
        self.get_sayings = get_sayings
        self.sayings = []
        self.no_more = False

    async def __call__(self, bot):
        """
        When the sayings have run out, get_sayings is run again
        to fetch more.
        """
        if self.no_more:
            return
        if not self.sayings:
            # try refreshing the list of sayings
            self.sayings = [s['title'] for s in await self.get_sayings()]
            if not self.sayings:
                # still nothing, in spite of refresh
                self.no_more = True  # raise BlabbingAction.NoMoreSayings()
                return
        saying = self.sayings.pop().strip()
        logger.info(f'{bot.name} says, "{saying}"')
        await bot.say(saying)
