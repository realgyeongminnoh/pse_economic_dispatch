from src.persource import PerSource


class Renewable:
    def __init__(self, data):
        self.solar = PerSource()
        self.wind = PerSource()
        self.hydro = PerSource()

        data.load_renewable(self)