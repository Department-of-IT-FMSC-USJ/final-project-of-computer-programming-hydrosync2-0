class DataProcessor:
    #biodiversity
    def extract_species_data(self, df):

        dataset = []

        for _, row in df.iterrows():

            species_counts = row[1:].tolist()  # skip first column if it's label

            dataset.append(species_counts)

        return dataset
    
    #plankton
    def extract_plankton_data(self, df):

        dataset = []

        for _, row in df.iterrows():

            values = row[1:].tolist()

            # Ensure all values are numbers
            if any(v is None for v in values):
                continue

            dataset.append(values)

        return dataset
    
    #tsi water quality
    def extract_water_quality_data(self, df):

        dataset = []

        for _, row in df.iterrows():

            values = row[1:].tolist()

            dataset.append({
                "chl_a": values[0],
                "phosphorus": values[1],
                "secchi": values[2],
                "nitrogen": values[3]
            })

        return dataset
    