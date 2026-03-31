class InterpretationService:

    def __init__(self, interpretations):
        self.interpretations = interpretations

    # 🔹 Step 1: remove weak relationships
    def filter_strong(self, threshold=0.5):

        strong = []

        for item in self.interpretations:
            if abs(item["correlation"]) >= threshold:
                strong.append(item)

        return strong

    # 🔹 Step 2: get top N strongest relationships
    def get_top_insights(self, top_n=5):

        strong = self.filter_strong()

        # sort by absolute correlation value
        strong.sort(key=lambda x: abs(x["correlation"]), reverse=True)

        return strong[:top_n]

    # 🔹 Step 3: format for UI
    def format_insights(self, insights):

        formatted = []

        for item in insights:
            col1, col2 = item["pair"]
            corr = item["correlation"]
            text = item["interpretation"]

            formatted.append(
                f"{col1} vs {col2} → {corr:.2f} → {text}"
            )

        return formatted

    # 🔹 Step 4: full report (for download)
    def full_report_text(self):

        lines = []

        for item in self.interpretations:
            col1, col2 = item["pair"]
            corr = item["correlation"]
            text = item["interpretation"]

            lines.append(
                f"{col1} vs {col2} → {corr:.2f} → {text}"
            )

        return "\n".join(lines)