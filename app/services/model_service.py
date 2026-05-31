import os
import json
import joblib

# Автоматическая настройка MLflow из переменных окружения
# MLFLOW_TRACKING_URI подхватывается автоматически
# Для S3 устанавливаю явно:
if 'S3_ENDPOINT_URL' in os.environ:
    os.environ['MLFLOW_S3_ENDPOINT_URL'] = os.environ['S3_ENDPOINT_URL']

class ModelService:
    def __init__(self):
        self.current_prod_path = "artifacts/models/current_prod_model.json"

    def get_active_info(self):
        if not os.path.exists(self.current_prod_path):
            return {
                "active_color": "blue",
                "model_path": "artifacts/models/model_blue.pkl",
                "version": "initial"
            }
        with open(self.current_prod_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_model(self):
        info = self.get_active_info()
        model_path = info["model_path"]
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Active model not found: {model_path}")
        model = joblib.load(model_path)
        return model, info
