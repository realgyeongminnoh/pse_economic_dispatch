import os
import csv
import numpy as np
from scipy.io import loadmat


class Data:
    def __init__(self):
        self.thermal_count: int = None
        self.dotcsv = ".csv"
        self.path = os.path.abspath(__file__).split("/src/data.py")[0] + "/data"
        self.path_kpg = self.path + "/inputs/KPG193_ver1_2"

    
    def get_path_files(self, folder, file):
        path = f"{self.path_kpg}/profile/{folder}/{file}_"
        return [(f"{path}{i}{self.dotcsv}") for i in range(1, 366)]

    
    def load_thermal(self, thermal):
        raw_thermal = loadmat(self.path_kpg + "/network/mat/KPG193_ver1_2.mat")["mpc"][0, 0]
        # 0 = coal = red; 1 = lng = blue; 2 = nuclear = green
        thermal.fueltype = np.array([0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 1, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], dtype=np.uint8)
        thermal.fuelcolor = np.array([[1, 0, 0], [0, 0, 1], [0, 1, 0]], dtype=np.uint8)[thermal.fueltype]
        thermal.idx_coal = np.where(thermal.fueltype == 0)[0]
        thermal.idx_lng = np.where(thermal.fueltype == 1)[0]
        thermal.idx_nuclear = np.where(thermal.fueltype == 2)[0]
        # 122 generators
        thermal.c2 = raw_thermal["gencost"][:, 4]
        thermal.c1 = raw_thermal["gencost"][:, 5]
        thermal.c0 = raw_thermal["gencost"][:, 6]
        thermal.pmin = raw_thermal["gen"][:, 9]
        thermal.pamx = raw_thermal["gen"][:, 8]
        thermal.count = len(thermal.pmin)
        self.thermal_count = thermal.count

    
    def load_renewable_capacity(self, renewable):
        # 197 buses
        # busid 119, 164, 185, 186 missing; solar capacity for these busid is assumed to be 0
        with open(self.path_kpg + "/renewables_capacity/solar_generators_2022.csv") as csvfile:
            raw_solar = np.array([row for row in csv.reader(csvfile)])[1:, [0, 2]].astype(float)
        renewable.solar_capacity = np.zeros(197)
        renewable.solar_capacity[raw_solar[:, 0].astype(int) -1] = raw_solar[:, 1]

        # same busid 119, 164, 185, 186 missing; the capacity for these busid is assumed to be 0
        with open(self.path_kpg + "/renewables_capacity/wind_generators_2022.csv") as csvfile:
            raw_wind = np.array([row for row in csv.reader(csvfile)])[1:, [0, 2]].astype(float)
        renewable.wind_capacity = np.zeros(197)
        renewable.wind_capacity[raw_wind[:, 0].astype(int) -1] = raw_wind[:, 1]

        # hydro capacity data is okay, full renewable 197 busid, all 0 pmin (4 empy pmin = 0)
        with open(self.path_kpg + "/renewables_capacity/hydro_generators_2022.csv") as csvfile:
            renewable.hydro_capacity = np.array([row for row in csv.reader(csvfile)])[1:, 2].astype(float)

    
    def load_renewable_generation(self, renewable):
        solar_ratio, wind_ratio, hydro_ratio = np.zeros((197, 8760)), np.zeros((197, 8760)), np.zeros((197, 8760))

        for idx_hour, file in zip(np.arange(0, 365 * 24, 24), self.get_path_files("renewables", "renewables")):
            with open(file) as csvfile:
                reader = csv.reader(csvfile)
                next(reader)
                raw = np.array([[float(cell) if cell else 0 for cell in row] for row in reader]) # empty cell correction
                raw[:, [0, 1]] -= 1 # 0-indexing hour and busid

                # please check KPG profile/renewables
                # busid 153 is duplicate hourly (1h 1h 2h 2h ... 24h 24h)
                # busid 151 is also missing... for all the 365 csv's
                # which was why the length (24 * 197) was correct for each too
                rawbusid153 = raw[(151 * 24):(153 * 24):2, :] # extracting hourly data from 2 * hourly duplicate in busid 153
                raw[(150 * 24):(151 * 24), 1] = 150 # busid 151's data slided down from busid 152's data (0-indexed in code!) 
                raw[(151 * 24):(152 * 24), :] = rawbusid153.copy() # busid 152's data is non duplicate busid 153's data 
                raw[(151 * 24):(152 * 24), 1] = 151 # busid 152's data's busid set to 152 (0-indexed in code!)
                raw[(152 * 24):(153 * 24), :] = rawbusid153.copy() # busid 152's data is non duplicate busid 153's data 
                # raw[:, [0, 1]] += 1 # if you need this new corrected version as csv you can uncomment and save these 365 arrays
                
                idx_hour += raw[:, 0].astype(int)
                idx_bus = raw[:, 1].astype(int)
                solar_ratio[idx_bus, idx_hour] = raw[:, 2]
                wind_ratio[idx_bus, idx_hour] = raw[:, 3]
                hydro_ratio[idx_bus, idx_hour] = raw[:, 4]

        # 8760 hours, 197 buses
        renewable.solar_generation = renewable.solar_capacity[:, None] * solar_ratio
        renewable.wind_generation = renewable.wind_capacity[:, None] * wind_ratio
        renewable.hydro_generation = renewable.hydro_capacity[:, None] * hydro_ratio
        # 8760 hours
        renewable.total_solar_generation = renewable.solar_generation.sum(axis=0)
        renewable.total_wind_generation = renewable.wind_generation.sum(axis=0)
        renewable.total_hydro_generation = renewable.hydro_generation.sum(axis=0)
        renewable.total_generation = renewable.total_solar_generation + renewable.total_wind_generation + renewable.total_hydro_generation

    
    def load_demand(self, demand):
        demand_total = []
        for file in self.get_path_files("demand", "daily_demand"):
            with open(file) as csvfile:
                raw_demand = np.array([row for row in csv.reader(csvfile)])[1:, :-1].astype(float)
                demand_total.append([raw_demand[raw_demand[:, 0] == hour][:, -1].sum() for hour in range(1, 25)])
        # 8760 hours
        demand.total = np.array(demand_total).reshape(-1)


    def load_commitment_decision(self, commitment):
        decision = np.zeros((8760, self.thermal_count), dtype=bool)

        for idx_hour, file in zip(np.arange(0, 365 * 24, 24), self.get_path_files("commitment_decision", "commitment_decision")):
            with open(file) as csvfile:
                reader = csv.reader(csvfile)
                next(reader)
                raw_commit = np.array([[int(cell) for cell in row] for row in reader])
                raw_commit[:, [0, 1]] -= 1 # 0-indexin hour and generatorid

                idx_hour += raw_commit[:, 0]
                idx_generator = raw_commit[:, 1]
                decision[idx_hour, idx_generator] = raw_commit[:, 2]

        # 8670 hours, 122 generators
        commitment.decision = decision