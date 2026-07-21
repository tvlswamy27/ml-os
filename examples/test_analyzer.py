from mlos.io.data_loader import DataLoader
from mlos.analysis.dataset_analyzer import DatasetAnalyzer

loader = DataLoader()
analyzer = DatasetAnalyzer()

df = loader.load("playground/sample.csv")

dataset = analyzer.analyze(df)

print(dataset)