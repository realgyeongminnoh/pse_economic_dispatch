import numpy as np

from src.generators import Generators
from src.others import Others


class Committed_generators:
    def __init__(self, generators : Generators, others : Others):
        self.generators = generators
        self.others = others
        # this class is for helper for solver /  analysis purpose (while its method is used everytime solver Compute_smp is called and idx_hour changes
        self.idx_hour: int = None
        self.commitments = None
        self.committed_gen_count = None
        self.committed_gen_pmax = None
        self.committed_gen_pmin = None
        self.committed_gencost_c2 = None
        self.committed_gencost_c1 = None
        self.committed_gencost_c0 = None
        self.gentypes_description: dict = {0: "Coal", 1: "LNG", 2: "Nuclear"} # fixed
        self.gentypes = None
        self.gentypes_colors = None
        self.idx_gen_coal = None
        self.idx_gen_lng = None
        self.idx_gen_nuclear = None

    def Get_committed_generators(self, idx_hour):
        self.commitments = self.others.commitments_matrix[idx_hour]

        self.committed_gen_count = self.commitments.sum()
        self.committed_gen_pmax = self.generators.gen_pmax[self.commitments]
        self.committed_gen_pmin = self.generators.gen_pmin[self.commitments]
        self.committed_gencost_c2 = self.generators.gencost_c2[self.commitments]
        self.committed_gencost_c1 = self.generators.gencost_c1[self.commitments]
        self.committed_gencost_c0 = self.generators.gencost_c0[self.commitments]
        self.committed_gentypes = self.generators.gentypes[self.commitments]
        self.committed_gentypes_colors = self.generators.gentypes_colors[self.commitments]
        self.committed_idx_gen_coal = np.where(self.committed_gentypes == 0)[0]
        self.committed_idx_gen_lng = np.where(self.committed_gentypes == 1)[0]
        self.committed_idx_gen_nuclear = np.where(self.committed_gentypes == 2)[0]