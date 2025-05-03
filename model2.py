import os
import pickle
from copy import deepcopy
from pathlib import Path
import numpy as np
from time import perf_counter as timer
from concurrent.futures import ProcessPoolExecutor # i still don't know why AMD w/ a higher core count is slower than INTEL when PPE is used

from src import *


def process_save_results(results: Results):
    results.process_outputs()

    path_data = Path(__file__).resolve().parents[0] / "data" / "outputs" / Path(__file__).stem
    path_data.mkdir(parents=True, exist_ok=True)

    with open(path_data / "object_results.pkl", "wb") as file:
        pickle.dump(results, file)
    np.save(path_data / "smp.npy", np.array(results.smp))
    np.savetxt(path_data / "smp.csv", np.array(results.smp), delimiter=",")
    np.save(path_data / "cost_system.npy", np.array(results.cost_system))
    np.save(path_data / "p_thermal.npy", np.array(results.p_thermal))
    np.save(path_data / "p_solar.npy", np.array(results.p_solar))
    np.save(path_data / "p_wind.npy", np.array(results.p_wind))
    np.save(path_data / "p_hydro.npy", np.array(results.p_hydro))


def get_alphas():
    # 2022 hourly (mainland) SMP from EPSIS
    smp_real = np.load(Path(__file__).resolve().parents[0] / "data" / "inputs" / "EPSIS" / "smp_2022.npy") # 8760

    # 2022 hourly model 1 results SMP
    with open(Path(__file__).resolve().parents[0] / "data" / "outputs" / "model1" / "object_results.pkl", "rb") as file:
        smp_model1 = pickle.load(file).smp

    # helpers
    def get_monthly_means_daily_max(smp_daily_max): # for 365 input
        days_in_months = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
        smp_daily_max_split = np.split(smp_daily_max, np.cumsum(days_in_months)[:-1])
        return np.array([month.mean() for month in smp_daily_max_split])

    # process data
    smp_real_daily_max = smp_real.reshape((-1, 24)).max(axis=1) # 365 len smp_real daily max values # min is around 130
    smp_model1_daily_max = smp_model1.reshape((-1, 24)).max(axis=1) # 365 len smp_model1 daily max values # min is around 57 so we are good

    smp_real_monthly_mean_daily_max = get_monthly_means_daily_max(smp_real_daily_max) # 12 len smp_real monthly mean of daily max values
    smp_model1_monthly_mean_daily_max = get_monthly_means_daily_max(smp_model1_daily_max) # 12 len smp_model1 monthly mean of daily max values

    # we now obtain the scaling factor for LNG C1 (linear coefficient)
    # model 2 will recompute the optimization after this tuning
    # i almost did bi-layer optimization with the outer one just naive... just for this project it's no point
    # scaling factor # I know that setting jan SMP close then scaling with lng_real ratio (jan = 1) would be more justifiable 
    # but LNG monthly price and SMP KPX mothly (monthly scales) are almost the same so both are justifiable # check analysis1.ipynb
    alphas = smp_real_monthly_mean_daily_max / smp_model1_monthly_mean_daily_max 
    return alphas # checked and correct

def parallel(idx_hour):
    # the easiest change (code-wise) for model2 without changing/creating anything much # not algorithmically the best design
    # solver.py Solver.solve
    # def solve(self, idx_hour, alpha:float = 0, model2: bool = False):
    #     thermal_c1 = self.thermal.c1.copy() # used in objective function later
    #     if model2:
    #         thermal_c1[self.thermal.idx_lng] *= alpha
            # thermal_c1[self.thermal.idx_coal] *= alpha

    # alpha for given month
    alpha = alphas[np.searchsorted(idxs_hour_month_start, idx_hour, side='right') - 1]
    
    solver = Solver(thermal, renewable, demand, commitment, results)
    solver.solve(idx_hour, alpha=alpha, model2=True)


def main():
    global thermal, renewable, demand, commitment, results
    data = Data()
    thermal = Thermal()
    renewable = Renewable()
    demand = Demand()
    commitment = Commitment()
    data.load_thermal(thermal)
    data.load_renewable_capacity(renewable)
    data.load_renewable_generation(renewable)
    data.load_demand(demand)
    data.load_commitment_decision(commitment)
    results = Results(thermal, renewable, commitment)   
    
    # LNG C1's monthly scaling factor # we don't do the same for C2 because MC(p) = C2*p + C1 # extremely sensitive for already high SMP days in model 1
    global alphas, idxs_hour_month_start
    alphas = get_alphas()
    idxs_hour_month_start = np.array([0, 744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016]) # non leap-year specific
    



    timer_start = timer()
    # gurobi license validation spam * os.cpu_count(); can be prevented by just solver.solve(0) initially but will slow down to 4 sec somehow    
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        list(executor.map(parallel, range(8760)))

    timer_end = timer()
    print(f"Time taken for solving optimization: {(timer_end - timer_start):.3f}s\nSaving results at: {Path(__file__).resolve().parents[1] / "data" / "outputs" / Path(__file__).stem}" )

    process_save_results(results)

if __name__=="__main__":
    main()