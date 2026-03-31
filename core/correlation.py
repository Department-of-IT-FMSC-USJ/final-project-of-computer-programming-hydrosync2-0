import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

class CorrelationAnalysis:

    def __init__(self, df):
        self.df = df

    # Step 1: extract only numeric columns
    def get_numeric_data(self):
        return self.df.select_dtypes(include='number')

    # Step 2: compute correlation matrix
    def compute_correlation(self):
        numeric_df = self.get_numeric_data()
        return numeric_df.corr(method='pearson')

    # Step 3: generate heatmap
    def generate_heatmap(self, corr_matrix):

        plt.figure(figsize=(10, 8))

        sns.heatmap(
            corr_matrix,
            annot=True,
            fmt=".2f",
            cmap="coolwarm",
            linewidths=0.5
        )

        plt.title("Correlation Heatmap")

        return plt

    # Step 4: interpretation engine
    def interpret(self, corr_matrix):

        interpretations = []

        for col1 in corr_matrix.columns:
            for col2 in corr_matrix.columns:

                if col1 == col2:
                    continue

                value = corr_matrix.loc[col1, col2]

                # avoid duplicate pairs
                if (col2, col1) in [(i["pair"][0], i["pair"][1]) for i in interpretations]:
                    continue

                text = self._interpret_value(value)

                interpretations.append({
                    "pair": (col1, col2),
                    "correlation": value,
                    "interpretation": text
                })

        return interpretations

    def _interpret_value(self, value):

        if value > 0.7:
            return "Strong positive relationship"
        elif value > 0.4:
            return "Moderate positive relationship"
        elif value > 0.2:
            return "Weak positive relationship"
        elif value > -0.2:
            return "No significant relationship"
        elif value > -0.4:
            return "Weak negative relationship"
        elif value > -0.7:
            return "Moderate negative relationship"
        else:
            return "Strong negative relationship"