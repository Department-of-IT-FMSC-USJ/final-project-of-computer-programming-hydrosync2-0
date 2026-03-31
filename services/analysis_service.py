from core.biodiversity import BiodiversityAnalysis
from core.plankton import PlanktonAnalysis
from core.water_quality import WaterQualityAnalysis
#file loader
from infrastructure.file_loader import FileLoader
from infrastructure.data_processor import DataProcessor
#coorelation
from core.correlation import CorrelationAnalysis
#analysis interpretations
from services.interpretation_service import InterpretationService



class AnalysisService:

    def run_biodiversity(self, species_counts):
        return BiodiversityAnalysis(species_counts).full_analysis()

    def run_plankton(self, inputs):
        p = PlanktonAnalysis(*inputs)
        return {"Plankton Abundance": p.calculate_abundance()}
    
    def run_water_quality(self, inputs):

        analysis = WaterQualityAnalysis(
        chl_a=inputs.get("chl_a"),
        phosphorus=inputs.get("phosphorus"),
        secchi_depth=inputs.get("secchi"),
        nitrogen=inputs.get("nitrogen")
        )

        return analysis.full_analysis()
    
    #file loader for biodiversity
    def run_biodiversity_on_file(self, file):

        loader = FileLoader()
        processor = DataProcessor()

        df = loader.load_excel(file)

        dataset = processor.extract_species_data(df)

        results = []

        for species_counts in dataset:

            analysis = BiodiversityAnalysis(species_counts)

            results.append(analysis.full_analysis())

        return df, results
    
    #file loader for plankton
    def run_plankton_on_file(self, file):

        loader = FileLoader()
        processor = DataProcessor()

        df = loader.load_excel(file)

        dataset = processor.extract_plankton_data(df)

        results = []

        for values in dataset:

            analysis = PlanktonAnalysis(*values)

            result = analysis.calculate_abundance()

            results.append({
                "Plankton Abundance": result
            })

        return df, results
    
    #file loader for tsi
    def run_water_quality_on_file(self, file):

        loader = FileLoader()
        processor = DataProcessor()

        df = loader.load_excel(file)

        dataset = processor.extract_water_quality_data(df)

        results = []

        for data in dataset:

            analysis = WaterQualityAnalysis(
                chl_a=data["chl_a"],
                phosphorus=data["phosphorus"],
                secchi_depth=data["secchi"],
                nitrogen=data["nitrogen"]
            )

            results.append(analysis.full_analysis())

        return df, results
    
    #corelation
    def run_correlation_analysis(self, file):

        loader = FileLoader()

        df = loader.load_excel(file)

        # Force aggressive numeric conversion on all columns except the very first (often Site Name)
        import pandas as pd
        if len(df.columns) > 1:
            for col in df.columns[1:]:
                # If pandas thinks it's an object, it might have European commas (e.g. "24,5")
                if df[col].dtype == object:
                    df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')

        analysis = CorrelationAnalysis(df)

        numeric_df = analysis.get_numeric_data()

        if numeric_df.empty or len(numeric_df) < 2:
            raise ValueError("The uploaded dataset must contain at least two rows of valid numeric data across columns to calculate correlations. Please fill out the empty template with numbers before uploading.")

        corr_matrix = analysis.compute_correlation()

        if corr_matrix.empty or corr_matrix.isna().all().all():
            raise ValueError("Calculation failed: The correlation matrix is completely empty. Ensure your columns have overlapping numeric data and no text blocks inside the numeric rows.")

        heatmap = analysis.generate_heatmap(corr_matrix)

        interpretations = analysis.interpret(corr_matrix)

        # NEW PART
        interpretation_service = InterpretationService(interpretations)

        top_insights = interpretation_service.get_top_insights()

        formatted_insights = interpretation_service.format_insights(top_insights)

        full_report = interpretation_service.full_report_text()

        return df, corr_matrix, heatmap, formatted_insights, full_report