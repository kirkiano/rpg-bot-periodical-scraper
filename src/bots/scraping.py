import datetime
import asyncio
import random
from collections import defaultdict, namedtuple

from .general import Bot
from connect import Connection


class ScrapingBot(Bot):

    Params = namedtuple('Params', 'ntitles, waitleave, waitdl')

    def __init__(self, name, ioloop, download_func, params,
                 do_shuffle=True, verbose=False):
        """
        Args:
            name (string): bot name
            ioloop (asyncio.ioloop):
            download_func: downloads and scrapes this bot's target content
            params (ScrapingBot.Params):
            do_shuffle (bool): randomize the order of headlines
            verbose (bool):
        """
        super(ScrapingBot, self).__init__(name, ioloop, verbose=verbose)
        self.download_func = download_func
        self.params = params
        self.do_shuffle = do_shuffle
        self.headlines = []
        self.seen = defaultdict(set)

        # set time of last download far enough in the
        # past to trigger a fresh download
        long_interval = datetime.timedelta(minutes=1 + params.waitdl)
        self.t_last_download = datetime.datetime.now() - long_interval

    @property
    def credentials(self):
        return Connection.Credentials(self.name, self.name)

    async def run(self):
        """
        Connect to the game, download target content specific to this bot, and
        walk around from room to room, announcing headlines from the content.
        """
        while True:
            self.location = (await self.conn.wait_for_place()).location
            if self.verbose:
                print(f'{self.conn.user} is now in {self.location.name}.')
            await self._maybe_scrape()
            if self.verbose:
                print(f'{self.conn.user} has downloaded its content.')
            await self._speak_headlines()
            wait_to_move = random.uniform(0, self.params.waitleave)
            await asyncio.sleep(wait_to_move)
            await self._take_random_exit()

    async def _maybe_scrape(self):
        """
        Download and scrape the target content if enough time has passed since
        the last time it was scraped.
        """
        t_now = datetime.datetime.now()
        wait_to_download = random.uniform(0, self.params.waitdl)
        waiting_time = datetime.timedelta(minutes=wait_to_download)
        if t_now - self.t_last_download > waiting_time:
            self.headlines = await self.download_func()
            self.t_last_download = t_now

    async def _speak_headlines(self):
        """
        Announce (at most) the next ntitles headlines.
        """
        unseen_headlines = [p for p in self.headlines
                            if p['id'] not in self.seen[self.location.id]]
        if self.do_shuffle:
            random.shuffle(unseen_headlines)
        num_headlines_to_speak = min(self.params.ntitles, len(unseen_headlines))
        for headline in unseen_headlines[:num_headlines_to_speak]:
            saying = headline['title'].strip()
            await self.conn.say(saying)
            if self.verbose:
                print(f'{self.conn.user} has said: {saying}.')
            self.seen[self.location.id].add(headline['id'])

    async def _take_random_exit(self):
        """Leave the current location by an exit chosen at random."""
        chosen_exit = random.choice([e.id for e in self.location.exits])
        await self.conn.take_exit(chosen_exit)