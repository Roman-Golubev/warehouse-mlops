import os
import json
import joblib
import mlflow
import mlflow.sklearn
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

PROCESSED_DIR = "artifacts/data/processed"
MODELS_DIR = "artifacts/models"
METRICS_DIR = "artifacts/metrics"

# Автоматическая настройка MLflow из переменных окружения
# MLFLOW_TRACKING_URI подхватывается автоматически
# Для S3 устанавливаю явно:
if 'S3_ENDPOINT_URL' in os.environ:
    os.environ['MLFLOW_S3_ENDPOINT_URL'] = os.environ['S3_ENDPOINT_URL']

def train_model():
    """
    Обучение модели
    """
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(METRICS_DIR, exist_ok=True)

    train_df = pd.read_csv(os.path.join(PROCESSED_DIR, "train.csv"))
    test_df = pd.read_csv(os.path.join(PROCESSED_DIR, "test.csv"))

    target_col = "target_demand_next_7d"

    X_train = train_df.drop(columns=[target_col])
    y_train = train_df[target_col]

    X_test = test_df.drop(columns=[target_col])
    y_test = test_df[target_col]

    categorical_cols = X_train.select_dtypes(include=["object"]).columns.tolist()
    numeric_cols = [c for c in X_train.columns if c not in categorical_cols]

    # Подготовка данных
    # дополнительно выполняется заполнение пропусков,
    # если что-то было пропущено при предобработке
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline([
                    ("imputer", SimpleImputer(strategy="median"))
                ]),
                numeric_cols
            ),
            (
                "cat",
                Pipeline([
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    ("encoder", OneHotEncoder(handle_unknown="ignore"))
                ]),
                categorical_cols
            )
        ]
    )

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=12,
        random_state=42,
        n_jobs=-1
    )

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", model)
    ])

    # эксперимент логируемый в MLflow
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment("warehouse-demand-forecast")

    with mlflow.start_run():
        pipeline.fit(X_train, y_train)
        preds = pipeline.predict(X_test)

        mae = mean_absolute_error(y_test, preds)
        rmse = mean_squared_error(y_test, preds) ** 0.5
        r2 = r2_score(y_test, preds)

        # Сохранение параметров модели и метрики в MLflow
        mlflow.log_param("model_type", "RandomForestRegressor")
        mlflow.log_param("n_estimators", 200)
        mlflow.log_param("max_depth", 12)
        mlflow.log_metric("mae", mae)
        mlflow.log_metric("rmse", rmse)
        mlflow.log_metric("r2", r2)
        mlflow.sklearn.log_model(pipeline, artifact_path="model")

    # Локальное сохранение модели
    joblib.dump(pipeline, os.path.join(MODELS_DIR, "model_candidate.pkl"))

    # Запись метрик в файл
    metrics = {"mae": mae, "rmse": rmse, "r2": r2}
    with open(os.path.join(METRICS_DIR, "candidate_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    return metrics


if __name__ == "__main__":
    # логируемый результат, добавлял для локального тестирования
    print(train_model())
