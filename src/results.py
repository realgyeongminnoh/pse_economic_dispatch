import gc
import numpy as np
from multiprocessing import Manager


class Results:
    def __init__(self, thermal, renewable, commitment):
        self.tc, self.sc, self.wc, self.hc = thermal.count, renewable.solar_count, renewable.wind_count, renewable.hydro_count
        self.cost_no_load = (commitment.decision * thermal.c0).sum(axis=1) # 8760 no load costs (122 summed; respecting UC decision)

        # parallel
        manager = Manager()
        self.smp = manager.list(np.empty((8760)))
        self.cost_system = manager.list(np.empty((8760)))
        self.p = manager.list(np.empty((8760)))

        # # sequential
        # self.smp = np.empty((8760))
        # self.cost_system = np.empty((8760))
        # # power for each 8760 hours, 427 generator/bus # less than 30 MB
        # self.p = np.empty((8760, self.tc + self.sc + self.wc + self.hc)) 


    def process_outputs(self):
        # parallel
        self.smp = np.array(self.smp)
        self.cost_system = np.array(self.cost_system) + self.cost_no_load
        self.p_thermal, self.p_solar, self.p_wind, self.p_hydro = np.split(
            np.vstack(self.p), [self.tc, self.tc + self.sc, self.tc + self.sc + self.wc], axis=1
        )
        del self.p
        gc.collect()

        # # sequential 
        # self.cost_system += self.cost_no_load
        # self.p_thermal, self.p_solar, self.p_wind, self.p_hydro = np.split(
        #     self.p, [self.tc, self.tc + self.sc, self.tc + self.sc + self.wc], axis=1
        # )
        # del self.p
        # gc.collect()