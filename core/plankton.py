class PlanktonAnalysis:

    def __init__(self, n, V, V_src, A_src, A_a, V_d):
        self.n = n
        self.V = V
        self.V_src = V_src
        self.A_src = A_src
        self.A_a = A_a
        self.V_d = V_d

    def calculate_abundance(self):

        if any(x <= 0 for x in [self.n, self.V, self.V_src, self.A_src, self.A_a, self.V_d]):
            return None

        N = self.n * self.V * (self.V_src * self.A_src) / (self.A_a * self.V_d)

        return N