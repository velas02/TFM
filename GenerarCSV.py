import os
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from StartupPreprocessor import StartupPreprocessor

# 1. instanciar preprocesador y cargar datos crudos
prep   = StartupPreprocessor()
raw_df = pd.read_csv(prep.csv_path)

# 2. limpieza de dominio y etiquetas
df_clean = prep._domain_clean(raw_df.copy())
y        = df_clean["labels"].astype(int)

# 3. reproducir split train/test (seed fija)
_, test_idx = train_test_split(
    df_clean.index, test_size=0.2, stratify=y, random_state=42
)

# 4. reconstruir test y añadir etiquetas
test_raw = raw_df.loc[test_idx].copy()
test_raw["labels"] = y.loc[test_idx].values

# 5. cargar pipeline entrenado
svm_pipe = joblib.load("models/svm_pipeline.pkl")

# 6. calcular probabilidad de éxito (p1) para cada startup en test
records = []
for idx, row in test_raw.iterrows():
    inst = row.drop("labels").to_frame().T
    df_i = prep.preprocess_instance(inst)
    X_i  = svm_pipe.named_steps['prep'].transform(df_i)
    p1   = svm_pipe.named_steps['svc'].predict_proba(X_i)[0, 1]
    records.append({"idx": idx, "label": row["labels"], "p1": p1})

df_probs = pd.DataFrame(records)

# 7. seleccionar las startups más cercanas a 0.5 para cada clase
df_pos = df_probs[(df_probs["label"] == 1) & (df_probs["p1"] >= 0.5)].copy()
df_neg = df_probs[(df_probs["label"] == 0) & (df_probs["p1"] < 0.5)].copy()

df_pos["diff"] = (df_pos["p1"] - 0.5).abs()
df_neg["diff"] = (df_neg["p1"] - 0.5).abs()

best_pos = df_pos.sort_values("diff").iloc[0]
best_neg = df_neg.sort_values("diff").iloc[0]

# 8. extraer las filas originales y convertir a DataFrame de una fila
serie_exitosa    = test_raw.loc[best_pos["idx"]].drop("labels")
serie_no_exitosa = test_raw.loc[best_neg["idx"]].drop("labels")

df_exitosa    = serie_exitosa.to_frame().T
df_no_exitosa = serie_no_exitosa.to_frame().T

# 9. exportar como CSV de una sola fila
output_dir = "ejemplos_validacion"
os.makedirs(output_dir, exist_ok=True)
df_exitosa.to_csv(os.path.join(output_dir, "startup_exitosa.csv"), index=False)
df_no_exitosa.to_csv(os.path.join(output_dir, "startup_no_exitosa.csv"), index=False)

print("→ CSVs generados:")
print(f"   startup_exitosa.csv  (idx={best_pos['idx']}, p1={best_pos['p1']:.4f})")
print(f"   startup_no_exitosa.csv(idx={best_neg['idx']}, p1={best_neg['p1']:.4f})")
