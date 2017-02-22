from prompt_toolkit import prompt_async
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit import prompt

import asyncio
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner

from autobahn.wamp.types import ComponentConfig


# http://python-prompt-toolkit.readthedocs.io/en/stable/pages/building_prompts.html#input-validation
class NumberValidator(Validator):

    def validate(self, document):
        text = document.text

        if text and not text.isdigit():
            i = 0

            # Get index of fist non numeric character.
            # We want to move the cursor here.
            for i, c in enumerate(text):
                if not c.isdigit():
                    break

            raise ValidationError(message='This input contains non-numeric characters',
                                  cursor_position=i)


class MyComponent(ApplicationSession):

    async def onJoin(self, details):
        #print('Connected!')

        self._ticks = 0
        def onevent():
            self._ticks += 1
            #print('got event')
        await self.subscribe(onevent, u'com.example.tick')

        #print('session ready')

        return

        # we are waiting for user input now - but without blocking!
        # that is, eg the above event handler will continue to receive events while
        # the user is still not finished with input
        x = await prompt_async('x: ', validator=NumberValidator(), patch_stdout=False)

        # user input is validated (in above, against a number validator) - but the value is
        # still returned as string, and hence needs to be converted
        x = int(x)
        y = self._ticks
        res = await self.call(u'com.example.add2', x, y)

        print("RPC succeded: {} + {} = {}".format(x, y, res))
        self.leave()

    def onDisconnect(self):
        loop = asyncio.get_event_loop()
        loop.stop()


async def run2():
    cfg = ComponentConfig(u"ws://localhost:8080/ws", {})
    session = MyComponent(cfg)
    runner = ApplicationRunner(u"ws://localhost:8080/ws", u"realm1")
    await runner.run(session)
    print(session)
    return session
    #return runner.run(MyComponent)


def run():
    cfg = ComponentConfig(u"realm1", {})
    session = MyComponent(cfg)
    runner = ApplicationRunner(u"ws://localhost:8080/ws", u"realm1")
    runner.run(session, start_loop=False)
    return session
    #return runner.run(MyComponent)
