import numpy as np
from scipy.io import loadmat

from src.basics import Basics


class Generators:
    def __init__(self, basics : Basics):
        self.basics = basics
        self.gen_count = None
        self.gen_pmax = None
        self.gen_pmin = None
        self.gencost_c2 = None
        self.gencost_c1 = None
        self.gencost_c0 = None
        self.gentypes_description: dict = {0: "Coal", 1: "LNG", 2: "Nuclear"} # fixed
        self.gentypes = None # 
        self.gentypes_colors = None # 
        self.idx_gen_coal = None
        self.idx_gen_lng = None
        self.idx_gen_nuclear = None
        self.Get_gen_data()

    def Get_gen_data(self):
        basics = self.basics
        data_raw_gen = loadmat(f"{basics.getcwd.split("src")[0]}data/inputs/KPG193_ver1_2.mat") # KPG dataset
        self.gen_count = 122

        # generator data - ordered by generatior id
        # unit: MW
        # ignoring status; following list is the number of hours in the year for the 15 killed generators to be committed again in the year
        # [47, 4, 10, 45, 576, 744, 4440, 7416, 3336, 14, 92, 32, 3, 315, 45]
        # it was included in the UC at least; enough reason to ignore status
        gen_data = data_raw_gen["mpc"][0, 0]["gen"][:, [8, 9]]
        self.gen_pmax= gen_data[:, 0]
        self.gen_pmin = gen_data[:, 1]

        # generator cost function - ordered by generatior id
        # unit: 1,000 KRW and MWh
        gencost_data = data_raw_gen["mpc"][0, 0]["gencost"][:, 4:]
        self.gencost_c2 = gencost_data[:, 0]
        self.gencost_c1 = gencost_data[:, 1]
        self.gencost_c0 = gencost_data[:, 2]

        # generator unit types - ordered by generatior id # copied from KPG data set
        self.gentypes = np.array([0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 1, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        self.gentypes_colors = np.array([[1, 0, 0], [0, 0, 1], [0, 1, 0]])[self.gentypes] # red; blue; green
        self.idx_gen_coal = np.where(self.gentypes == 0)[0]
        self.idx_gen_lng = np.where(self.gentypes == 1)[0]
        self.idx_gen_nuclear = np.where(self.gentypes == 2)[0]