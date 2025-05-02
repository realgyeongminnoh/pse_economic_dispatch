class Renewable:
    def __init__(self):
        self.max_count: int = 197           # fixed; for collection of /profile/renewable/ which has 24 hours x 197 buses

        self.solar_count: int = None        # 193 buses w/ +ve capacity
        self.wind_count: int = None         # 95 buses w/ +ve capacity
        self.hydro_count: int = None        # 17 buses w/ +ve capacity

        self.solar_idx_bus = None           # for load_renewable_generation, shirinking from 197 to 193
        self.wind_idx_bus = None            # for load_renewable_generation, shirinking from 197 to 95
        self.hydro_idx_bus = None           # for load_renewable_generation, shirinking from 197 to 17

        self.solar_capacity = None          # 193 buses w/ +ve capacity
        self.wind_capacity = None           # 95 buses w/ +ve capacity
        self.hydro_capacity = None          # 17 buses w/ +ve capacity

        self.solar_generation = None        # 8760 hours x 193 buses
        self.wind_generation = None         # 8760 hours x 95 buses
        self.hydro_generation = None        # 8760 hours x 17 buses

        self.total_solar_generation = None  # 8760 hours
        self.total_wind_generation = None   # 8760 hours
        self.total_hydro_generation = None  # 8760 hours
        
        self.total_generation = None        # 8760 hours