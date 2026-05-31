import os
import json
import shutil

MODELS_DIR = "artifacts/models"
METRICS_DIR = "artifacts/metrics"

# Автоматическая настройка MLflow из переменных окружения
# MLFLOW_TRACKING_URI подхватывается автоматически
# Для S3 устанавливаю явно:
if 'S3_ENDPOINT_URL' in os.environ:
    os.environ['MLFLOW_S3_ENDPOINT_URL'] = os.environ['S3_ENDPOINT_URL']

def load_json(path, default=None):
    """
    Безопасная загрузка JSON
    """
    if not os.path.exists(path):
        return default if default is not None else {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_and_promote():
    # Загрузка метрик кандидата
    candidate_metrics = load_json(os.path.join(METRICS_DIR, "candidate_metrics.json"), {})
    # Загрузка метрики текущей production-модели
    production_metrics = load_json(os.path.join(METRICS_DIR, "production_metrics.json"), None)
    # Загрузка JSON с информацией о текущей production-модели
    current_prod = load_json(os.path.join(MODELS_DIR, "current_prod_model.json"), None)

    candidate_path = os.path.join(MODELS_DIR, "model_candidate.pkl")

    # Условие первого деплоя
    if current_prod is None or production_metrics is None:
        blue_path = os.path.join(MODELS_DIR, "model_blue.pkl")
        # передача в первичный продакшн - в слот blue
        shutil.copyfile(candidate_path, blue_path)
        # мета-информация о текущей продакшн-модели
        current = {
            "active_color": "blue",
            "model_path": blue_path,
            "version": "initial"
        }
        with open(os.path.join(MODELS_DIR, "current_prod_model.json"), "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2)
        with open(os.path.join(METRICS_DIR, "production_metrics.json"), "w", encoding="utf-8") as f:
            json.dump(candidate_metrics, f, indent=2)
        return {"promoted": True, "reason": "initial_model"}

    current_color = current_prod.get("active_color", "blue") # по умолчанию "blue" - ключа нет
    # следующий (неактивный) слот
    next_color = "green" if current_color == "blue" else "blue"
    # куда будет скопирован кандидат
    next_model_path = os.path.join(MODELS_DIR, f"model_{next_color}.pkl")

    mae_ok = candidate_metrics["mae"] <= production_metrics["mae"] * 1.03
    rmse_ok = candidate_metrics["rmse"] <= production_metrics["rmse"] * 1.03
    r2_ok = candidate_metrics["r2"] >= production_metrics["r2"] - 0.02

    # Promotion для подходящего кандидата
    if mae_ok and rmse_ok and r2_ok:
        shutil.copyfile(candidate_path, next_model_path)
        new_prod = {
            "active_color": next_color,
            "model_path": next_model_path,
            "version": "promoted_candidate"
        }
        with open(os.path.join(MODELS_DIR, "current_prod_model.json"), "w", encoding="utf-8") as f:
            json.dump(new_prod, f, indent=2)
        with open(os.path.join(METRICS_DIR, "production_metrics.json"), "w", encoding="utf-8") as f:
            json.dump(candidate_metrics, f, indent=2)
        return {"promoted": True, "reason": "better_or_equal_model"}
    else:
        return {"promoted": False, "reason": "candidate_failed_policy"}
