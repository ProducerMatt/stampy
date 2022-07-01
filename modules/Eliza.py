import re
import random
from modules.module import Module, Response
from utilities.utilities import randbool
from database.eliza_db import psychobabble, reflections


class Eliza(Module):
    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.psychobabble = psychobabble
        self.reflections = reflections

    def reflect(self, fragment):
        """
        Convert a string to parrot it back
        'I am your friend' -> 'You are my friend' etc.
        """
        tokens = fragment.lower().split()
        for i, token in enumerate(tokens):
            if token in self.reflections:
                tokens[i] = self.reflections[token]
        return " ".join(tokens)

    def analyze(self, statement):
        # self.log(self.class_name, msg="analyzing with ELIZA")
        for pattern, responses in self.psychobabble:
            match = re.match(pattern, statement.lower().rstrip(".!"))
            if match:
                response = random.choice(responses)
                return response.format(*[self.reflect(g) for g in match.groups()])
        return ""

    def process_message(self, message):
        if self.is_at_me(message):
            # ELIZA can respond to almost anything, so it only talks if nothing else has, hence 1 confidence
            text = self.is_at_me(message)
            if text.startswith("is ") and text[-1] != "?":  # stampy is x becomes "you are x"
                text = "you are " + text.partition(" ")[2]
            result = self.dereference(
                self.analyze(text).replace("<<", "{{").replace(">>", "}}"), message.author.name
            )
            if result:
                return Response(
                    confidence=1,
                    text=result,
                    why="%s said '%s', and ELIZA responded '%s'" % (message.author.name, text, result),
                )
        else:
            return Response()