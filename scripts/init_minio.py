import os
import sys
import time
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

# Автоматическая настройка MLflow из переменных окружения
# MLFLOW_TRACKING_URI подхватывается автоматически
# Для S3 устанавливаю явно:
if 'S3_ENDPOINT_URL' in os.environ:
    os.environ['MLFLOW_S3_ENDPOINT_URL'] = os.environ['S3_ENDPOINT_URL']

# Список имён бакетов, которые нужно создать/проверить
BUCKETS = ["raw-data", "processed-data", "models", "reports"]

# Параметры retry
RETRIES = int(os.getenv("INIT_MINIO_RETRIES", "20"))
SLEEP_SECONDS = int(os.getenv("INIT_MINIO_SLEEP", "3"))

def get_s3_client():
    """
    Создаёт и возвращает boto3 S3-клиент с signature_version='s3v4' для надёжной совместимости с MinIO.
    """
    endpoint = os.getenv("S3_ENDPOINT_URL", "http://minio:9000")
    access_key = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")

    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )

def wait_for_minio(s3_client):
    """
    Ждёт доступности MinIO, проверяя list_buckets. При неудаче завершается с ошибкой.
    """
    last_exc = None
    for attempt in range(1, RETRIES + 1):
        try:
            s3_client.list_buckets()
            return True
        except Exception as e:
            last_exc = e
            if attempt == RETRIES:
                break
            time.sleep(SLEEP_SECONDS)
    print(f"MinIO not available after {RETRIES} attempts: {last_exc}", file=sys.stderr)
    return False

def ensure_buckets(s3_client, buckets):
    """
    Создаёт недостающие бакеты, обрабатывает состояние гонки.
    """
    try:
        existing = {b["Name"] for b in s3_client.list_buckets().get("Buckets", [])}
    except Exception as e:
        print(f"Failed to list buckets: {e}", file=sys.stderr)
        raise

    for bucket in buckets:
        if bucket in existing:
            print(f"Bucket already exists: {bucket}")
            continue

        try:
            s3_client.create_bucket(Bucket=bucket)
            print(f"Created bucket: {bucket}")
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            # Игнорирует ошибки, которые означают, что бакет уже создан/принадлежит мне
            if code in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
                print(f"Bucket already created by another process: {bucket}")
            else:
                print(f"Failed to create bucket {bucket}: {e}", file=sys.stderr)
                raise

def main():
    s3 = get_s3_client()

    if not wait_for_minio(s3):
        sys.exit(1)

    ensure_buckets(s3, BUCKETS)

if __name__ == "__main__":
    main()
