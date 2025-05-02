import numpy as np
import gurobipy as gp

from src.thermal import Thermal
from src.renewable import Renewable
from src.demand import Demand
from src.commitment import Commitment
from src.results import Results


class Solver:
    def __init__(self, thermal: Thermal, renewable: Renewable, demand: Demand, commitment: Commitment, results: Results):
        self.thermal = thermal
        self.renewable = renewable
        self.demand = demand
        self.commitment = commitment
        self.results = results


    def solve(self, idx_hour):
        hourly_decision = self.commitment.decision[idx_hour]

        # model declaration
        model = gp.Model()
        model.setParam("OutputFlag", 0)

        # varaible declaration with min max bounds (implicit inequality constraints)
        p_thermal = model.addVars(self.thermal.count, lb=(self.thermal.pmin * hourly_decision).tolist(), ub=(self.thermal.pmax * hourly_decision).tolist())
        p_solar = model.addVars(self.renewable.count, lb=0, ub=self.renewable.solar_generation[idx_hour].tolist())
        p_wind = model.addVars(self.renewable.count, lb=0, ub=self.renewable.wind_generation[idx_hour].tolist())
        p_hydro = model.addVars(self.renewable.count, lb=0, ub=self.renewable.hydro_generation[idx_hour].tolist())
        
        # equality constraint declaration
        model.addConstr(
            gp.quicksum(p_thermal[g] for g in range(self.thermal.count)) +   # sum of p_thermal
            gp.quicksum(p_solar[b] for b in range(self.renewable.count)) +   # sum of p_solar
            gp.quicksum(p_wind[b] for b in range(self.renewable.count)) +    # sum of p_wind
            gp.quicksum(p_hydro[b] for b in range(self.renewable.count))     # sum of p_hydro
            == float(self.demand.total[idx_hour])
        )

        # objective function declaration (total cost to run thermal; excluding thermal units' no load cost term)
        model.setObjective(
            gp.quicksum(
                self.thermal.c2.tolist()[g] * p_thermal[g] * p_thermal[g] + self.thermal.c1.tolist()[g] * p_thermal[g]
                for g in range(self.thermal.count)
            ), gp.GRB.MINIMIZE
        )

        # solve
        model.optimize()

        # result collection
        if model.Status == gp.GRB.OPTIMAL:
            self.results.smp[idx_hour] = model.getAttr("Pi")[0]       # SMP
            self.results.cost_system[idx_hour] = model.ObjVal         # total system cost
            self.results.p[idx_hour] = np.array(model.getAttr("X"))   # power generation for 713 generators and buses

        else:
            self.results.smp[idx_hour] = np.nan
            self.results.cost_system[idx_hour] = np.nan
            self.results.p[idx_hour] = np.empty(8760) * np.nan

            if model.Status == gp.GRB.INFEASIBLE:
                model.computeIIS()
                if model.getVars()[0].IISUB:
                    print(f"Problem for {idx_hour} is infeasible: upper bound in variables")
                else:
                    print(f"Problem for {idx_hour} is infeasible: lower bound in variables")
            else:
                print("https://docs.gurobi.com/projects/optimizer/en/current/reference/numericcodes/statuscodes.html")
                print(f"Problem for {idx_hour} is neither optimal nor infeasible: {model.Status} status code")