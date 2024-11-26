import os
import pickle

# Ruta al modelo guardado
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "informe_analysis_model.pkl")

# Cargar el modelo
with open(MODEL_PATH, "rb") as model_file:
    model = pickle.load(model_file)

def analyze_informe(description):
    """
    Analiza la descripción de un informe y devuelve un diagnóstico.
    """
    prediction = model.predict([description])
    return prediction[0]
