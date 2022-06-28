import sys
import inspect
import discord
import unicodedata
from utilities import (
    Utilities,
    get_question_id,
    is_test_response,
    is_test_message,
    is_test_question,
    get_git_branch_info,
)
from modules.module import Response
from collections.abc import Iterable
from datetime import datetime, timezone, timedelta
from config import (
    discord_token,
    bot_dev_channel_id,
    TEST_RESPONSE_PREFIX,
    maximum_recursion_depth,
)


class DiscordHandler():

    def __init__(self):
        self.utils = Utilities.get_instance()
        self.modules = self.utils.modules_dict.values()
        """
        All Discord Functions need to be under another function in order to
        use self.
        """
        @self.utils.client.event
        async def on_ready() -> None:
            print(f"{self.utils.client.user} has connected to Discord!")
            print("searching for a guild named '%s'" % self.utils.GUILD)
            print(self.utils.client.guilds)
            guild = discord.utils.get(self.utils.client.guilds, name=self.utils.GUILD)
            if guild is None:
                raise Exception("Guild Not Found : '%s'" % self.utils.GUILD)

            print("found a guild named '%s' with id '%s'" % (guild.name, guild.id))

            members = "\n - ".join([member.name for member in guild.members])
            print(f"Guild Members:\n - {members}")
            await self.utils.client.get_channel(bot_dev_channel_id).send(f"I just (re)started {get_git_branch_info()}!")

        @self.utils.client.event
        async def on_message(message: discord.message.Message) -> None:
            # don't react to our own messages unless running test
            message_author_is_stampy = message.author == self.utils.client.user
            if is_test_message(message.clean_content) and self.utils.test_mode:
                print("TESTING " + message.clean_content)
            elif message_author_is_stampy:
                for module in self.modules:
                    module.process_message_from_stampy(message)
                return

            # This is mostly working but it's commented out for now.
            # from utilities.discordutils import DiscordMessage
            # message = DiscordMessage(message)

            print("########################################################")
            print(datetime.now().isoformat(sep=" "))
            if hasattr(message.channel, "name"):
                print(f"Message: id={message.id} in '{message.channel.name}' (id={message.channel.id})")
            else:
                print(f"DM: id={message.id}")
            print(f"from {message.author.name}#{message.author.discriminator} (id={message.author.id})")
            if message.reference:
                print("In reply to:", message.reference)
            print(f"    {message.content}")
            print("#####################################")

            if hasattr(message.channel, "name") and message.channel.name == "general":
                print("the latest general discord channel message was not from stampy")
                self.utils.last_message_was_youtube_question = False

            responses = [Response()]
            for module in self.modules:
                print(f"# Asking module: {module}")
                response = module.process_message(message)
                if response:
                    response.module = module  # tag it with the module it came from, for future reference

                    if response.callback:  # break ties between callbacks and text in favour of text
                        response.confidence -= 0.001

                    responses.append(response)

            print("#####################################")

            for i in range(maximum_recursion_depth):  # don't hang if infinite regress
                responses = sorted(responses, key=(lambda x: x.confidence), reverse=True)

                # print some debug
                print("Responses:")
                for response in responses:
                    if response.callback:
                        args_string = ", ".join([a.__repr__() for a in response.args])
                        if response.kwargs:
                            args_string += ", " + ", ".join(
                                [f"{k}={v.__repr__()}" for k, v in response.kwargs.items()]
                            )
                        print(
                            f"  {response.confidence}: {response.module}: `{response.callback.__name__}("
                            f"{args_string})`"
                        )
                    else:
                        print(f'  {response.confidence}: {response.module}: "{response.text}"')
                        if response.why:
                            print(f'       (because "{response.why}")')

                top_response = responses.pop(0)

                if top_response.callback:
                    print("Top response is a callback. Calling it")
                    if inspect.iscoroutinefunction(top_response.callback):
                        new_response = await top_response.callback(*top_response.args, **top_response.kwargs)
                    else:
                        new_response = top_response.callback(*top_response.args, **top_response.kwargs)

                    new_response.module = top_response.module
                    responses.append(new_response)
                else:
                    if top_response:
                        if self.utils.test_mode:
                            if is_test_response(message.clean_content):
                                return  # must return after process message is called so that response can be evaluated
                            if is_test_question(message.clean_content):
                                top_response.text = (
                                    TEST_RESPONSE_PREFIX + str(get_question_id(message)) + ": " + top_response.text
                                )
                        print("Replying:", top_response.text)
                        # TODO: check to see if module is allowed to embed via a config?
                        if top_response.embed:
                            await message.channel.send(top_response.text, embed=top_response.embed)
                        elif isinstance(top_response.text, str):
                            # Discord allows max 2000 characters, use a list or other iterable to sent multiple messages for longer text
                            await message.channel.send(top_response.text[:2000])
                        elif isinstance(top_response.text, Iterable):
                            for chunk in top_response.text:
                                await message.channel.send(chunk)
                    print("########################################################")
                    sys.stdout.flush()
                    return

            # if we ever get here, we've gone maximum_recursion_depth layers deep without the top response being text
            # so that's likely an infinite regress
            message.channel.send("[Stampy's ears start to smoke. There is a strong smell of recursion]")

        @self.utils.client.event
        async def on_socket_raw_receive(_) -> None:
            """
            This event fires whenever basically anything at all happens.
            Anyone joining, leaving, sending anything, even typing and not sending...
            So I'm going to use it as a kind of 'update' or 'tick' function,
            for things the bot needs to do regularly. Yes this is hacky.
            Rate limit these things, because this function might be firing a lot
            """

            # keep the log file fresh
            sys.stdout.flush()

            # give all the modules a chance to do things
            for module in self.modules:
                await module.tick()

            # never fire more than once a second
            if self.utils.rate_limit("on_socket_raw_receive", seconds=1):
                return

            # this is needed for later checks, which should all be replaced with rate_limit calls (TODO)
            now = datetime.now(timezone.utc)

            # check for new youtube comments
            new_comments = self.utils.check_for_new_youtube_comments()
            if new_comments:
                for comment in new_comments:
                    if "?" in comment["text"]:
                        self.utils.add_youtube_question(comment)
            # add_question should maybe just take in the dict, but to make sure
            # nothing is broken extra fields have been added as optional params
            # This is just checking if there _are_ questions
            question_count = self.utils.get_question_count()
            if question_count:
                # ask a new question if it's been long enough since we last asked one
                question_ask_cooldown = timedelta(hours=12)

                if (now - self.utils.last_question_asked_timestamp) > question_ask_cooldown:
                    if not self.utils.last_message_was_youtube_question:
                        # Don't ask anything if the last thing posted in the chat was stampy asking a question
                        self.utils.last_question_asked_timestamp = now
                        # this actually gets the question and sets it to asked, then sends the report
                        report = self.utils.get_question(order_type="LATEST")
                        guild = discord.utils.find(lambda g: g.name == self.utils.GUILD, self.utils.client.guilds)
                        general = discord.utils.find(lambda c: c.name == "general", guild.channels)
                        await general.send(report)
                        self.utils.last_message_was_youtube_question = True
                    else:
                        # wait the full time again
                        self.utils.last_question_asked_timestamp = now
                        print("Not asking question: previous post in the channel was a question stampy asked.")
                else:
                    remaining_cooldown = str(question_ask_cooldown - (now - self.utils.last_question_asked_timestamp))
                    print("%s Questions in queue, waiting %s to post" % (question_count, remaining_cooldown))
                    return

        @self.utils.client.event
        async def on_raw_reaction_add(payload: discord.raw_models.RawReactionActionEvent) -> None:
            print("RAW REACTION ADD")
            if len(payload.emoji.name) == 1:
                # if this is an actual unicode emoji
                print(unicodedata.name(payload.emoji.name))
            else:
                print(payload.emoji.name.upper())
            print(payload)

            for module in self.modules:
                await module.process_raw_reaction_event(payload)

        @self.utils.client.event
        async def on_raw_reaction_remove(payload: discord.raw_models.RawReactionActionEvent) -> None:
            print("RAW REACTION REMOVE")
            print(payload)

            for module in self.modules:
                await module.process_raw_reaction_event(payload)

    def start(self):
        self.utils.client.run(discord_token)