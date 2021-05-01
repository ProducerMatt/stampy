import re
import json
import discord
from modules.module import Module
from config import stampy_youtube_channel_id, youtube_testing_thread_url


class Reply(Module):
    def __str__(self):
        return "YouTube Reply Posting Module"

    def __init__(self):
        Module.__init__(self)

    @staticmethod
    def is_post_request(text):
        """Is this message asking us to post a reply?"""
        print(text)
        if text:
            return text.lower().endswith("post this") or text.lower().endswith("send this")
        else:
            return False

    @staticmethod
    def is_allowed(message):
        """[Deprecated] Is the message author authorised to make stampy post replies?"""
        posting_role = discord.utils.find(lambda r: r.name == "poaster", message.guild.roles)
        return posting_role in message.author.roles

    @staticmethod
    def extract_reply(text):
        """Pull the text of the reply out of the message"""
        lines = text.split("\n")
        reply_message = ""
        for line in lines:
            # pull out the quote syntax "> " and a user if there is one
            match = re.match(r"([^#]+#\d\d\d\d )?> (.*)", line)
            if match:
                reply_message += match.group(2) + "\n"

        return reply_message

    @staticmethod
    def post_reply(text, question_id):
        """Actually post the reply to YouTube. Currently this involves a horrible hack"""

        # first build the dictionary that will be passed to youtube.comments().insert as the 'body' arg
        body = {
            "snippet": {
                "parentId": question_id,
                "textOriginal": text,
                "authorChannelId": {"value": stampy_youtube_channel_id},
            }
        }

        # now we're going to put it in a json file, which CommentPoster.py will read and send it
        with open("database/topost.json") as post_file:
            responses_to_post = json.load(post_file)

        responses_to_post.append(body)

        with open("database/topost.json", "w") as post_file:
            json.dump(responses_to_post, post_file, indent="\t")

        print("dummy, posting %s to %s" % (text, question_id))

    def can_process_message(self, message, client=None):
        """From the Module() Interface. Is this a message we can process?"""
        if self.is_at_me(message):
            text = self.is_at_me(message)

            if self.is_post_request(text):
                print("this is a posting request")
                return 9, "Ok, I'll post this when it has more than 30 stamp points"

        return 0, ""

    async def process_message(self, message, client=None):
        """From the Module() Interface. Handle a reply posting request message"""
        return 0, ""

    async def post_message(self, message, approvers=None):
        if approvers is None:
            approvers = []
        approvers.append(message.author)
        approvers = [a.name for a in approvers]
        approvers = list(set(approvers))

        if len(approvers) == 1:
            approver_string = approvers[0]
        elif len(approvers) == 2:
            approver_string = " and ".join(approvers)
        else:
            approvers[-1] = "and " + approvers[-1]
            approver_string = ", ".join(approvers)

        # strip off stampy's name
        text = self.is_at_me(message)

        reply_message = self.extract_reply(text)
        reply_message += "\n -- _I am a bot. This reply was approved by %s_" % approver_string

        report = ""

        if message.reference:
            # if this message is a reply
            reference = await message.channel.fetch_message(message.reference.message_id)
            reference_text = reference.clean_content
            question_url = reference_text.split("\n")[-1].strip("<> \n")
            if "youtube.com" not in question_url:
                return "I'm confused about what YouTube comment to reply to..."
        else:
            if not self.utils.latest_question_posted:
                report = (
                    "I don't remember the URL of the last question I posted here,"
                    " so I've probably been restarted since that happened. I'll just"
                    " post to the dummy thread instead...\n\n"
                )
                # use the dummy thread
                self.utils.latest_question_posted = {"url": youtube_testing_thread_url}

            question_url = self.utils.latest_question_posted["url"]

        question_id = re.match(r".*lc=([^&]+)", question_url).group(1)

        quoted_reply_message = "> " + reply_message.replace("\n", "\n> ")
        report += "Ok, posting this:\n %s\n\nas a response to this question: <%s>" % (
            quoted_reply_message,
            question_url,
        )

        self.post_reply(reply_message, question_id)

        return report

    async def evaluate_message_stamps(self, message):
        """Return the total stamp value of all the stamps on this message, and a list of who approved it"""
        total = 0
        print("Evaluating message")

        approvers = []

        reactions = message.reactions
        if reactions:
            print(reactions)
            for reaction in reactions:
                reaction_type = getattr(reaction.emoji, "name", "")
                if reaction_type in ["stamp", "goldstamp"]:
                    print("STAMP")
                    users = await reaction.users().flatten()
                    for user in users:
                        approvers.append(user)
                        print("  From", user.id, user)
                        stampvalue = self.utils.modules_dict["StampsModule"].get_user_stamps(user)
                        total += stampvalue
                        print("  Worth", stampvalue)

        return total, approvers

    @staticmethod
    def has_been_replied_to(message):
        reactions = message.reactions
        print("Testing if question has already been replied to")
        print("The message has these reactions:", reactions)
        if reactions:
            for reaction in reactions:
                reacttype = getattr(reaction.emoji, "name", reaction.emoji)
                print(reacttype)
                if reacttype in ["📨", ":incoming_envelope:"]:
                    print("Message has envelope emoji, it's already replied to")
                    return True
                elif reacttype in ["🚫", ":no_entry_sign:"]:
                    print("Message has no entry sign, it's vetoed")
                    return True

        print("Message has no envelope emoji, it has not already replied to")
        return False

    async def process_raw_reaction_event(self, event, client=None):
        emoji = getattr(event.emoji, "name", event.emoji)

        if emoji in ["stamp", "goldstamp"]:
            print("GUILD = ", self.utils.GUILD)
            guild = discord.utils.find(lambda g: g.name == self.utils.GUILD, client.guilds)
            channel = discord.utils.find(lambda c: c.id == event.channel_id, guild.channels)
            message = await channel.fetch_message(event.message_id)
            if self.is_at_me(message) and self.is_post_request(self.is_at_me(message)):

                if self.has_been_replied_to(message):
                    return

                stamp_score, approvers = await self.evaluate_message_stamps(message)
                if stamp_score > 30:
                    report = await self.post_message(message, approvers)

                    # mark it with an envelope to show it was sent
                    await message.add_reaction("📨")

                    await channel.send(report)
                else:
                    report = "This reply has %s stamp points. I will send it when it has 30" % stamp_score
                    await channel.send(report)