import os
import pandas as pd
import numpy as np
import kagglehub
from sklearn.preprocessing import StandardScaler

class StartupPreprocessor:
    """
    Clase que descarga, limpia y genera las características finales del dataset
    'startup-success-prediction', dejando el DataFrame listo para entrenamiento.
    """

    def __init__(self, kaggle_dataset: str = "manishkc06/startup-success-prediction"):
        self.kaggle_dataset = kaggle_dataset
        self.scaler = StandardScaler()
        # listas de columnas a eliminar en distintos pasos
        self._initial_drop = [
            'Unnamed: 0', 'Unnamed: 6', 'state_code.1', 'id', 'object_id', 'name'
        ]
        self._derived_drop = [
            'city', 'category_code',
            'founded_at', 'closed_at', 'first_funding_at', 'last_funding_at',
            'milestones', 'has_roundA', 'has_roundB', 'has_roundC', 'has_roundD',
            'funding_total_usd', 'relationships', 'avg_participants'
        ]
        self._extra_drop = [
            'age_first_funding_year', 'age_last_funding_year',
            'age_first_milestone_year', 'age_last_milestone_year',
            'state_code', 'zip_code', 'latitude', 'longitude',
            'has_milestone_info', 'status', 'is_top500'
        ]

    def preprocess(self) -> pd.DataFrame:
        # descargar y leer
        path = kagglehub.dataset_download(self.kaggle_dataset)
        csv_path = os.path.join(path, "startup data.csv")
        df = pd.read_csv(csv_path)

        # eliminar columnas no informativas
        df.drop(columns=[c for c in self._initial_drop if c in df], inplace=True)

        # convertir a datetime
        for c in ['founded_at','closed_at','first_funding_at','last_funding_at']:
            if c in df:
                df[c] = pd.to_datetime(df[c], errors='coerce')

        # asegurar columna status
        if 'status' not in df:
            raw = pd.read_csv(csv_path, usecols=['status'])
            df['status'] = raw['status']

        # crear derivadas temporales
        fecha_corte = pd.to_datetime("2025-01-01")
        df['lifetime_years'] = ((df['closed_at'].fillna(fecha_corte) - df['founded_at']).dt.days/365).round(2)
        df['funding_delay_years'] = ((df['first_funding_at'] - df['founded_at']).dt.days/365).round(2)
        df['last_milestone_delay_years'] = ((df['last_funding_at'] - df['founded_at']).dt.days/365).round(2)
        df['post_funding_duration_years'] = ((df['closed_at'].fillna(fecha_corte) - df['last_funding_at']).dt.days/365).round(2)

        # eliminar inconsistencias negativas
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

        # binarizar sector
        tech = {'software','web','mobile','enterprise'}
        df['main_sector'] = df['category_code'].apply(lambda x: 'tech' if x in tech else 'non_tech')

        # agrupar ciudades
        top = df['city'].value_counts()
        freq = top[top>20].index
        df['city_grouped'] = df['city'].apply(lambda x: x if x in freq else 'other')

        # escalar continuas
        for var in ['funding_total_usd','relationships','avg_participants']:
            if var in df:
                df[f'{var}_scaled'] = self.scaler.fit_transform(df[[var]])

        # booleanas adicionales
        df['has_milestones'] = df['milestones'] > 0
        df['has_late_funding'] = (
            (df.get('has_roundC',0)==1) |
            (df.get('has_roundD',0)==1)
        )

        # eliminar redundantes
        drop_all = (
            self._derived_drop +
            self._extra_drop +
            [c for c in df.columns if c.startswith('is_')]
        )
        df.drop(columns=[c for c in drop_all if c in df], inplace=True)

        return df.reset_index(drop=True)


# ejemplo de uso
if __name__ == "__main__":
    prep = StartupPreprocessor()
    final_df = prep.preprocess()
    print("Columnas finales:", final_df.columns.tolist())
    print("Dimensiones finales:", final_df.shape)
