class Renewable:
    def __init__(self):
        # 197 buses
        self.solar_capacity = None
        self.wind_capacity = None
        self.hydro_capacity = None
        # 197 buses, 8760 hours
        self.solar_generation = None
        self.wind_generation = None
        self.hydro_generation = None
        # 8760 hours
        self.total_solar_generation = None
        self.total_wind_generation = None
        self.total_hydro_generation = None
        self.total_generation = None
