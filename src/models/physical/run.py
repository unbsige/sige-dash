import pandas as pd

columns = ["date_time", "pv_power"]
file_path = "./data/raw/pv_power_kw_20221213_20250630_PT5M.csv"

df_power = pd.read_csv(file_path, index_col="date_time", parse_dates=["date_time"], usecols=columns)
df_power = df_power.rename(columns={"pv_power": "ac_power_kw"})
df_power = df_power.sort_index()

print("-" * 80)
print(" => Dados carregados do arquivo CSV")
print("-" * 80)
print(f"Shape: {df_power.shape}")
print(f"Período: {df_power.index.min()} até {df_power.index.max()}")
print(f"frequency dataset: {df_power.index.freqstr} - infer: {pd.infer_freq(df_power.index)}")
print(f"\nValores ausentes (NaN):\n{df_power.isna().sum()}")
print("-" * 80)
