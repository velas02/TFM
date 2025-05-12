# =============================================================================
# 1. entrenar y exportar pipeline SVM a un pkl
# =============================================================================

import os
import joblib
import kagglehub
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC

# ======================
# 1. descarga y preprocesamiento
# ======================
path = kagglehub.dataset_download("manishkc06/startup-success-prediction")
csv_path = os.path.join(path, "startup data.csv")
df = pd.read_csv(csv_path)

initial_drop = [
    'Unnamed: 0', 'Unnamed: 6', 'state_code.1', 'id', 'object_id', 'name'
]
df.drop(columns=[c for c in initial_drop if c in df.columns], inplace=True)

for c in ['founded_at', 'closed_at', 'first_funding_at', 'last_funding_at']:
    df[c] = pd.to_datetime(df[c], errors='coerce')

if 'status' not in df.columns:
    raw = pd.read_csv(csv_path, usecols=['status'])
    df['status'] = raw['status']

fecha_corte = pd.to_datetime("2025-01-01")
df['lifetime_years'] = ((df['closed_at'].fillna(fecha_corte) - df['founded_at']).dt.days / 365).round(2)
df['funding_delay_years'] = ((df['first_funding_at'] - df['founded_at']).dt.days / 365).round(2)
df['last_milestone_delay_years'] = ((df['last_funding_at'] - df['founded_at']).dt.days / 365).round(2)
df['post_funding_duration_years'] = ((df['closed_at'].fillna(fecha_corte) - df['last_funding_at']).dt.days / 365).round(2)

mask = (
    (df['lifetime_years'] < 0) |
    (df['funding_delay_years'] < 0) |
    (df['last_milestone_delay_years'] < 0) |
    (df['post_funding_duration_years'] < 0) |
    (df.get('age_first_funding_year', 0) < 0) |
    (df.get('age_last_funding_year', 0) < 0) |
    (df.get('age_first_milestone_year', 0) < 0) |
    (df.get('age_last_milestone_year', 0) < 0)
)
df = df.loc[~mask].copy()

tech = {'software', 'web', 'mobile', 'enterprise'}
df['main_sector'] = df['category_code'].apply(lambda x: 'tech' if x in tech else 'non_tech')

top = df['city'].value_counts()
freq = top[top > 20].index
df['city_grouped'] = df['city'].apply(lambda x: x if x in freq else 'other')

scaler = StandardScaler()
for col in ['funding_total_usd', 'relationships', 'avg_participants']:
    if col in df.columns:
        df[f"{col}_scaled"] = scaler.fit_transform(df[[col]])

df['has_milestones'] = df['milestones'] > 0
df['has_late_funding'] = (df.get('has_roundC', 0) == 1) | (df.get('has_roundD', 0) == 1)

derived_drop = [
    'city', 'category_code', 'founded_at', 'closed_at', 'first_funding_at', 'last_funding_at',
    'milestones', 'has_roundA', 'has_roundB', 'has_roundC', 'has_roundD',
    'funding_total_usd', 'relationships', 'avg_participants'
]

extra_drop = [
    'age_first_funding_year', 'age_last_funding_year',
    'age_first_milestone_year', 'age_last_milestone_year',
    'state_code', 'zip_code', 'latitude', 'longitude',
    'has_milestone_info', 'status', 'is_top500'
]

drop_all = derived_drop + extra_drop + [c for c in df.columns if c.startswith('is_')]
df.drop(columns=[c for c in drop_all if c in df.columns], inplace=True)

X = df.drop(columns='labels')
y = df['labels'].astype(int).values

# ======================
# 2. división train/test
# ======================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# ======================
# 3. pipeline SVM
# ======================
cat_cols = X.select_dtypes(['object','bool','category']).columns.tolist()
num_cols = [c for c in X.select_dtypes(['int64','float64']).columns if not c.endswith('_scaled')]

preprocessor = ColumnTransformer([
    ('ohe',    OneHotEncoder(handle_unknown='ignore', sparse_output=False, drop='if_binary'), cat_cols),
    ('scaler', StandardScaler(),                                              num_cols)
], remainder='drop')

pipe_svm = Pipeline([
    ('prep', preprocessor),
    ('svc',  SVC(kernel='rbf', probability=True))
])

# ======================
# 4. grid search
# ======================
param_grid = {'svc__C':[0.1,1,10],'svc__gamma':['scale','auto']}
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
grid = GridSearchCV(pipe_svm, param_grid, cv=cv, scoring='roc_auc', n_jobs=-1, verbose=1)
grid.fit(X_train, y_train)

best_svm = grid.best_estimator_
print("mejores parámetros SVM:", grid.best_params_)

# ======================
# 5. guardar pipeline
# ======================
os.makedirs("models", exist_ok=True)
joblib.dump(best_svm, "models/svm_pipeline.pkl")
print("→ pipeline SVM guardado en models/svm_pipeline.pkl")
