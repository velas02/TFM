import os
import logging

from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import shap
import numpy as np
import pandas as pd
import warnings
from sklearn.exceptions import InconsistentVersionWarning

from StartupPreprocessor import StartupPreprocessor

warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
warnings.filterwarnings("ignore", message=".*kagglehub.*version.*")


def create_app():
    # ----------------------------------------------------------------------------
    # configuración de logging
    # ----------------------------------------------------------------------------
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")
    logger = logging.getLogger(__name__)

    # ----------------------------------------------------------------------------
    # instancia de Flask y CORS
    # ----------------------------------------------------------------------------
    app = Flask(__name__)
    CORS(app)

    # ----------------------------------------------------------------------------
    # cargar preprocesador y modelo entrenado
    # ----------------------------------------------------------------------------
    logger.info("inicializando StartupPreprocessor y cargando pipeline SVM")
    prep     = StartupPreprocessor()
    svm_pipe = joblib.load("models/svm_pipeline.pkl")

    # ----------------------------------------------------------------------------
    # preparar background para SHAP
    # ----------------------------------------------------------------------------
    df_full = prep.preprocess()
    X_full  = df_full.drop(columns="labels")
    X_bg    = svm_pipe.named_steps['prep'].transform(X_full)

    # nombres de las columnas transformadas
    feature_names = svm_pipe.named_steps['prep'].get_feature_names_out()

    # explainer en escala de probabilidad (clase 1)
    explainer = shap.KernelExplainer(
        lambda x: svm_pipe.named_steps['svc'].predict_proba(x)[:, 1],
        X_bg[np.random.RandomState(42)
             .choice(X_bg.shape[0], 100, replace=False)],
        link="identity",
        feature_names=feature_names
    )
    logger.info("background SHAP preparado")

    # ----------------------------------------------------------------------------
    # cargar pipeline y explainer para MLP
    # ----------------------------------------------------------------------------
    logger.info("cargando pipeline MLP")
    mlp_pipe = joblib.load("models/mlp_pipeline.pkl")

    # reutilizamos X_bg para building SHAP background
    # (mismo preprocesador que con SVM)
    logger.info("preparando background SHAP para MLP")
    explainer_mlp = shap.KernelExplainer(
        lambda x: mlp_pipe.named_steps['mlp'].predict_proba(x)[:, 1],
        X_bg[np.random.RandomState(42)
             .choice(X_bg.shape[0], 100, replace=False)],
        link="identity",
        feature_names=feature_names
    )
    logger.info("background SHAP MLP preparado")

    # ----------------------------------------------------------------------------
    # manejadores de error globales
    # ----------------------------------------------------------------------------
    @app.errorhandler(400)
    def bad_request(err):
        return jsonify({"error": "bad request", "message": str(err)}), 400

    @app.errorhandler(500)
    def internal_error(err):
        return jsonify({"error": "internal server error", "message": str(err)}), 500

    # ----------------------------------------------------------------------------
    # endpoint: predicción desde archivo CSV
    # ----------------------------------------------------------------------------
    @app.route('/predict_svm', methods=['POST'])
    def predict_svm():
        try:
            # comprobar fichero
            if 'file' not in request.files:
                return jsonify({"error": "no se proporcionó archivo CSV"}), 400
            file = request.files['file']
            # leer CSV (una sola fila)
            df_raw = pd.read_csv(file)

            print(df_raw['name'])

            # preprocesar
            inst = prep.preprocess_instance(df_raw)
            # transformar y predecir
            X_in = svm_pipe.named_steps['prep'].transform(inst)
            prob = float(svm_pipe.named_steps['svc'].predict_proba(X_in)[0, 1])
            label = int(prob >= 0.5)
            return jsonify({"prediction": label, "probability": prob})
        except Exception as e:
            logger.exception("error en predict_svm")
            return jsonify({"error": str(e)}), 400

    # ----------------------------------------------------------------------------
    # endpoint: explicación SHAP desde archivo CSV
    # ----------------------------------------------------------------------------
    @app.route('/explain_svm', methods=['POST'])
    def explain_svm():
        try:
            # validación de fichero
            if 'file' not in request.files:
                return jsonify({"error": "no se proporcionó archivo CSV"}), 400

            # lectura y preprocesado de la instancia
            file     = request.files['file']
            df_raw   = pd.read_csv(file)
            inst     = prep.preprocess_instance(df_raw)
            X_in     = svm_pipe.named_steps['prep'].transform(inst)

            # cálculo de SHAP
            shap_vals   = explainer.shap_values(X_in, nsamples=200)
            shap_class1 = shap_vals  
            flat        = shap_class1.reshape(-1)

            # reconstrucción de la predicción a partir de SHAP
            expected = (explainer.expected_value[1]
                        if isinstance(explainer.expected_value, (list, np.ndarray))
                        else explainer.expected_value)
            shap_sum  = float(flat.sum())
            pred_shap = expected + shap_sum
            real_prob = float(svm_pipe.named_steps['svc'].predict_proba(X_in)[0, 1])

            # diccionario de contribuciones por feature
            shap_dict = {name: float(val)
                         for name, val in zip(feature_names, flat)}

            # respuesta completa
            return jsonify({
                "expected_value":       expected,
                "shap_sum":             shap_sum,
                "predicted_probability": pred_shap,
                "real_probability":     real_prob,
                "shap_values":          shap_dict
            })
        except Exception as e:
            logger.exception("error en explain_svm")
            return jsonify({"error": str(e)}), 400
        

    # ----------------------------------------------------------------------------
    # endpoint: predicción MLP desde archivo CSV
    # ----------------------------------------------------------------------------
    @app.route('/predict_mlp', methods=['POST'])
    def predict_mlp():
        try:
            if 'file' not in request.files:
                return jsonify({"error": "no se proporcionó archivo CSV"}), 400
            df_raw = pd.read_csv(request.files['file'])
            inst   = prep.preprocess_instance(df_raw)
            X_in   = mlp_pipe.named_steps['prep'].transform(inst)
            prob   = float(mlp_pipe.named_steps['mlp'].predict_proba(X_in)[0, 1])
            label  = int(prob >= 0.5)
            return jsonify({"prediction": label, "probability": prob})
        except Exception as e:
            logger.exception("error en predict_mlp")
            return jsonify({"error": str(e)}), 400

    # ----------------------------------------------------------------------------
    # endpoint: explicación SHAP MLP desde archivo CSV
    # ----------------------------------------------------------------------------
    @app.route('/explain_mlp', methods=['POST'])
    def explain_mlp():
        try:
            if 'file' not in request.files:
                return jsonify({"error": "no se proporcionó archivo CSV"}), 400
            df_raw = pd.read_csv(request.files['file'])
            inst   = prep.preprocess_instance(df_raw)
            X_in   = mlp_pipe.named_steps['prep'].transform(inst)

            shap_vals   = explainer_mlp.shap_values(X_in, nsamples=200)
            flat        = np.array(shap_vals).reshape(-1)

            expected    = explainer_mlp.expected_value
            shap_sum    = float(flat.sum())
            pred_shap   = expected + shap_sum
            real_prob   = float(mlp_pipe.named_steps['mlp'].predict_proba(X_in)[0, 1])
            shap_dict   = {name: float(val) for name, val in zip(feature_names, flat)}

            return jsonify({
                "expected_value":        expected,
                "shap_sum":              shap_sum,
                "predicted_probability": pred_shap,
                "real_probability":      real_prob,
                "shap_values":           shap_dict
            })
        except Exception as e:
            logger.exception("error en explain_mlp")
            return jsonify({"error": str(e)}), 400

    return app


# ----------------------------------------------------------------------------
# WSGI entrypoint
# ----------------------------------------------------------------------------
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
