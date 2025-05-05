from src.persource import PerSource


class Conventional:
    def __init__(self, data):
        self.coal = PerSource()
        self.lng = PerSource()
        self.nuclear = PerSource()

        data.load_conventional(self)