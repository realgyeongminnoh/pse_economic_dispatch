import os
import numpy as np

from time import perf_counter as timer
from src import *


def Main():
    # instantiation
    t0 = timer()
    basics = Basics()
    generators = Generators(basics)
    others = Others(basics)
    committed_generators = Committed_generators(generators, others)
    solver = Solver(generators, others, committed_generators)
    
    # computing SMP for every hour in 2022 based on KPG dataset
    t1 = timer()
    result_status, result_smp, result_p_error_demand, result_cost_system, result_powers_by_source, result_cost_by_source = [], [], [], [], [], []

    for idx_hour in range(0, 8760): # no point to not do it on the whole dataset
        committed_generators.Get_committed_generators(idx_hour)
        solver.Compute_smp(idx_hour=idx_hour, save_powers_by_bus=False)

        result_status.append(solver.status)
        result_smp.append(solver.smp)
        result_p_error_demand.append(solver.p_error_demand)
        result_cost_system.append(solver.cost_system)
        result_powers_by_source.append(solver.powers_by_source) 
        result_cost_by_source.append(solver.cost_by_source) 

    # result organization, summary print, result saving
    t2 = timer()
    result_status, result_smp, result_p_error_demand, result_cost_system, result_powers_by_source, result_cost_by_source = np.array(result_status), np.array(result_smp), np.array(result_p_error_demand), np.array(result_cost_system), np.array(result_powers_by_source), np.array(result_cost_by_source) # i do this because list appending is faster than nparray but i need nparray afterall
    result_cost_system *= 1000
    result_cost_by_source *= 1000
    idx_nonan = np.where(result_status == 0)[0]

    print(f"""
    PRELIMINARY RESULT SUMMARY
    --------------------------------------------------------------------------------------------
    TOTAL PROBLEMS: 8760
    FEASIBLE OPTIMIZATION PROBLEMS: {len(idx_nonan)}
    INFEASIBLEOPTIMIZATION PROBLEMS: {8760 - len(idx_nonan)} 
    TIME TAKEN FOR DATA ORGANIZATION (s): {t1 - t0}
    TIME TAKEN FOR SOLVING OPTIMIZATION (s): {t2 - t1}

    ACCURACY SUMMARY & SANITY CHECK FOR {len(idx_nonan)} FEASIBLE OPTIMIZATION PROBLEMS
    --------------------------------------------------------------------------------------------
    SUM OF PERCENTAGE ERROR OF EQUALITY CONSTRAINT (%): {result_p_error_demand[idx_nonan].sum()}
    SUM OF DIFFERENCE BETWEEN DEMAND AND TOTAL POWER (MWh): {(others.thermalgen_demands[idx_nonan] - result_powers_by_source[idx_nonan].sum(axis=1)).sum()}
    SUM OF DIFFERENCE BETWEEN SYSTEM COST AND SUM OF COST BY SOURCE (KRW): {(result_cost_system[idx_nonan] - result_cost_by_source[idx_nonan].sum(axis=1)).sum() * 1000}""")

    folder_path = os.path.abspath(__file__).split("main_1.py")[0] + "data/outputs/main_1/"
    os.makedirs(folder_path, exist_ok=True)
    np.save(folder_path + "result_status.npy", result_status)
    np.save(folder_path + "result_smp.npy", result_smp)
    np.save(folder_path + "result_p_error_demand.npy", result_p_error_demand)
    np.save(folder_path + "result_cost_system.npy", result_cost_system)
    np.save(folder_path + "result_powers_by_source.npy", result_powers_by_source)
    np.save(folder_path + "result_cost_by_source.npy", result_cost_by_source)
    np.save(folder_path + "idx_nonan.npy", idx_nonan)


if __name__ == "__main__":
    Main()