import gc
import numpy as np
from multiprocessing import Manager

from src.conventional import Conventional
from src.renewable import Renewable


class Result:
    def __init__(self, con: Conventional, ren: Renewable):
        self.cc, self.lc, self.nc = con.coal.count, con.lng.count, con.nuclear.count
        self.sc, self.wc, self.hc = ren.solar.count, ren.wind.count, ren.hydro.count

        # parallel
        manager = Manager()
        self.smp = manager.list(np.empty((8760)))
        self.cost_energy = manager.list(np.empty((8760)))
        self.cost_reserve = manager.list(np.empty((8760)))
        self.p = manager.list(np.empty((8760)))

        # # sequential
        # self.tc = self.cc + self.lc + self.nc + self.sc+ self.wc + self.hc # total generator count
        # self.smp = np.empty((8760))
        # self.cost_energy = np.empty((8760))
        # self.cost_reserve = np.empty((8760))
        # self.p = np.empty((8760, self.tc)) 


    def process_outputs(self):
        # parallel
        self.smp = np.array(self.smp)
        self.cost_energy = np.array(self.cost_energy)
        self.cost_reserve = np.array(self.cost_reserve)
        self.p_coal, self.p_lng, self.p_nuclear, self.p_solar, self.p_wind, self.p_hydro = np.split(
            np.vstack(self.p), np.cumsum([self.cc, self.lc, self.nc, self.sc, self.wc, self.hc][:-1]), axis=1
        )
        del self.p
        gc.collect()

        # # sequential
        # self.smp = np.array(self.smp)
        # self.cost_energy = np.array(self.cost_energy)
        # self.cost_reserve = np.array(self.cost_reserve)
        # self.p_thermal, self.p_solar, self.p_wind, self.p_hydro = np.split(
        #     self.p, np.cumsum([self.cc, self.lc, self.nc, self.sc, self.wc, self.hc][:-1]), axis=1
        # )
        # del self.p
        # gc.collect()