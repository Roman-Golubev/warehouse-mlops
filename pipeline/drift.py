import os
import json
import datetime
import pandas as pd

from evidently import Report
from evidently.presets import DataDriftPreset, DataQualityPreset

ARTIFACTS_DIR = "artifacts"
REPORTS_DIR = os.path.join(ARTIFACTS_DIR, "reports")

# Автоматическая настройка MLflow из переменных окружения
# MLFLOW_TRACKING_URI подхватывается автоматически
# Для S3 устанавливаю явно:
if 'S3_ENDPOINT_URL' in os.environ:
    os.environ['MLFLOW_S3_ENDPOINT_URL'] = os.environ['S3_ENDPOINT_URL']

def run_drift():
    """
    Проверка выполняется в сравнении с референсным датасетом.
    Проверяется дрифт по признакам и качество данных.
    """
    os.makedirs(REPORTS_DIR, exist_ok=True)

    reference_path = "artifacts/data/reference/reference.csv"
    current_path = "artifacts/data/processed/test.csv"

    if not os.path.exists(reference_path) or not os.path.exists(current_path):
        raise FileNotFoundError("reference or current data not found for drift report")

    reference = pd.read_csv(reference_path)
    current = pd.read_csv(current_path)

    common_cols = [c for c in reference.columns if c in current.columns]
    reference = reference[common_cols].copy()
    current = current[common_cols].copy()

    drift_report = Report(
        metrics=[
            DataDriftPreset(),
            DataQualityPreset(),
        ]
    )

    drift_report.run(reference_data=reference, current_data=current)

    # Сохранение отчёта
    report_dict = drift_report.dict()
    result = {
        "timestamp": datetime.datetime.now().isoformat(),
        "report": report_dict
    }

    out_path = os.path.join(REPORTS_DIR, "drift_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(json.dumps({"saved_to": out_path}, indent=2))
    return result


if __name__ == "__main__":
    # логируемый результат, добавлял для локального тестирования
    print(run_drift())
