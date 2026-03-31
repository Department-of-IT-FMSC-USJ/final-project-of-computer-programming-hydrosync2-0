import math

def simpson_diversity(filtered):
    N = sum(filtered)
    numerator = sum(n * (n - 1) for n in filtered)
    denominator = N * (N - 1)
    D = numerator / denominator
    SID = 1 - D
    return SID

def shannon_index(filtered):
    N = sum(filtered)
    if N == 0:
        return None

    H = 0
    for n in filtered:
        if n > 0:
            p = n / N
            H += p * math.log(p)
    return -H

def pielou_evenness(filtered):
    H = shannon_index(filtered)
    if H is None: return None
    S = len(filtered)
    if S <= 1: return 0.0
    E = H / math.log(S)
    return E

def plankton_abundance():
    n = input("Enter number of observed plankton (n): ")
    V = input("Enter volume of water in sample bottle (ml) (V): ")
    V_src = input("Enter volume of water in SRC (ml) (Vsrc): ")
    A_src = input("Enter SRC's area of view (mm^2) (Asrc): ")
    A_a = input("Enter microscope area of view (mm^2) (Aa): ")
    V_d = input("Enter volume of filtered water sample (m^3) (Vd): ")

    if not (n.isdigit() and V.isdigit() and V_src.isdigit() and A_src.isdigit() and A_a.isdigit() and V_d.isdigit()):
        print("Error: All inputs must be positive integers with no decimals or symbols.")
        return None ##only for value passing (Stop the function and return no meaningful value)
    n = float(n)
    V = float(V)
    V_src = float(V_src)
    A_src = float(A_src)
    A_a = float(A_a)
    V_d = float(V_d)

    if any(x <= 0 for x in [n, V, V_src, A_src, A_a, V_d]):
        raise ValueError("All inputs must be greater than zero.")  ##not enter to 0 value (if x=0 it dosen't work)

    N = n * V * (V_src * A_src) / (A_a * V_d)
    return N ##not print

def richness_index(filtered):
    N = sum(filtered)
    if N <= 1: return 0.0
    numerator = (len(filtered)) - 1
    denominator = math.log(N)
    D = numerator / denominator
    return D