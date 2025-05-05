import numpy as np
import gurobipy as gp

from src.conventional import Conventional
from src.renewable import Renewable
from src.demand import Demand
from src.result import Result


class Solver:
    def __init__(self, con: Conventional, ren: Renewable, demand: Demand, result: Result):
        self.con = con
        self.ren = ren
        self.demand = demand
        self.result = result


    def solve(self, idx_hour, gamma):
        # model declaration
        model = gp.Model()
        model.setParam("OutputFlag", 0)

        # varaible declaration with min max bounds (inequality constraints applied implicitly)
        p_coal = model.addVars(self.con.coal.count, lb=self.con.coal.pmin[idx_hour].tolist(), ub=self.con.coal.pmax[idx_hour].tolist())
        p_lng = model.addVars(self.con.lng.count, lb=self.con.lng.pmin[idx_hour].tolist(), ub=self.con.lng.pmax[idx_hour].tolist())
        p_nuclear = model.addVars(self.con.nuclear.count, lb=self.con.nuclear.pmin[idx_hour].tolist(), ub=self.con.nuclear.pmax[idx_hour].tolist())
        p_solar = model.addVars(self.ren.solar.count, lb=0, ub=self.ren.solar.pmax[idx_hour].tolist())
        p_wind = model.addVars(self.ren.wind.count, lb=0, ub=self.ren.wind.pmax[idx_hour].tolist())
        p_hydro = model.addVars(self.ren.hydro.count, lb=0, ub=self.ren.hydro.pmax[idx_hour].tolist())

        # demand equality constraint declaration
        model.addConstr(
            gp.quicksum(p_coal[g] for g in range(self.con.coal.count)) +
            gp.quicksum(p_lng[g] for g in range(self.con.lng.count)) +
            gp.quicksum(p_nuclear[g] for g in range(self.con.nuclear.count)) +
            gp.quicksum(p_solar[b] for b in range(self.ren.solar.count)) +
            gp.quicksum(p_wind[b] for b in range(self.ren.wind.count)) +
            gp.quicksum(p_hydro[b] for b in range(self.ren.hydro.count))
            == float(self.demand.total[idx_hour])
        )

        # RESERVE CAPCITY
        # variable declaration
        r_lng = model.addVars(self.con.lng.count, lb=0, ub=(self.con.lng.pmax[idx_hour] - self.con.lng.pmin[idx_hour]).tolist())
        # for each lng unit, the sum of power output and reserve capacity must be less than the pmax (which respects the commitmnet decision)
        model.addConstrs(
            p_lng[g] + r_lng[g] <= self.con.lng.pmax[idx_hour].tolist()[g]
            for g in range(self.con.lng.count)
        )
        # total reserve capacity at optimum must be greater than the designated reserve capacity
        reserve_total_des = gamma * self.demand.total[idx_hour]
        model.addConstr(gp.quicksum(r_lng[g] for g in range(self.con.lng.count)) >= reserve_total_des)

        # objective function declaration
        # energy cost
        cost_energy = (
            gp.quicksum(
                self.con.coal.c2.tolist()[g] * p_coal[g] * p_coal[g] + self.con.coal.c1.tolist()[g] * p_coal[g] + self.con.coal.c0.tolist()[g]
                for g in range(self.con.coal.count)
            ) + 
            gp.quicksum(
                self.con.lng.c2.tolist()[g] * p_lng[g] * p_lng[g] + self.con.lng.c1.tolist()[g] * p_lng[g] + self.con.lng.c0.tolist()[g]
                for g in range(self.con.lng.count)
            ) + 
            gp.quicksum(
                self.con.nuclear.c2.tolist()[g] * p_nuclear[g] * p_nuclear[g] + self.con.nuclear.c1.tolist()[g] * p_nuclear[g] + self.con.nuclear.c0.tolist()[g]
                for g in range(self.con.nuclear.count)
            )
        )
        # reserve cost
        cost_reserve = (
            gp.quicksum(
                self.con.lng.c1.tolist()[g] * r_lng[g]
                for g in range(self.con.lng.count)
            )
        )
        # objective # only minimize energy cost
        model.setObjective(cost_energy, gp.GRB.MINIMIZE)

        # solve
        model.optimize()

        # result collection
        if model.Status == gp.GRB.OPTIMAL:
            if reserve_total_des == 0:
                reserve_total_des = 1

            reserve_total_opt = sum(r_lng[g].X for g in range(self.con.lng.count))
            self.result.smp[idx_hour] = model.getAttr("Pi")[0]                      # SMP
            self.result.cost_energy[idx_hour] = cost_energy.getValue()              # total system cost
            self.result.cost_reserve[idx_hour] = cost_reserve.getValue()            # total system cost
            self.result.gamma_eff[idx_hour] = reserve_total_opt / reserve_total_des # effective gamma
            self.result.pr[idx_hour] = np.array(model.getAttr("X"))                 # varaible values at optimum

        else:
            self.result.smp[idx_hour] = np.nan
            self.result.cost_energy[idx_hour] = np.nan
            self.result.cost_reserve[idx_hour] = np.nan
            self.result.gamma_eff[idx_hour] = np.nan
            self.result.pr[idx_hour] = np.empty((self.result.tc)) * np.nan

            if model.Status == gp.GRB.INFEASIBLE:
                model.computeIIS()
                if model.getVars()[0].IISUB:
                    print(f"Model 1 | Problem for {idx_hour} is infeasible: upper bound in variables")
                else:
                    print(f"Model 1 | Problem for {idx_hour} is infeasible: lower bound in variables")
            else:
                print("https://docs.gurobi.com/projects/optimizer/en/current/reference/numericcodes/statuscodes.html")
                print(f"Model 1 | Problem for {idx_hour} is neither optimal nor infeasible: {model.Status} status code")


    def solve_pre(self, idx_hour, alpha_coal, alpha_lng, alpha_nuclear, gamma):
        # cost curve tuning
        coal_c2 = self.con.coal.c2.copy() * alpha_lng # alpha_coal is substituted by alpha_lng
        coal_c1 = self.con.coal.c1.copy() * alpha_lng # alpha_coal is substituted by alpha_lng
        coal_c0 = self.con.coal.c0.copy() * alpha_lng # alpha_coal is substituted by alpha_lng
        lng_c2 = self.con.lng.c2.copy() * alpha_lng
        lng_c1 = self.con.lng.c1.copy() * alpha_lng
        lng_c0 = self.con.lng.c0.copy() * alpha_lng
        nuclear_c2 = self.con.nuclear.c2.copy() * alpha_nuclear
        nuclear_c1 = self.con.nuclear.c1.copy() * alpha_nuclear
        nuclear_c0 = self.con.nuclear.c0.copy() * alpha_nuclear

        # model declaration
        model = gp.Model()
        model.setParam("OutputFlag", 0)

        # varaible declaration with min max bounds (inequality constraints applied implicitly)
        p_coal = model.addVars(self.con.coal.count, lb=self.con.coal.pmin[idx_hour].tolist(), ub=self.con.coal.pmax[idx_hour].tolist())
        p_lng = model.addVars(self.con.lng.count, lb=self.con.lng.pmin[idx_hour].tolist(), ub=self.con.lng.pmax[idx_hour].tolist())
        p_nuclear = model.addVars(self.con.nuclear.count, lb=self.con.nuclear.pmin[idx_hour].tolist(), ub=self.con.nuclear.pmax[idx_hour].tolist())
        p_solar = model.addVars(self.ren.solar.count, lb=0, ub=self.ren.solar.pmax[idx_hour].tolist())
        p_wind = model.addVars(self.ren.wind.count, lb=0, ub=self.ren.wind.pmax[idx_hour].tolist())
        p_hydro = model.addVars(self.ren.hydro.count, lb=0, ub=self.ren.hydro.pmax[idx_hour].tolist())

        # equality constraint declaration
        model.addConstr(
            gp.quicksum(p_coal[g] for g in range(self.con.coal.count)) +
            gp.quicksum(p_lng[g] for g in range(self.con.lng.count)) +
            gp.quicksum(p_nuclear[g] for g in range(self.con.nuclear.count)) +
            gp.quicksum(p_solar[b] for b in range(self.ren.solar.count)) +
            gp.quicksum(p_wind[b] for b in range(self.ren.wind.count)) +
            gp.quicksum(p_hydro[b] for b in range(self.ren.hydro.count))
            == float(self.demand.total[idx_hour])
        )

        # RESERVE CAPCITY
        # variable declaration
        r_lng = model.addVars(self.con.lng.count, lb=0, ub=(self.con.lng.pmax[idx_hour] - self.con.lng.pmin[idx_hour]).tolist())
        # for each lng unit, the sum of power output and reserve capacity must be less than the pmax (which respects the commitmnet decision)
        model.addConstrs(
            p_lng[g] + r_lng[g] <= self.con.lng.pmax[idx_hour].tolist()[g]
            for g in range(self.con.lng.count)
        )
        # total reserve capacity at optimum must be greater than the designated reserve capacity
        reserve_total_des = gamma * self.demand.total[idx_hour]
        model.addConstr(gp.quicksum(r_lng[g] for g in range(self.con.lng.count)) >= reserve_total_des)

        # objective function declaration
        # energy cost
        cost_energy = (
            gp.quicksum(
                coal_c2.tolist()[g] * p_coal[g] * p_coal[g] + coal_c1.tolist()[g] * p_coal[g] + coal_c0.tolist()[g]
                for g in range(self.con.coal.count)
            ) + 
            gp.quicksum(
                lng_c2.tolist()[g] * p_lng[g] * p_lng[g] + lng_c1.tolist()[g] * p_lng[g] + lng_c0.tolist()[g]
                for g in range(self.con.lng.count)
            ) + 
            gp.quicksum(
                nuclear_c2.tolist()[g] * p_nuclear[g] * p_nuclear[g] + nuclear_c1.tolist()[g] * p_nuclear[g] + nuclear_c0.tolist()[g]
                for g in range(self.con.nuclear.count)
            )
        )
        # reserve cost
        cost_reserve = (
            gp.quicksum(
                lng_c1.tolist()[g] * r_lng[g]
                for g in range(self.con.lng.count)
            )
        )
        # objective # only minimize energy cost
        model.setObjective(cost_energy, gp.GRB.MINIMIZE)

        # solve
        model.optimize()

        if model.Status == gp.GRB.OPTIMAL:
            if reserve_total_des == 0:
                reserve_total_des = 1

            reserve_total_opt = sum(r_lng[g].X for g in range(self.con.lng.count))
            self.result.smp[idx_hour] = model.getAttr("Pi")[0]                      # SMP
            self.result.cost_energy[idx_hour] = cost_energy.getValue()              # total system cost
            self.result.cost_reserve[idx_hour] = cost_reserve.getValue()            # total system cost
            self.result.gamma_eff[idx_hour] = reserve_total_opt / reserve_total_des # effective gamma
            self.result.pr[idx_hour] = np.array(model.getAttr("X"))                 # varaible values at optimum

        else:
            self.result.smp[idx_hour] = np.nan
            self.result.cost_energy[idx_hour] = np.nan
            self.result.cost_reserve[idx_hour] = np.nan
            self.result.gamma_eff[idx_hour] = np.nan
            self.result.pr[idx_hour] = np.empty((self.result.tc)) * np.nan

            if model.Status == gp.GRB.INFEASIBLE:
                model.computeIIS()
                if model.getVars()[0].IISUB:
                    print(f"Model 1 | Problem for {idx_hour} is infeasible: upper bound in variables")
                else:
                    print(f"Model 1 | Problem for {idx_hour} is infeasible: lower bound in variables")
            else:
                print("https://docs.gurobi.com/projects/optimizer/en/current/reference/numericcodes/statuscodes.html")
                print(f"Model 1 | Problem for {idx_hour} is neither optimal nor infeasible: {model.Status} status code")


    def solve_post(self, idx_hour, alpha_coal, alpha_lng, alpha_nuclear, gamma):
        # cost curve tuning
        coal_c2 = self.con.coal.c2.copy() * alpha_lng # alpha_coal is substituted by alpha_lng
        coal_c1 = self.con.coal.c1.copy() * alpha_lng # alpha_coal is substituted by alpha_lng
        coal_c0 = self.con.coal.c0.copy() * alpha_lng # alpha_coal is substituted by alpha_lng
        lng_c2 = self.con.lng.c2.copy() * alpha_lng
        lng_c1 = self.con.lng.c1.copy() * alpha_lng
        lng_c0 = self.con.lng.c0.copy() * alpha_lng
        nuclear_c2 = self.con.nuclear.c2.copy() * alpha_nuclear
        nuclear_c1 = self.con.nuclear.c1.copy() * alpha_nuclear
        nuclear_c0 = self.con.nuclear.c0.copy() * alpha_nuclear

        # model declaration
        model = gp.Model()
        model.setParam("OutputFlag", 0)

        # varaible declaration with min max bounds (inequality constraints applied implicitly)
        p_coal = model.addVars(self.con.coal.count, lb=self.con.coal.pmin[idx_hour].tolist(), ub=self.con.coal.pmax[idx_hour].tolist())
        p_lng = model.addVars(self.con.lng.count, lb=self.con.lng.pmin[idx_hour].tolist(), ub=self.con.lng.pmax[idx_hour].tolist())
        p_nuclear = model.addVars(self.con.nuclear.count, lb=self.con.nuclear.pmin[idx_hour].tolist(), ub=self.con.nuclear.pmax[idx_hour].tolist())
        p_solar = model.addVars(self.ren.solar.count, lb=0, ub=self.ren.solar.pmax[idx_hour].tolist())
        p_wind = model.addVars(self.ren.wind.count, lb=0, ub=self.ren.wind.pmax[idx_hour].tolist())
        p_hydro = model.addVars(self.ren.hydro.count, lb=0, ub=self.ren.hydro.pmax[idx_hour].tolist())

        # equality constraint declaration
        model.addConstr(
            gp.quicksum(p_coal[g] for g in range(self.con.coal.count)) +
            gp.quicksum(p_lng[g] for g in range(self.con.lng.count)) +
            gp.quicksum(p_nuclear[g] for g in range(self.con.nuclear.count)) +
            gp.quicksum(p_solar[b] for b in range(self.ren.solar.count)) +
            gp.quicksum(p_wind[b] for b in range(self.ren.wind.count)) +
            gp.quicksum(p_hydro[b] for b in range(self.ren.hydro.count))
            == float(self.demand.total[idx_hour])
        )
        
        # RESERVE CAPCITY
        # variable declaration
        r_lng = model.addVars(self.con.lng.count, lb=0, ub=(self.con.lng.pmax[idx_hour] - self.con.lng.pmin[idx_hour]).tolist())
        # for each lng unit, the sum of power output and reserve capacity must be less than the pmax (which respects the commitmnet decision)
        model.addConstrs(
            p_lng[g] + r_lng[g] <= self.con.lng.pmax[idx_hour].tolist()[g]
            for g in range(self.con.lng.count)
        )
        # total reserve capacity at optimum must be greater than the designated reserve capacity
        reserve_total_des = gamma * self.demand.total[idx_hour]
        model.addConstr(gp.quicksum(r_lng[g] for g in range(self.con.lng.count)) >= reserve_total_des)

        # objective function declaration
        # energy cost
        cost_energy = (
            gp.quicksum(
                coal_c2.tolist()[g] * p_coal[g] * p_coal[g] + coal_c1.tolist()[g] * p_coal[g] + coal_c0.tolist()[g]
                for g in range(self.con.coal.count)
            ) + 
            gp.quicksum(
                lng_c2.tolist()[g] * p_lng[g] * p_lng[g] + lng_c1.tolist()[g] * p_lng[g] + lng_c0.tolist()[g]
                for g in range(self.con.lng.count)
            ) + 
            gp.quicksum(
                nuclear_c2.tolist()[g] * p_nuclear[g] * p_nuclear[g] + nuclear_c1.tolist()[g] * p_nuclear[g] + nuclear_c0.tolist()[g]
                for g in range(self.con.nuclear.count)
            )
        )
        # reserve cost
        cost_reserve = (
            gp.quicksum(
                lng_c1.tolist()[g] * r_lng[g]
                for g in range(self.con.lng.count)
            )
        )
        # objective # minimize both energy and reserve cost
        model.setObjective(cost_energy + cost_reserve, gp.GRB.MINIMIZE)

        # solve
        model.optimize()

        # result collection
        if model.Status == gp.GRB.OPTIMAL:
            if reserve_total_des == 0:
                reserve_total_des = 1

            reserve_total_opt = sum(r_lng[g].X for g in range(self.con.lng.count))
            self.result.smp[idx_hour] = model.getAttr("Pi")[0]                      # SMP
            self.result.cost_energy[idx_hour] = cost_energy.getValue()              # total system cost
            self.result.cost_reserve[idx_hour] = cost_reserve.getValue()            # total system cost
            self.result.gamma_eff[idx_hour] = reserve_total_opt / reserve_total_des # effective gamma
            self.result.pr[idx_hour] = np.array(model.getAttr("X"))                 # varaible values at optimum

        else:
            self.result.smp[idx_hour] = np.nan
            self.result.cost_energy[idx_hour] = np.nan
            self.result.cost_reserve[idx_hour] = np.nan
            self.result.gamma_eff[idx_hour] = np.nan
            self.result.pr[idx_hour] = np.empty((self.result.tc)) * np.nan

            if model.Status == gp.GRB.INFEASIBLE:
                model.computeIIS()
                if model.getVars()[0].IISUB:
                    print(f"Model 1 | Problem for {idx_hour} is infeasible: upper bound in variables")
                else:
                    print(f"Model 1 | Problem for {idx_hour} is infeasible: lower bound in variables")
            else:
                print("https://docs.gurobi.com/projects/optimizer/en/current/reference/numericcodes/statuscodes.html")
                print(f"Model 1 | Problem for {idx_hour} is neither optimal nor infeasible: {model.Status} status code")