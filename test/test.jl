using MAT, JuMP, Ipopt

# generator-related parameters; unit1, unit2, unit3
count_generators = 3
iterator_generators = 1:3
Pmin = [0; 100; 0]
Pmax = [500; 350; 200]
MC = [10; 30; 35]

# hourly demands; 1h, 2h,3h
count_hours = 3
iterator_hours = count_hours
Pd = [550; 750; 1050]



hour_of_interest = 1
# model declaration
ED = Model(Ipopt.Optimizer)
# variable declaration
@variable(ED, Pmin[g] <= pg[g in genset] <= Pmax[g])
# constraint declaration
@constraint(ED, load_generation_balance, sum(pg) == Pd[hour_of_interest])
# objecive function declaration
@expression(ED, OCgen[g in iterator_generators], MC[g] * pg[g]) # element-wise multiplication
@expression(ED, OC, sum(OCgen)) # sum; complete dot-product
@objective(ED, Min, OC) # value.(OCgen) / value(OC)

optimize!(ED)

value.(pg)
value.(OCgen)

dual.(load_generation_balance)
