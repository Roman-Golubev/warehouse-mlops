import os
import json
from uuid import uuid4

TASK_DIR = "artifacts/tasks"
os.makedirs(TASK_DIR, exist_ok=True)

# Автоматическая настройка MLflow из переменных окружения
# MLFLOW_TRACKING_URI подхватывается автоматически
# Для S3 устанавливаю явно:
if 'S3_ENDPOINT_URL' in os.environ:
    os.environ['MLFLOW_S3_ENDPOINT_URL'] = os.environ['S3_ENDPOINT_URL']


def create_task():
    task_id = str(uuid4())
    path = os.path.join(TASK_DIR, f"{task_id}.json")
    payload = {"task_id": task_id, "status": "created"}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return task_id


def save_task(task_id, data):
    path = os.path.join(TASK_DIR, f"{task_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_task(task_id):
    path = os.path.join(TASK_DIR, f"{task_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
