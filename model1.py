import os
import pickle
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


def parallel(idx_hour):
    solver = Solver(thermal, renewable, demand, commitment, results)
    solver.solve(idx_hour)


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
    
    timer_start = timer()
    # gurobi license validation spam * os.cpu_count(); can be prevented by just solver.solve(0) initially but will slow down to 4 sec somehow    
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        list(executor.map(parallel, range(8760)))

    timer_end = timer()
    print(f"Time taken for solving optimization: {(timer_end - timer_start):.3f}s\nSaving results at: {Path(__file__).resolve().parents[1] / "data" / "outputs" / Path(__file__).stem}" )

    process_save_results(results)

if __name__=="__main__":
    main()