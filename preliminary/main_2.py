import os
import numpy as np

from time import perf_counter as timer
from src import *


def Get_modified_commitments_matrix(
    generators: Generators, others: Others, committed_generators: Committed_generators,
    idx_nan_model1):
    
    modified_commitments_matrix = others.commitments_matrix.copy() # to be updated
    marginal_unit_idx_and_hour = {} # marginal unit; cus demand not necessarily exactly equals the modified pmin sum this unit is responsible for producing the deficit (which is below its original pmin)

    for idx_hour in idx_nan_model1:
        committed_generators.Get_committed_generators(idx_hour) # unmodified committed generators class 
        demand = others.thermalgen_demands[idx_hour] # for comparison
        modified_commitments = committed_generators.commitments.copy()

        while True:
            current_commitments = modified_commitments
            current_idx_committed = np.where(current_commitments == 1)[0]   

            # updating necesssary vars
            committed_gen_pmin = generators.gen_pmin[current_idx_committed] 
            committed_gencost_c2 = generators.gencost_c2[current_idx_committed]
            committed_gencost_c1 = generators.gencost_c1[current_idx_committed]
            
            total_pmin = committed_gen_pmin.sum()
            if total_pmin <= demand: # discretely turning off one by one give me feasible -> break
                break

            mc_gen_pmin = 2 * committed_gencost_c2 * committed_gen_pmin + committed_gencost_c1
            idx_highest_mc = np.argmax(mc_gen_pmin)
            idx_gen_turn_off = current_idx_committed[idx_highest_mc]
            modified_commitments[idx_gen_turn_off] = 0

        # for overshoot correction
        surplus = demand - total_pmin
        if surplus > 0:
            modified_commitments[idx_gen_turn_off] = 1
            marginal_unit_idx_and_hour[idx_hour] = idx_gen_turn_off

        modified_commitments_matrix[idx_hour] = modified_commitments

    return modified_commitments_matrix, marginal_unit_idx_and_hour


def Main():
    # instantiation
    t0 = timer()
    basics = Basics()
    generators = Generators(basics)
    others = Others(basics)
    committed_generators = Committed_generators(generators, others)
    solver = Solver(generators, others, committed_generators)

    # modify commitments_matrix    
    idx_nan_model1 = np.where(np.load(f"{os.path.abspath(__file__).split("main_2.py")[0]}/data/outputs/main_1/result_status.npy") == -1)[0] 
    others.commitments_matrix, marginal_unit_idx_and_hour = Get_modified_commitments_matrix(generators, others, committed_generators, idx_nan_model1)
    np.save(f"{os.path.abspath(__file__).split("main_2.py")[0]}/data/inputs/modified_commitments_matrix.npy", others.commitments_matrix)

    # re-instantiation
    committed_generators = Committed_generators(generators, others)
    solver = Solver(generators, others, committed_generators)

    # computing SMP for every hour in 2022 based on KPG dataset 
    # i know i don't have to for model 2 and just simply power.value[last to be turned off and on again] = demand-gen deficit
    # but i wanna compare it and just using existing code ...
    t1 = timer()
    result_status, result_smp, result_p_error_demand, result_cost_system, result_powers_by_source, result_cost_by_source = [], [], [], [], [], []

    for idx_hour in range(0, 8760): # no point to not do it on the whole dataset
        committed_generators.Get_committed_generators(idx_hour)

        ################# MODEL 2 opt change: pmin loosening of the marginal unit for the modified infeasible problem
        # demand not necessarily exactly equals the modified pmin sum this unit is responsible for producing the deficit (which is below its original pmin)
        if idx_hour in marginal_unit_idx_and_hour:
            committed_generators.Get_committed_generators(idx_hour)
            idx_marginal_unit_gen = marginal_unit_idx_and_hour[idx_hour]
            committed_generators.committed_gen_pmin[
                np.where(committed_generators.commitments == 1)[0].tolist().index(idx_marginal_unit_gen)
                ] = 0

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
    MAIN 2 - PRELIMINARY RESULT SUMMARY
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

    folder_path = f"{os.path.abspath(__file__).split("main_2.py")[0]}data/outputs/main_2/"
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