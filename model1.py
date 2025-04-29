from src import *


thermal = Thermal()
renewable = Renewable()
demand = Demand()
commitment = Commitment()
data = Data()

data.load_thermal(thermal)
data.load_renewable_capacity(renewable)
data.load_renewable_generation(renewable)
data.load_demand(demand)
data.load_commitment_decision(commitment)