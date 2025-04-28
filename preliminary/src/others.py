import csv
import numpy as np

from src.basics import Basics


class Others:
    def __init__(self, basics : Basics):
        self.basics = basics
        self.total_demands = None
        self.renewable_capacity_by_bus = None # not needed for the rest
        self.renewable_capacity_by_source = None
        self.renewable_generation = None
        self.commitments_matrix = None

        self.Get_demands()
        self.Get_renewable_capacity() 
        self.Get_renewable_generation()
        del self.renewable_capacity_by_bus
        self.thermalgen_demands = self.total_demands - self.renewable_generation # demands to be fulfilled by thermal generators
        self.Get_commitments_matrix()

    def Get_demands(self):
        data_demands = []
        for path_file in self.basics.Get_path_files("demand", "daily_demand"):
            with open(path_file) as csvfile:
                data = np.array([row for row in csv.reader(csvfile)])[1:, :-1].astype(float) # len(data) == 197 * 24 == 4728 for all csv files
                data_demands.append([data[data[:, 0] == hour][:, -1].sum() for hour in range(1, 25)])
        # this is the same as https://www.data.go.kr/data/15065266/fileData.do#/layer_data_infomation
        self.total_demands =  np.array(data_demands).reshape(-1) # demands; len(demands) == 365 * 24 == 8760

    def Get_renewable_capacity(self):
        zeroArrays = np.zeros(197)
        with open(self.basics.getcwd.split("src")[0] + "data/inputs/renewables_capacity/solar_generators_2022.csv") as f:
            data_raw_solar = np.array([row for row in csv.reader(f)])[1:, [0, 2]].astype(float)
        data_solar = zeroArrays.copy()
        data_solar[data_raw_solar[:, 0].astype(int) - 1] = data_raw_solar[:, 1] # missing 4 bus id covered with 0 (bus number unified as 197 as indicated in the demand)

        with open(self.basics.getcwd.split("src")[0] + f"data/inputs/renewables_capacity/wind_generators_2022.csv") as csvfile:
            data_raw_wind = np.array([row for row in csv.reader(csvfile)])[1:, [0, 2]].astype(float) # bus id ordered pmax, pmin is all 0; ignore
        data_wind = zeroArrays.copy()
        data_wind[data_raw_wind[:, 0].astype(int) - 1] = data_raw_wind[:, 1] # missing 4 bus id covered with 0 (bus number unified as 197 as indicated in the demand)

        with open(self.basics.getcwd.split("src")[0] + f"data/inputs/renewables_capacity/hydro_generators_2022.csv") as csvfile:
            data_hydro = np.array([row for row in csv.reader(csvfile)])[1:, 2].astype(float)

        self.renewable_capacity_by_bus = np.column_stack([data_solar, data_wind, data_hydro]) # used for calculation of renewable generation
        self.renewable_capacity_by_source = self.renewable_capacity_by_bus.sum(axis=0) # idk for analysis

    def Get_renewable_generation(self):
        renewable_capacity_24_repeat = np.repeat(self.renewable_capacity_by_bus, 24, axis=0)
        self.renewable_generation = np.zeros(24 * 365)
        renewable_generation = self.renewable_generation
        idx_hour = 0

        for path_file in self.basics.Get_path_files("renewables", "renewables"): # hour, busid, solar, wind, hydro
            # DAILY PROFILE RATIO
            with open(path_file) as csvfile:
                reader = csv.reader(csvfile)
                next(reader)
                data_raw_reg_ratio = np.array([[float(cell.strip()) if cell.strip() else 0.0 for cell in row] for row in reader]) # some bad rows (pv ratio has nothing) - covererd
                # H1, BUS1 / H2, BUS1 / H3, BUS3/ ...
                # shitty code alert ; it works correctly i checked
                reg_per_hour_bus = (data_raw_reg_ratio[:, 2:] * renewable_capacity_24_repeat).sum(axis=1)
                hours = data_raw_reg_ratio[:, 0]
                for hour_incremental in range(1, 25):
                    for hour, reg in zip(hours, reg_per_hour_bus):
                        if hour == hour_incremental:
                            renewable_generation[idx_hour] += reg
                    idx_hour += 1
        # no for renewable generation by source (hourly) and analysis 

    def Get_commitments_matrix(self):
        matrix_for_zeroindexing = np.stack((np.ones(2928), np.ones(2928), np.zeros(2928)), axis=1).astype(int) # for data from the whole csv file
        self.commitments_matrix = np.zeros((365 * 24, 122), dtype=bool)
        commitments_matrix = self.commitments_matrix

        for day, path_file in enumerate(self.basics.Get_path_files("commitment_decision", "commitment_decision")):
            # DAILY
            with open(path_file) as csvfile:
                reader = csv.reader(csvfile)
                data = np.array([row for row in reader][1:], dtype=int) # all correct len
                data -= matrix_for_zeroindexing # idk if this is still needed zeroindexing of busid

            for hour in range(0, 24): # 0-index hour
                commitments_matrix[(day * 24 + hour)] = data[(122 * hour):(122 * (hour + 1))][:, -1].reshape(-1).astype(bool) # checked by another primitive method

# # KPG nuclear_mustoff vs commitment decision consistency test
# # all false - the commitment decision dataset truly reflect the nuclear must off
# # i did the complement set (whether nuclear always runs on NOT mustoff hour) but there were some small offs (obv excluding the multiple mustoff for single one)

# nuclear_mustoff = np.array([
#     [46, 47, 47, 48, 50, 52, 59, 61, 62, 63, 64, 65, 66, 68, 69, 96, 96, 97, 97, 100, 100, 104],
#     [1, 37, 49, 305, 362, 75, 269, 1, 81, 17, 240, 169, 332, 236, 1, 254, 307, 251, 257, 48, 160, 220], # off start day
#     [1, 1, 1, 1, 1, 10, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], # off start time
#     [341, 88, 115, 392, 407, 137, 375, 334, 260, 165, 717, 224, 385, 294, 226, 256, 362, 307, 312, 159, 182, 298], # off end day
#     [24, 24, 24, 21, 24, 24, 24, 24, 24, 24, 11, 24, 24, 24, 24, 15, 24, 24, 24, 24, 24, 24], # off end time
# ]).T - 1 # ALL 0-INDEXED

# for row in nuclear_mustoff:
#     idx_nuke = row[0]
#     idx_hour_off_start = row[1] * 24 + row[2]
#     idx_hour_off_end = row[3] * 24 + row[4]
#     print(np.any(commitments_matrix[idx_hour_off_start:(idx_hour_off_end + 1), idx_nuke]))