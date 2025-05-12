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

warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
warnings.filterwarnings("ignore", message=".*kagglehub.*version.*")

from StartupPreprocessor import StartupPreprocessor

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
    X_bg     = svm_pipe.named_steps['prep'].transform(X_full)
    explainer = shap.KernelExplainer(
        lambda x: svm_pipe.named_steps['svc'].predict_proba(x),
        X_bg[np.random.RandomState(42).choice(X_bg.shape[0], 100, replace=False)]
    )
    logger.info("background SHAP preparado")

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
    # endpoint: predicción
    # ----------------------------------------------------------------------------
    @app.route('/predict_svm', methods=['POST'])
    def predict_svm():
        try:
            payload = request.get_json(force=True)
            logger.info(f"predict_svm payload: {payload}")
            raw = pd.DataFrame([payload])
            inst = prep.preprocess_instance(raw)
            X_in = svm_pipe.named_steps['prep'].transform(inst)
            prob = float(svm_pipe.named_steps['svc'].predict_proba(X_in)[0, 1])
            label = int(prob >= 0.5)
            return jsonify({"prediction": label, "probability": prob})
        except Exception as e:
            logger.exception("error en predict_svm")
            return jsonify({"error": str(e)}), 400

    # ----------------------------------------------------------------------------
    # endpoint: explicación SHAP
    # ----------------------------------------------------------------------------
    @app.route('/explain_svm', methods=['POST'])
    def explain_svm():
        try:
            payload = request.get_json(force=True)
            logger.info(f"explain_svm payload: {payload}")
            raw = pd.DataFrame([payload])
            inst = prep.preprocess_instance(raw)
            X_in = svm_pipe.named_steps['prep'].transform(inst)
            shap_vals = explainer.shap_values(X_in, nsamples=100)
            vals = shap_vals[1] if isinstance(shap_vals, list) else shap_vals
            flat = vals.reshape(-1)
            feat_names = svm_pipe.named_steps['prep'].get_feature_names_out()
            result = {name: float(val) for name, val in zip(feat_names, flat)}
            return jsonify(result)
        except Exception as e:
            logger.exception("error en explain_svm")
            return jsonify({"error": str(e)}), 400

    return app

# ----------------------------------------------------------------------------
# WSGI entrypoint
# ----------------------------------------------------------------------------
app = create_app()

# Si ejecutas directamente: no usar debug en producción
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
