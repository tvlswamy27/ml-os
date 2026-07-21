from mlos.io.data_loader import DataLoader

loader = DataLoader()

df = loader.load("playground/sample.csv")

print(df)