import os
import boto3
from botocore.client import Config

# Автоматическая настройка MLflow из переменных окружения
# MLFLOW_TRACKING_URI подхватывается автоматически
# Для S3 устанавливаю явно:
if 'S3_ENDPOINT_URL' in os.environ:
    os.environ['MLFLOW_S3_ENDPOINT_URL'] = os.environ['S3_ENDPOINT_URL']

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

def upload_file(local_path: str, bucket_name: str, object_name: str):
    """
    Загружает локальный файл в бакет.
    """
    s3 = get_s3_client()
    s3.upload_file(local_path, bucket_name, object_name)


def download_file(bucket_name: str, object_name: str, local_path: str):
    """
    Скачивает объект из бакета в локальную файловую систему.
    """
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    s3 = get_s3_client()
    s3.download_file(bucket_name, object_name, local_path)
