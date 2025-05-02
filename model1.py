import os
import csv
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
    renewable = Renewable()
    demand = Demand()
    commitment = Commitment()
    data.load_thermal(thermal)
    data.load_renewable_capacity(renewable)
    data.load_renewable_generation(renewable)
    data.load_demand(demand)
    data.load_commitment_decision(commitment)
    results = Results(thermal, renewable, commitment)   

    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        list(executor.map(parallel, range(8760)))
    results.process_outputs()


if __name__=="__main__":
    main()