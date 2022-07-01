from utilities.serviceutils import ServiceUser, ServiceServer, ServiceChannel, ServiceMessage, Services
import threading
import time


# Depending on how secret we want this, we may want to move it to an environment variable with a JSON dict.
server_keys = {
    "$bF*-6KJ2-K6aR-KB%F": "cli",
}


class FlaskUtilities:
    __instance = None

    @staticmethod
    def get_instance():
        if FlaskUtilities.__instance is None:
            FlaskUtilities()
        return FlaskUtilities.__instance

    def __init__(self):
        if FlaskUtilities.__instance is not None:
            raise Exception("this class is a singleton!")
        else:
            FlaskUtilities.__instance = self

    def stampy_is_author(self, message: "FlaskMessage") -> bool:
        return False  # Flask doesn't process Stampy's messages so it's always False

    def is_stampy(self, user: "FlaskUser") -> bool:
        return False  # Flask doesn't process Stampy's messages so it's always False

    def is_stampy_mentioned(self, message: "FlaskMessage") -> bool:
        return True  # Flask only process messages meant for stampy so assume True


def kill_thread(event: threading.Event, thread: threading.Thread):
    event.wait()
    thread.stop()


class FlaskUser(ServiceUser):
    def __init__(self):
        id = str(time.time())
        super().__init__(id, id, id)


class FlaskServer(ServiceServer):
    def __init__(self, key: str):
        if key not in server_keys:
            raise LookupError("Server is not registered.")
        super().__init__(server_keys[key], key)


class FlaskChannel(ServiceChannel):
    def __init__(self, server: FlaskServer):
        super().__init__("Web Interface", 0, server)


class FlaskMessage(ServiceMessage):
    def __init__(self, msg):
        self._message = msg
        server = FlaskServer(msg["key"])
        id = str(time.time())
        service = Services.FLASK
        super().__init__(id, msg["content"], FlaskUser(), FlaskChannel(server), service)
        self.modules = msg["modules"]
