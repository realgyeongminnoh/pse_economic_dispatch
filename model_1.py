import os
from pathlib import Path
import numpy as np
import gurobipy as gp
from time import perf_counter as timer
from concurrent.futures import ProcessPoolExecutor
import argparse

from src import *


def ParseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gamma", "--g", type=float, required=True, help="flat gamma (reserve ratio) for all lng units")
    return parser.parse_args()


def process_save_result(result: Result, path_outputs):
    result.process_outputs()

    path_outputs.mkdir(parents=True, exist_ok=True)

    # smp save
    np.savetxt(path_outputs / "smp.csv", np.array(result.smp), delimiter=",")
    np.save(path_outputs / "smp.npy", np.array(result.smp))
    # total energy and reserve cost save
    np.save(path_outputs / "cost_energy.npy", np.array(result.cost_energy))
    np.save(path_outputs / "cost_reserve.npy", np.array(result.cost_reserve))
    # effective gama save
    np.save(path_outputs / "gammas_eff.npy", np.array(result.gammas_eff))
    # p save for each source
    np.save(path_outputs / "p_coal.npy", np.array(result.p_coal))
    np.save(path_outputs / "p_lng.npy", np.array(result.p_lng))
    np.save(path_outputs / "p_nuclear.npy", np.array(result.p_nuclear))
    np.save(path_outputs / "p_solar.npy", np.array(result.p_solar))
    np.save(path_outputs / "p_wind.npy", np.array(result.p_wind))
    np.save(path_outputs / "p_hydro.npy", np.array(result.p_hydro))
    np.save(path_outputs / "r_lng.npy", np.array(result.r_lng))

def suppress_gurobi_parallel_spam():
    print(); (_ := gp.Model()).setParam("OutputFlag", 0)


def parallel(idx_hour):
    solver = Solver(con, ren, demand, result)
    solver.solve(idx_hour, gamma)


def main():
    # data loading
    global con, ren, demand, result
    data = Data(gamma)
    con = Conventional(data)
    ren = Renewable(data)
    demand = Demand(data)
    result = Result(con, ren)

    # solving
    suppress_gurobi_parallel_spam()
    timer_start = timer()
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        list(executor.map(parallel, range(8760)))
    timer_end = timer()

    # saving
    path_outputs = data.path_data / "outputs" / f"{gamma}" / Path(__file__).stem
    print(f"\nTime taken for solving optimization: {(timer_end - timer_start):.3f}s \
          \nSaving result at: {str(path_outputs)}" )
    process_save_result(result, path_outputs)


if __name__=="__main__":
    gamma = float(ParseArgs().gamma)
    main()