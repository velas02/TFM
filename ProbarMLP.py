# ProbarMLP.py

import requests
import os

API_PREDICT_URL = "http://localhost:5000/predict_mlp"
API_EXPLAIN_URL = "http://localhost:5000/explain_mlp"
CSV_DIR = "ejemplos_validacion"
files_to_test = [
    ("exitosa",    os.path.join(CSV_DIR, "startup_exitosa.csv")),
    ("no_exitosa", os.path.join(CSV_DIR, "startup_no_exitosa.csv"))
]

def test_csv(name, path):
    print(f"\n=== startup {name} ===")
    print(f"archivo: {path}")

    # llamada a predict_mlp
    with open(path, "rb") as f:
        files = {"file": (os.path.basename(path), f, "text/csv")}
        resp = requests.post(API_PREDICT_URL, files=files)
        resp.raise_for_status()
        result = resp.json()
    print(f"predicción:   {result['prediction']}")
    print(f"probabilidad: {result['probability']:.4f}")

    # llamada a explain_mlp
    with open(path, "rb") as f:
        files = {"file": (os.path.basename(path), f, "text/csv")}
        resp = requests.post(API_EXPLAIN_URL, files=files)
        resp.raise_for_status()
        explanation = resp.json()

    print("\nexplicación SHAP:")
    print(f"  expected_value:        {explanation['expected_value']:.6f}")
    print(f"  shap_sum:              {explanation['shap_sum']:.6f}")
    print(f"  predicted_probability: {explanation['predicted_probability']:.6f}")
    print(f"  real_probability:      {explanation['real_probability']:.6f}")
    print("\ncontribuciones por variable:")
    for feature, value in explanation['shap_values'].items():
        print(f"  {feature}: {value:.6f}")

if __name__ == "__main__":
    for name, path in files_to_test:
        test_csv(name, path)
