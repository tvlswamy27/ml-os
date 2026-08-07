from mlos.analysis.dataset_analyzer import DatasetAnalyzer
from mlos.io.data_loader import DataLoader

loader = DataLoader()
analyzer = DatasetAnalyzer()

df = loader.load("playground/sample.csv")

dataset = analyzer.analyze(df)

print(dataset)
