class Demand:
    def __init__(self, data):
        self.total = None

        data.load_demand(self)