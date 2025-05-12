import os
import pandas as pd
import numpy as np
import kagglehub
from sklearn.preprocessing import StandardScaler

class StartupPreprocessor:
    def __init__(self):
        # descarga dataset una sola vez
        path         = kagglehub.dataset_download("manishkc06/startup-success-prediction")
        self.csv_path = os.path.join(path, "startup data.csv")
        self._df      = pd.read_csv(self.csv_path)

        # listas de columnas a eliminar
        self._initial_drop = [
            'Unnamed: 0', 'Unnamed: 6',
            'state_code.1', 'id',
            'object_id', 'name'
        ]
        self._derived_drop = [
            'city', 'category_code', 'founded_at',
            'closed_at', 'first_funding_at',
            'last_funding_at', 'milestones',
            'has_roundA', 'has_roundB',
            'has_roundC', 'has_roundD',
            'funding_total_usd', 'relationships',
            'avg_participants'
        ]
        self._extra_drop = [
            'age_first_funding_year','age_last_funding_year',
            'age_first_milestone_year','age_last_milestone_year',
            'state_code','zip_code','latitude','longitude',
            'has_milestone_info','status','is_top500'
        ]

        # scaler para uso posterior
        self._scaler = StandardScaler()

        # columnas numéricas a escalar
        self._num_cols = ['funding_total_usd', 'relationships', 'avg_participants']

        # ajustar el scaler sobre las tres columnas juntas
        df_clean = self._domain_clean(self._df.copy())
        cols_existentes = [c for c in self._num_cols if c in df_clean.columns]
        if cols_existentes:
            self._scaler.fit(df_clean[cols_existentes])

    def _domain_clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """limpieza de dominio: fechas, variables derivadas y categorizaciones"""
        df = df.copy()

        # 1. limpieza inicial
        df.drop(columns=[c for c in self._initial_drop if c in df], inplace=True)

        # 2. conversión de fechas
        for c in ['founded_at','closed_at','first_funding_at','last_funding_at']:
            df[c] = pd.to_datetime(df[c], errors='coerce')

        # 3. asegurar 'status'
        if 'status' not in df:
            raw = pd.read_csv(self.csv_path, usecols=['status'])
            df['status'] = raw['status']

        # 4. variables temporales derivadas
        fecha_corte = pd.to_datetime("2025-01-01")
        df['lifetime_years']             = ((df['closed_at'].fillna(fecha_corte) - df['founded_at'])
                                            .dt.days / 365).round(2)
        df['funding_delay_years']        = ((df['first_funding_at'] - df['founded_at'])
                                            .dt.days / 365).round(2)
        df['last_milestone_delay_years'] = ((df['last_funding_at'] - df['founded_at'])
                                            .dt.days / 365).round(2)
        df['post_funding_duration_years']= ((df['closed_at'].fillna(fecha_corte) - df['last_funding_at'])
                                            .dt.days / 365).round(2)

        # 5. filtrar inconsistentes
        mask = (
            (df['lifetime_years'] < 0) |
            (df['funding_delay_years'] < 0) |
            (df['last_milestone_delay_years'] < 0) |
            (df['post_funding_duration_years'] < 0)
        )
        df = df.loc[~mask].copy()

        # 6. clasificación sector tecnológico
        tech = {'software','web','mobile','enterprise'}
        df['main_sector'] = df['category_code'].apply(
            lambda x: 'tech' if x in tech else 'non_tech'
        )

        # 7. agrupación de ciudades
        top  = df['city'].value_counts()
        freq = top[top > 20].index
        df['city_grouped'] = df['city'].apply(
            lambda x: x if x in freq else 'other'
        )

        return df

    def preprocess(self) -> pd.DataFrame:
        """aplica limpieza de dominio + escalado + booleanas + elimina redundantes"""
        df = self._domain_clean(self._df.copy())

        # 8. escalado de variables numéricas
        cols_existentes = [c for c in self._num_cols if c in df.columns]
        if cols_existentes:
            scaled = self._scaler.transform(df[cols_existentes])
            for i, c in enumerate(cols_existentes):
                df[f"{c}_scaled"] = scaled[:, i]

        # 9. variables booleanas derivadas
        df['has_milestones']   = df['milestones'] > 0
        df['has_late_funding'] = ((df.get('has_roundC', 0) == 1) |
                                  (df.get('has_roundD', 0) == 1))

        # 10. eliminación de columnas redundantes
        drop_all = self._derived_drop + self._extra_drop + [
            c for c in df.columns if c.startswith('is_')
        ]
        df.drop(columns=[c for c in drop_all if c in df], inplace=True, errors='ignore')

        return df

    def preprocess_instance(self, df: pd.DataFrame) -> pd.DataFrame:
        """preprocesa una única fila para inferencia"""
        df = self._domain_clean(df.copy())

        # escalado
        cols_existentes = [c for c in self._num_cols if c in df.columns]
        if cols_existentes:
            scaled = self._scaler.transform(df[cols_existentes])
            for i, c in enumerate(cols_existentes):
                df[f"{c}_scaled"] = scaled[:, i]

        # booleanas
        df['has_milestones']   = df['milestones'] > 0
        df['has_late_funding'] = ((df.get('has_roundC', 0) == 1) |
                                  (df.get('has_roundD', 0) == 1))

        # eliminar redundantes
        drop_all = self._derived_drop + self._extra_drop + [
            c for c in df.columns if c.startswith('is_')
        ]
        df.drop(columns=[c for c in drop_all if c in df], inplace=True, errors='ignore')

        return df.reset_index(drop=True)
