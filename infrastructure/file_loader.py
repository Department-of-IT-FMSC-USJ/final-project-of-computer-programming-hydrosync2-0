import pandas as pd

class FileLoader:

    def load_excel(self, file):

        df = pd.read_excel(file)

        return df