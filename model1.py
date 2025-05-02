import os
import numpy as np
from concurrent.futures import ProcessPoolExecutor

from src import *


def parallel(idx_hour):
    solver = Solver(thermal, renewable, demand, commitment, results)
    solver.solve(idx_hour)


def main():
    global thermal, renewable, demand, commitment, results
    data = Data()
    thermal = Thermal()
    data.load_thermal(thermal)
    renewable = Renewable()
    data.load_renewable_capacity(renewable)
    data.load_renewable_generation(renewable)
    demand = Demand()
    data.load_demand(demand)
    commitment = Commitment()
    data.load_commitment_decision(commitment)
    results = Results(thermal, renewable, commitment)   

    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        list(executor.map(parallel, range(8760)))
    results.process_outputs()


if __name__=="__main__":
    main()