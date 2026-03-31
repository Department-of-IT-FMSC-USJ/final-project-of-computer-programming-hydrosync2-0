import math

class WaterQualityAnalysis:
    
    def __init__(self, chl_a=None, phosphorus=None, secchi_depth=None, nitrogen=None):
        self.chl_a = chl_a
        self.phosphorus = phosphorus
        self.secchi_depth = secchi_depth
        self.nitrogen = nitrogen

    def tsi_chlorophyll(self):

        if self.chl_a is None or self.chl_a <= 0:
            return None

        return 9.81 * math.log(self.chl_a) + 30.6

    def tsi_phosphorus(self):

        if self.phosphorus is None or self.phosphorus <= 0:
            return None

        return 14.42 * math.log(self.phosphorus) + 4.15


    def tsi_secchi(self):

        if self.secchi_depth is None or self.secchi_depth <= 0:
            return None

        return 60 - (14.41 * math.log(self.secchi_depth))

    def np_ratio(self):

        if self.nitrogen is None or self.phosphorus is None:
            return None

        if self.phosphorus == 0:
            return None

        return self.nitrogen / self.phosphorus

    #interpretation part
    def interpret_tsi(self, value):
        if value is None: return {"short": "No data", "detailed": "No TSI data available to interpret."}
        base = "**Trophic State Index (TSI)** measures the biological productivity of a lake based on nutrient levels like phosphorus and nitrogen. "
        if value < 40:
            return {"short": "Oligotrophic (Clean)", "detailed": base + "The water is highly clear with low nutrients, meaning very little algae growth. Excellent for drinking and swimming."}
        elif value <= 50:
            return {"short": "Mesotrophic (Moderate)", "detailed": base + "The water has a balanced level of nutrients. It supports a healthy, diverse population of fish and aquatic plants."}
        else:
            return {"short": "Eutrophic (Polluted)", "detailed": base + "High nutrients are causing excessive algae growth. This reduces water clarity and can starve fish of oxygen."}
        
    def interpret_np(self, ratio):
        if ratio is None: return {"short": "No data", "detailed": "No ratio data available."}
        base = "**Nitrogen to Phosphorus Ratio (N:P)** helps identify which nutrient is the 'limiting factor' controlling algae growth in an aquatic ecosystem. "
        if ratio < 10:
            return {"short": "Nitrogen limiting", "detailed": base + "Lack of nitrogen often triggers toxic 'blue-green algae' (cyanobacteria) to bloom since they safely pull nitrogen from the air when water levels are low."}
        elif ratio > 20:
            return {"short": "Phosphorus limiting", "detailed": base + "The ecosystem lacks phosphorus. This is the natural, healthy state for most freshwater lakes, preventing excessive weed and algae growth."}
        else:
            return {"short": "Balanced nutrients", "detailed": base + "Both Nitrogen and Phosphorus are present in equal, optimal amounts to support standard aquatic plant life."}

    # full analyse
    def full_analysis(self):

        tsi_chl = self.tsi_chlorophyll()
        tsi_p = self.tsi_phosphorus()
        tsi_sd = self.tsi_secchi()
        np = self.np_ratio()

        return {
            "TSI (Chlorophyll)": tsi_chl,
            "TSI (Phosphorus)": tsi_p,
            "TSI (Secchi)": tsi_sd,
            "TSI Interpretation (Chl)": self.interpret_tsi(tsi_chl),
            "N:P Ratio": np,
            "N:P Interpretation": self.interpret_np(np)
        }