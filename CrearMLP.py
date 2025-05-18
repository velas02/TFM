# CrearMLP.py

import os
import pandas as pd
import numpy as np
import kagglehub
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.neural_network import MLPClassifier
import joblib

# 1. descarga y carga del dataset original
path     = kagglehub.dataset_download("manishkc06/startup-success-prediction")
csv_path = os.path.join(path, "startup data.csv")
df       = pd.read_csv(csv_path)

# 2. limpieza inicial de columnas irrelevantes
initial_drop = [
    'Unnamed: 0', 'Unnamed: 6', 'state_code.1',
    'id', 'object_id', 'name'
]
df.drop(columns=[c for c in initial_drop if c in df.columns], inplace=True)

# 3. conversión de columnas de fecha
for c in ['founded_at', 'closed_at', 'first_funding_at', 'last_funding_at']:
    df[c] = pd.to_datetime(df[c], errors='coerce')

# 4. asegurar existencia de la columna 'labels'
if 'labels' not in df.columns:
    raw = pd.read_csv(csv_path, usecols=['labels'])
    df['labels'] = raw['labels']

# 5. creación de variables temporales derivadas
fecha_corte = pd.to_datetime("2025-01-01")
df['lifetime_years']             = ((df['closed_at'].fillna(fecha_corte) - df['founded_at']).dt.days / 365).round(2)
df['funding_delay_years']        = ((df['first_funding_at'] - df['founded_at']).dt.days / 365).round(2)
df['last_milestone_delay_years'] = ((df['last_funding_at'] - df['founded_at']).dt.days / 365).round(2)
df['post_funding_duration_years']= ((df['closed_at'].fillna(fecha_corte) - df['last_funding_at']).dt.days / 365).round(2)

# 6. eliminación de observaciones con errores temporales
mask = (
    (df['lifetime_years'] < 0) |
    (df['funding_delay_years'] < 0) |
    (df['last_milestone_delay_years'] < 0) |
    (df['post_funding_duration_years'] < 0)
)
df = df.loc[~mask].copy()

# 7. clasificación sector y agrupación de ciudades
tech = {'software', 'web', 'mobile', 'enterprise'}
df['main_sector']  = df['category_code'].apply(lambda x: 'tech' if x in tech else 'non_tech')
top_cities         = df['city'].value_counts()
freq               = top_cities[top_cities > 20].index
df['city_grouped'] = df['city'].apply(lambda x: x if x in freq else 'other')

# 8. variables booleanas derivadas
df['has_milestones']   = df['milestones'] > 0
df['has_late_funding'] = (df.get('has_roundC', 0) == 1) | (df.get('has_roundD', 0) == 1)

# 9. eliminación de columnas redundantes
derived_drop = [
    'city', 'category_code', 'founded_at', 'closed_at',
    'first_funding_at', 'last_funding_at', 'milestones',
    'has_roundA', 'has_roundB', 'has_roundC', 'has_roundD'
]
extra_drop = [
    'age_first_funding_year', 'age_last_funding_year',
    'age_first_milestone_year', 'age_last_milestone_year',
    'state_code', 'zip_code', 'latitude', 'longitude',
    'has_milestone_info', 'status', 'is_top500'
]
drop_all = derived_drop + extra_drop + [c for c in df.columns if c.startswith('is_')]
df.drop(columns=[c for c in drop_all if c in df.columns], inplace=True)

# 10. separación de variable objetivo
X = df.drop(columns='labels')
y = df['labels'].astype(int).values

# 11. división en train/test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# 12. detección de columnas para pipeline
cat_cols = ['main_sector', 'city_grouped', 'has_milestones', 'has_late_funding']
num_cols = [
    'funding_rounds', 'has_VC', 'has_angel',
    'lifetime_years', 'funding_delay_years',
    'last_milestone_delay_years', 'post_funding_duration_years',
    'funding_total_usd', 'relationships', 'avg_participants'
]

# 13. preprocesamiento: one-hot y escalado
preprocessor = ColumnTransformer([
    ('ohe',    OneHotEncoder(handle_unknown='ignore', sparse_output=False, drop='if_binary'), cat_cols),
    ('scaler', StandardScaler(), num_cols)
], remainder='drop')

# 14. pipeline completo con MLPClassifier
pipe = Pipeline([
    ('prep', preprocessor),
    ('mlp',  MLPClassifier(random_state=42, max_iter=500))
])

# 15. grid search con validación cruzada
param_grid = {
    'mlp__hidden_layer_sizes': [(50,), (100,), (50, 50)],
    'mlp__activation': ['relu', 'tanh'],
    'mlp__alpha': [1e-4, 1e-3],
    'mlp__learning_rate_init': [1e-3, 1e-2]
}
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
grid = GridSearchCV(
    estimator=pipe,
    param_grid=param_grid,
    cv=cv,
    scoring='roc_auc',
    n_jobs=-1,
    verbose=1
)

# 16. ajuste del modelo
grid.fit(X_train, y_train)
print("mejores parámetros:", grid.best_params_)
best_model = grid.best_estimator_

# 17. guardar pipeline entrenado
os.makedirs('models', exist_ok=True)
joblib.dump(best_model, 'models/mlp_pipeline.pkl')
print("pipeline mlp entrenado guardado en models/mlp_pipeline.pkl")
