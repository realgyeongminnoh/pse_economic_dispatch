class PerSource:
    def __init__(self):
        self.count: int = None
        self._idx_helper = None

        self.capmin = None # 1-D # len = count # 0 for renewable
        self.capmax = None # 1-D # len = count

        self.pmin = None # 2-D # shape = (time, count) # 0 for renewable
        self.pmax = None # 2-D # shape = (time, count)

        self.c2 = None # 1-D # KPG COST # MONTHLY IS DONE IN MAIN # 0 for renewable
        self.c1 = None # 1-D # KPG COST # MONTHLY IS DONE IN MAIN # 0 for renewable
        self.c0 = None # 1-D # KPG COST # MONTHLY IS DONE IN MAIN # 0 for renewable