from prompt_toolkit import prompt_async
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit import prompt

import asyncio
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner

from autobahn.wamp.types import ComponentConfig


class ShellClient(ApplicationSession):

    async def onJoin(self, details):

        self._ticks = 0
        def on_tick(tick):
            self._ticks += 1

        await self.subscribe(on_tick, u'com.example.tick')

    def onDisconnect(self):
        loop = asyncio.get_event_loop()
        loop.stop()


def run():
    cfg = ComponentConfig(u"realm1", {})
    session = ShellClient(cfg)
    runner = ApplicationRunner(u"ws://localhost:8080/ws", u"realm1")
    runner.run(session, start_loop=False)
    return session
