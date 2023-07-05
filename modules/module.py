from typing import Optional, Callable
from dataclasses import dataclass, field

import discord


class Validator:
    self.description: str
    self.f: Callable[[str], bool]

    def __init__(self, description: str, f: Callable):
        self.description = description
        self.f = f
    def __repr__(self):
        return self.description

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__repr__ == other.__repr__
        else:
            return False


@dataclass
class Option:
    self.name: str
    self.validator: Optional[Validator] = None

    def __repr__(self):
        name = self.name
        validator = self.validator
        return (
            "Option("
            + f"{name=}"
            + (f"{validator=}" if validator else "")
            + ")"
        )

@dataclass
class Response:
    """The response a module gives.
    Two types of response are possible:
        1. Text responses, with a string and a confidence rating, and
        2. Callback responses, with a (possibly async) function, args/kwargs for the function,
           and the *optimistic expected confidence of the function's response*
    Set `text` or `callback`, not both.

    For example, suppose the incoming message says "What is AIXI?"
    One module may spot that this is a question, and generate a quick joke as a text response:

        Response(text="https://www.google.com/search?q=AIXI", confidence=2)

    This means "This module suggests Stampy give the user a link to a google search for 'AIXI',
    but only with confidence 2/10, because that's a weak response"
    If no other module responds with confidence 2 or more, Stampy will give the google link response.

    If a module needs to respond with multiple Discord messages (e.g. for messages over 2000 characters
    that need manual splitting, or for asynchronous operations over multiple items like wiki edits), it
    can use a list, a generator, or another iterable:

        Response(text=["a", "b", "c"], confidence=9)

    Another module may spot that "What is AIXI?" is a question it may be able to actually answer well,
    but it doesn't know without slow/expensive operations that we don't want to do if we don't have to,
    like hitting a remote API or running a large language model. So it generates a callback response:

        Response(callback=self.search_alignment_forum_tags,
                 args=["AIXI"],
                 kwargs={'type'='exact_match'},
                 confidence=8
                )

    This means "This module has the potential for a confidence 8 response (in this case, if the
    Alignment Forum has a tag with the exact string the user asked about), but do check that there are
    no better options first, before we hit the Alignment Forum API.
    If another module responds with confidence 9 or 10, the callback function is never called,
    but if the callback response's given confidence is the highest of any response, we call

        await search_alignment_forum_tags("AIXI", type='exact_match')

    This function will return a Response object in exactly the same way.
    For example, if the search finds a hit:

        Response(text="AIXI is a mathematical formalism for a hypothetical (super)intelligence, "
                      "developed by Marcus Hutter.\n"
                      "See <https://www.alignmentforum.org/tag/aixi> for more",
                 confidence=8
                )

    Or if there's no match for the search:

        Response(text="I don't know, there's no alignment forum tag for that", confidence=1)

    Callback functions can also return callback responses, so the process can be recursive.
    Please do not do anything stupid with this.

    Picking confidence levels to give for callbacks is kind of subtle. You're effectively saying

    "What confidence of response would another module have to give, such that it would be not worth
    running this callback?". This will vary depending on: how good the response could be, how likely
    a good response is, and how slow/expensive the callback function is.
    """

    embed: Optional[discord.Embed] = None
    confidence: float = 0.0
    text: Union[str, Iterable[str]] = ""
    callback: Optional[Callable] = None
    args: list = field(default_factory=list)
    kwargs: dict = field(default_factory=dict)

    module: object = None

    why: str = ""

    def __bool__(self):
        return bool(self.text) or bool(self.callback) or bool(self.confidence)

    def __repr__(self) -> str:
        embed = self.embed
        confidence = self.confidence
        text = self.text
        callback = self.callback.__name__ if self.callback else None
        args = self.args
        kwargs = self.kwargs
        module = str(self.module)
        why = self.why
        return (
            "Response("
            + (f"{embed=} " if embed else "")
            + f"{confidence=} "
            + (f"{text=} " if text else "")
            + (f"{callback=} " if callback else "")
            + (f"{args=} " if args else "")
            + (f"{kwargs=} " if kwargs else "")
            + (f"{module=} " if module else "")
            + (f"{why=}" if why else "")
            + ")"
        )
