import csv
import pickle
from pathlib import Path

import numpy as np
from scipy.io import loadmat
# for type check
from src.persource import PerSource
from src.conventional import Conventional
from src.renewable import Renewable


class Data:
    def __init__(self, gamma):
        self.gamma = gamma
        self.path_data = Path(__file__).resolve().parents[1] / "data"
        self.path_kpg = self.path_data / "inputs" / "KPG193_ver1_2"
        

        self.idx_hour_month_start = np.array([0, 744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016]) # non leap-year specific
        self.idx_hour_month_end = np.concatenate((np.delete(self.idx_hour_month_start, 0), np.array([8760]))) - 1 # 24th hour


    def get_path_files(self, folder, file) -> list:
        base = self.path_kpg / "profile" / folder
        return [base / f"{file}_{i}.csv" for i in range(1, 366)]


    def get_smp_real(self):
        smp_real = np.load(self.path_data / "inputs" / "EPSIS" / "smp_2022.npy")
        return smp_real


    def get_smp_model_1(self):
        smp_model_1 = np.load(self.path_data / "outputs" / f"{self.gamma}" / "model_1" / "smp.npy")
        return smp_model_1


    def get_alphas_per_source(self):

        smp_real = self.get_smp_real()
        smp_model_1 = self.get_smp_model_1()
        idx_hour_jan_start, idx_hour_jan_end = self.idx_hour_month_start[0], self.idx_hour_month_end[0]

        smp_real_jan_mean = smp_real[idx_hour_jan_start:idx_hour_jan_end+1].reshape((24, -1)).mean()
        smp_model_1_jan_mean = smp_model_1[idx_hour_jan_start:idx_hour_jan_end+1].reshape((24, -1)).mean()
        smp_ratio_jan = smp_real_jan_mean / smp_model_1_jan_mean

        with open(self.path_data / "inputs" / "EPSIS" / "fuel_cost_2022.csv", encoding="cp949") as csvfile:
            raw = np.array([row for row in csv.reader(csvfile)])[3:, 1:][::-1].astype(float)
        alphas_coal = raw[:, 6] / raw[0, 6] * smp_ratio_jan # 6 # 11
        alphas_lng = raw[:, 9] / raw[0, 9] * smp_ratio_jan # 9 # 14
        alphas_nuclear = raw[:, 5] / raw[0, 5] * smp_ratio_jan # 5 # 10
        return alphas_coal, alphas_lng, alphas_nuclear


    def _load_commitment_for_conventional(self, con: Conventional) -> np.ndarray:
        conv_count_total = con.coal.count + con.lng.count + con.nuclear.count
        decision = np.empty((8760, conv_count_total), dtype=bool)

        for idx_hour, file in zip(np.arange(0, 8760, 24), self.get_path_files("commitment_decision", "commitment_decision")):
            with open(file) as csvfile:
                reader = csv.reader(csvfile)
                next(reader)
                raw_commit = np.array([[int(cell) for cell in row] for row in reader])
                raw_commit[:, [0, 1]] -= 1 # 0-based indexing for hour and generatorid

                idx_hour += raw_commit[:, 0]
                idx_generator = raw_commit[:, 1]
                decision[idx_hour, idx_generator] = raw_commit[:, 2]
        
        return decision # unit commitment decision for conventional units from dataset # 8670 hours, 122 generators
    

    def load_conventional(self, con: Conventional):
        idx_helper_total = np.array([
            0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1,
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 1, 1, 
            1, 1, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 
            0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 1, 1, 1, 2, 2, 1, 1, 1, 
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], dtype=np.uint8)
        con.coal._idx_helper = np.where(idx_helper_total == 0)[0] 
        con.lng._idx_helper = np.where(idx_helper_total == 1)[0] 
        con.nuclear._idx_helper = np.where(idx_helper_total == 2)[0]
        
        con.coal.count = len(con.coal._idx_helper)
        con.lng.count = len(con.lng._idx_helper)
        con.nuclear.count = len(con.nuclear._idx_helper)

        raw = loadmat(self.path_kpg / "network" / "mat" / "KPG193_ver1_2.mat")["mpc"][0, 0]
        capmin_total = raw["gen"][:, 9]
        capmax_total = raw["gen"][:, 8]
        c2_total = raw["gencost"][:, 4]
        c1_total = raw["gencost"][:, 5]
        c0_total = raw["gencost"][:, 6]
        decision_total = self._load_commitment_for_conventional(con)
        
        for source in ["coal", "lng", "nuclear"]:
            source_obj = getattr(con, source)
            idx = source_obj._idx_helper
            source_obj.capmin = capmin_total[idx]
            source_obj.capmax = capmax_total[idx]
            source_obj.c2 = c2_total[idx]
            source_obj.c1 = c1_total[idx]
            source_obj.c0 = c0_total[idx]
            decision_source = decision_total[:, idx] # im just gonna say p min max already respect the binary decision
            source_obj.pmin = decision_source * source_obj.capmin # this so unncessarily increases memory but it just looks better 
            source_obj.pmax = decision_source * source_obj.capmax # and same structure with renewable 

    
    def _load_some_renewable_per_source_for_renewable(self, source_obj: PerSource, source: str) -> None:
        with open(self.path_kpg / "renewables_capacity" / f"{source}_generators_2022.csv") as csvfile:
            raw = np.array([row for row in csv.reader(csvfile)])[1:, [0, 2]].astype(float)
        idx_from_raw = np.where(raw[:, 1] > 0)[0]

        source_obj._idx_helper = (raw[idx_from_raw][:, 0] - 1).astype(int) 
        source_obj.count = len(source_obj._idx_helper)
        source_obj.capmax = raw[idx_from_raw][:, 1]
        # type is not np.ndarray
        source_obj.capmin = 0
        source_obj.pmin = 0
        source_obj.c2 = 0
        source_obj.c1 = 0
        source_obj.c0 = 0
        

    def load_renewable(self, ren: Renewable):
        # all this just for pmax (renewable """generation""")
        renewable_max_count = 197 # because these data has max bux id = 197
        solar_ratio, wind_ratio, hydro_ratio = np.empty((8760, renewable_max_count)), np.empty((8760, renewable_max_count)), np.empty((8760, renewable_max_count))

        for idx_hour, file in zip(np.arange(0, 8760, 24), self.get_path_files("renewables", "renewables")):
            with open(file) as csvfile:
                reader = csv.reader(csvfile)
                next(reader)
                raw = np.array([[float(cell) if cell else 0 for cell in row] for row in reader]) # csv empty cell correction
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
                
                idx_hour += raw[:, 0].astype(int) # true idx_hour
                idx_bus = raw[:, 1].astype(int)
                solar_ratio[idx_hour, idx_bus] = raw[:, 2]
                wind_ratio[idx_hour, idx_bus] = raw[:, 3]
                hydro_ratio[idx_hour, idx_bus] = raw[:, 4]

        for source, ratio in zip(["solar", "wind", "hydro"], [solar_ratio, wind_ratio, hydro_ratio]):
            source_obj = getattr(ren, source)
            self._load_some_renewable_per_source_for_renewable(source_obj, source)
            idx = source_obj._idx_helper

            source_obj.pmax = ratio[:, idx] * source_obj.capmax


    def load_demand(self, demand):
        demand_total = []
        for file in self.get_path_files("demand", "daily_demand"):
            with open(file) as csvfile:
                raw_demand = np.array([row for row in csv.reader(csvfile)])[1:, :-1].astype(float)
                demand_total.append([raw_demand[raw_demand[:, 0] == hour][:, -1].sum() for hour in range(1, 25)])
        
        demand.total = np.array(demand_total).reshape(-1) # 8760 hours