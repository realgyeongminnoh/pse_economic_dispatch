import numpy as np
import cvxpy as cp

from src.generators import Generators
from src.others import Others
from src.committed_generators import Committed_generators


class Solver:
    def __init__(self, generators : Generators, others : Others, committed_generators : Committed_generators):
        self.generators = generators
        self.others = others
        self.committed_generators = committed_generators
        # solver to contain result (of single compute_smp call)
        self.status = None # 0 = feasible, -1 = infeasible; thermalgen_demand < (thermal pmin sum), -2 = infeasble; thermalgen_demand > (thermal pmin max)
        self.smp = None 
        self.p_error_demand = None # percentage error from equality constraint 
        self.cost_system = None
        self.powers_by_source = None # coal, lng, nuclear
        self.cost_by_source = None # coal, lng, nuclear
        self.powers_by_bus = None # powers_by_bus len changes as # committed generators change. only for analysis for specific hour
        # cost unit: 1,000 $ / MWh = 1 $ / kWh = 1000 krw / kWh (according to m file from KPG)

    def Compute_smp(self, idx_hour, save_powers_by_bus:bool = False):
        # re initialization for reuse of Compute_smp
        self.status, self.smp, self.p_error_demand, self.cost_system, self.powers_by_bus = 0, np.nan, np.nan, np.nan, np.nan
        self.cost_by_source = np.array([np.nan, np.nan, np.nan])
        self.powers_by_source = np.array([np.nan, np.nan, np.nan])
    
        

        demand = self.others.thermalgen_demands[idx_hour]
        if not (demand >= self.committed_generators.committed_gen_pmin.sum()):
            self.status = -1
            return # probably sensible to substitute with smp = 0 (idk this is all bc UC commitments; probably could tune commitments too later)
        
        if not (demand <= self.committed_generators.committed_gen_pmax.sum()):
            self.status = -2
            return # not happening # idk

        # solving quadratic convex problem by cvxpy - checked with julia ipopt
        powers = cp.Variable(self.committed_generators.committed_gen_count)
        cost_system = cp.sum(
            cp.multiply(self.committed_generators.committed_gencost_c2, cp.square(powers)) + 
            cp.multiply(self.committed_generators.committed_gencost_c1, powers) + 
            self.committed_generators.committed_gencost_c0) # constant term added for just 
        constraints = [
            powers >= self.committed_generators.committed_gen_pmin,
            powers <= self.committed_generators.committed_gen_pmax,
            cp.sum(powers) == demand,
        ]        
        objective = cp.Minimize(cost_system)
        problem = cp.Problem(objective, constraints)
        problem.solve(solver=cp.OSQP) # checked with julia ipopt 

        # updating single hour optimzation result
        self.smp = -constraints[-1].dual_value
        self.p_error_demand = abs(powers.value.sum() - demand) / demand * 100
        self.cost_system = cost_system.value
        self.powers_by_bus = powers.value if save_powers_by_bus else None

        ### powers_by_source - checked and correct (thermalgen_demand)
        committed_idx_gen_coal = self.committed_generators.committed_idx_gen_coal
        committed_idx_gen_lng = self.committed_generators.committed_idx_gen_lng
        committed_idx_gen_nuclear = self.committed_generators.committed_idx_gen_nuclear
    
        powers_by_bus_coal = powers.value[committed_idx_gen_coal]
        powers_by_bus_lng = powers.value[committed_idx_gen_lng]
        powers_by_bus_nuclear = powers.value[committed_idx_gen_nuclear]

        self.powers_by_source = np.array([powers_by_bus_coal.sum(), powers_by_bus_lng.sum(), powers_by_bus_nuclear.sum()])

        ### cost_by_source - checked and correct (also with cost_system)
        cost_by_source_coal = np.sum(self.committed_generators.committed_gencost_c2[committed_idx_gen_coal] * (powers_by_bus_coal ** 2) + 
                                        self.committed_generators.committed_gencost_c1[committed_idx_gen_coal] * powers_by_bus_coal + 
                                        self.committed_generators.committed_gencost_c0[committed_idx_gen_coal])
        
        cost_by_source_lng = np.sum(self.committed_generators.committed_gencost_c2[committed_idx_gen_lng] * (powers_by_bus_lng ** 2) + 
                                        self.committed_generators.committed_gencost_c1[committed_idx_gen_lng] * powers_by_bus_lng + 
                                        self.committed_generators.committed_gencost_c0[committed_idx_gen_lng])
        
        cost_by_source_nuclear = np.sum(self.committed_generators.committed_gencost_c2[committed_idx_gen_nuclear] * (powers_by_bus_nuclear ** 2) + 
                                        self.committed_generators.committed_gencost_c1[committed_idx_gen_nuclear] * powers_by_bus_nuclear + 
                                        self.committed_generators.committed_gencost_c0[committed_idx_gen_nuclear])

        self.cost_by_source = np.array([cost_by_source_coal, cost_by_source_lng, cost_by_source_nuclear])