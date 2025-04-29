class Demand:
    def __init__(self):
        self.total = None

        # model 1 - 183 infeasibilities
        self.renewable = None # demand to be fulfilled by renewable generation
        self.thermal = None # demand to be fulfilled by thermal generation
    
        # model 2
        # infeasibility corrected by "thermal curtailment"
        # reneable generation is fixed - probably not that realistic WOTTTTTTTTTTTTT
        self.renewalbe_model2 = None
        self.thermal_model2 = None

        # model 3
        # infeasibility corrected by renewable curtailment
        # optimization now have renewable powers as variables...
        # not known before optimum...

        # model 4 AAAAAAAAAAAAAAAAAAAAA 
