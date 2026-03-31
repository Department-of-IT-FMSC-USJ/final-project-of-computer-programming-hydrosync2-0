import math

class BiodiversityAnalysis:

    def __init__(self, species_counts):
        # remove zero counts
        self.species_counts = [n for n in species_counts if n > 0]

        self.N = sum(self.species_counts)      # total individuals
        self.S = len(self.species_counts)      # number of species


    def simpson_index(self):
        if self.N < 2:
            return 0

        numerator = sum(n * (n - 1) for n in self.species_counts)
        denominator = self.N * (self.N - 1)

        return 1 - (numerator / denominator)


    def shannon_index(self):
        if self.N == 0:
            return 0

        H = 0
        for n in self.species_counts:
            p = n / self.N
            H += p * math.log(p)

        return -H


    def pielou_evenness(self):
        H = self.shannon_index()

        if self.S <= 1:
            return 0

        return H / math.log(self.S)


    def richness_index(self):
        if self.N <= 1:
            return 0

        return (self.S - 1) / math.log(self.N)


    def full_analysis(self):
        return {
            "shannon_index": self.shannon_index(),
            "simpson_index": self.simpson_index(),
            "pielou_evenness": self.pielou_evenness(),
            "richness_index": self.richness_index()
        }