import gc
import numpy as np
from multiprocessing import Manager


class Results:
    def __init__(self, thermal, renewable, commitment):
        self.tc, self.rc = thermal.count, renewable.count
        self.cost_no_load = (commitment.decision * thermal.c0).sum(axis=1)

        # parallel
        manager = Manager()
        self.smp = manager.list(np.empty((8760)))
        self.cost_system = manager.list(np.empty((8760)))
        self.p = manager.list(np.empty((8760)))

        # # sequential
        # self.smp = np.empty((8760))
        # # total system cost, initialized as 8760 no load costs (122 summed) # [idx_hour] += model.ObjVal
        # self.cost_system = np.empty((8760))
        # # power for each 8760 hours, 713 generator/bus # less than 50 MB
        # self.p = np.empty((8760, self.tc + self.rc * 3)) 




    def process_outputs(self):
        # parallel
        self.smp = np.array(self.smp)
        self.cost_system = np.array(self.cost_system) + self.cost_no_load
        self.p_thermal, self.p_solar, self.p_wind, self.p_hydro = np.split(
            np.vstack(self.p), [self.tc, self.tc + self.rc, self.tc + 2 * self.rc], axis=1
        )
        del self.p
        gc.collect()

        # # sequential 
        # self.cost_system += self.cost_no_load
        # self.p_thermal, self.p_solar, self.p_wind, self.p_hydro = np.split(
        #     self.p, [self.tc, self.tc + self.rc, self.tc + 2 * self.rc], axis=1
        # )
        # del self.p
        # gc.collect()