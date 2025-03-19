# Análisis de Factores de Riesgo en la Inversión en Startups Tecnológicas

Este repositorio contiene el código y documentación relacionados con el Trabajo de Fin de Máster titulado **"Análisis de Factores de Riesgo en la Inversión en Startups Tecnológicas"**. El objetivo principal del proyecto es desarrollar un sistema de software con una interfaz de usuario y un backend que implemente uno o varios modelos de aprendizaje automático explicables, sin uso de deep learning. 

## Estructura del repositorio

El desarrollo del proyecto se organiza en cuatro ramas principales:

### 1. `main`
La rama principal del repositorio. Contiene el código estable e integrado de la interfaz de usuario, el backend y el modelo de aprendizaje automático. Esta rama solo recibe cambios tras la validación de las implementaciones en ramas secundarias.

### 2. `C#`
Rama dedicada al desarrollo de la interfaz de usuario en **.NET Framework con C#**. Aquí se desarrollarán las funcionalidades de visualización de datos y la interacción con el backend.

### 3. `Machine-Learning-Models`
Rama enfocada en el desarrollo del modelo o modelos de **Machine Learning explicables** utilizando **Scikit-learn**. En esta rama se implementarán las técnicas de explicabilidad como **LIME** y **SHAP**, así como el preprocesamiento de datos y la validación del modelo.

### 4. `Flask`
Rama dedicada al desarrollo del backend en **Flask con Python**. Aquí se manejarán las API necesarias para la comunicación entre la interfaz de usuario y el modelo de aprendizaje automático.

## Tecnologías utilizadas

- **Backend:** Flask con Python
- **Frontend:** .NET Framework con C#
- **Machine Learning:** Scikit-learn
- **Explicabilidad:** LIME, SHAP
- **Fuente de datos:** Kaggle

## Contribuciones

Cada rama debe seguir un flujo de trabajo basado en *feature branches*, es decir, cada funcionalidad nueva se desarrolla en una rama separada y luego se fusiona en su respectiva rama principal (`C#`, `Machine-Learning-Models` o `Flask`) antes de integrarse en `main`.

Las contribuciones deberán seguir el siguiente flujo:
1. Crear una nueva rama a partir de `C#`, `Machine-Learning-Models` o `Flask` según corresponda.
2. Desarrollar la funcionalidad.
3. Realizar pruebas y documentación.
4. Enviar un *pull request* para revisión.
5. Una vez aprobada, fusionar la rama en la correspondiente (`C#`, `Machine-Learning-Models` o `Flask`).
6. Periódicamente, estas ramas se integrarán en `main` tras validación final.

## Contacto
Para cualquier duda o sugerencia, puedes contactar a través del correo **David_Velasco@usal.es**.
