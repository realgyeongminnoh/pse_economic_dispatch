import gc
import numpy as np
from multiprocessing import Manager

from src.conventional import Conventional
from src.renewable import Renewable


class Result:
    def __init__(self, con: Conventional, ren: Renewable):
        self.cc, self.lc, self.nc = con.coal.count, con.lng.count, con.nuclear.count
        self.sc, self.wc, self.hc = ren.solar.count, ren.wind.count, ren.hydro.count
        self.rc = self.lc # (lng) reserve count
        self.tc = self.cc + self.lc + self.nc + self.sc+ self.wc + self.hc + self.rc # total variable count for pr

        # parallel
        manager = Manager()
        self.smp = manager.list([np.nan]*8760)
        self.cost_energy = manager.list([np.nan]*8760)
        self.cost_reserve = manager.list([np.nan]*8760)
        self.gammas_eff = manager.list([np.nan]*8760)
        self.pr = manager.list([np.full(self.tc, np.nan) for _ in range(8760)])        
        
        # # sequential
        # self.smp = np.empty((8760))
        # self.cost_energy = np.empty((8760))
        # self.cost_reserve = np.empty((8760))
        # self.gammas_eff = np.empty((8760))
        # self.pr = np.empty((8760, self.tc)) 


    def process_outputs(self):
        def _has_nan(seq):
            return any(np.isnan(x).any() for x in seq)

        if (_has_nan(self.smp) or _has_nan(self.cost_energy) or
            _has_nan(self.cost_reserve) or _has_nan(self.gammas_eff) or
            _has_nan(self.pr)):
            print("[Result] WARNING: NaNs detected in solver outputs")


        # parallel
        self.smp = np.array(self.smp)
        self.cost_energy = np.array(self.cost_energy)
        self.cost_reserve = np.array(self.cost_reserve)
        self.gammas_eff = np.array(self.gammas_eff)
        self.p_coal, self.p_lng, self.p_nuclear, self.p_solar, self.p_wind, self.p_hydro, self.r_lng = np.split(
            np.vstack(self.pr), np.cumsum([self.cc, self.lc, self.nc, self.sc, self.wc, self.hc, self.rc][:-1]), axis=1
        )
        del self.pr
        gc.collect()

        # # sequential
        # self.smp = np.array(self.smp)
        # self.cost_energy = np.array(self.cost_energy)
        # self.cost_reserve = np.array(self.cost_reserve)
        # self.gammas_eff = np.array(self.gammas_eff)
        # self.p_coal, self.p_lng, self.p_nuclear, self.p_solar, self.p_wind, self.p_hydro, self.r_lng = np.split(
        #     self.pr, np.cumsum([self.cc, self.lc, self.nc, self.sc, self.wc, self.hc, self.rc][:-1]), axis=1
        # )
        # del self.pr
        # gc.collect()
