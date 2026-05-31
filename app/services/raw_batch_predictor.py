import os
import time
import shutil
import pandas as pd

from pipeline.data_pipeline import data_extraction, data_validation, data_preparation
from app.services.model_service import ModelService
from app.core.metrics import (
    prediction_requests_total,
    prediction_request_errors_total,
    prediction_batch_files_total,
    prediction_latency_seconds,
    incident_events_total,
)

# Автоматическая настройка MLflow из переменных окружения
# MLFLOW_TRACKING_URI подхватывается автоматически
# Для S3 устанавливаю явно:
if 'S3_ENDPOINT_URL' in os.environ:
    os.environ['MLFLOW_S3_ENDPOINT_URL'] = os.environ['S3_ENDPOINT_URL']


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def run_prediction_from_raw_files(task_id: str, products_file, warehouses_file, orders_file):
    start = time.time()
    prediction_requests_total.inc()

    batch_dir = os.path.join("artifacts", "incoming_batches", task_id)
    ensure_dir(batch_dir)

    products_path = os.path.join(batch_dir, "products.csv")
    warehouses_path = os.path.join(batch_dir, "warehouses.csv")
    orders_path = os.path.join(batch_dir, "orders.csv")

    with open(products_path, "wb") as f:
        shutil.copyfileobj(products_file.file, f)
    with open(warehouses_path, "wb") as f:
        shutil.copyfileobj(warehouses_file.file, f)
    with open(orders_path, "wb") as f:
        shutil.copyfileobj(orders_file.file, f)

    prediction_batch_files_total.inc(3)

    try:
        with prediction_latency_seconds.time():
            products, warehouses, orders = data_extraction(batch_dir)
            validation = data_validation(products, warehouses, orders)

            if not validation["is_valid"]:
                prediction_request_errors_total.inc()
                incident_events_total.labels(incident_type="validation_error").inc()
                return {
                    "status": "failed",
                    "predictions": None,
                    "details": {"errors": validation["errors"]}
                }

            X_train, X_test, y_train, y_test, full_df = data_preparation(products, warehouses, orders)

            infer_df = X_test.tail(20).copy()
            if infer_df.empty:
                prediction_request_errors_total.inc()
                incident_events_total.labels(incident_type="empty_features").inc()
                return {
                    "status": "failed",
                    "predictions": None,
                    "details": {"errors": ["No inference rows produced after preparation"]}
                }

            model_service = ModelService()
            model, info = model_service.load_model()
            preds = model.predict(infer_df)

            return {
                "status": "completed",
                "predictions": [float(x) for x in preds.tolist()],
                "model_color": info["active_color"],
                "details": {
                    "rows_used_for_prediction": len(infer_df),
                    "elapsed_seconds": round(time.time() - start, 3)
                }
            }

    except Exception as e:
        prediction_request_errors_total.inc()
        incident_events_total.labels(incident_type="runtime_error").inc()
        return {
            "status": "failed",
            "predictions": None,
            "details": {"errors": [str(e)]}
        }
