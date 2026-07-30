from mlos.analysis.dataset_analyzer import DatasetAnalyzer

analyzer = DatasetAnalyzer()

dataset = analyzer.analyze("playground/sample.csv")

print(dataset)