from datetime import datetime, timedelta, timezone
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "mlops",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=3),
}

with DAG(
    dag_id="warehouse_retrain_pipeline",
    default_args=default_args,
    description="Automated retraining pipeline for warehouse demand forecasting",
    start_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
    schedule="@daily",
    catchup=False,
    tags=["mlops", "retraining", "warehouse"],
) as dag:

    data_pipeline = BashOperator(
        task_id="data_pipeline",
        bash_command="cd /opt/project && python pipeline/data_pipeline.py",
        append_env=True,  # Наследует все env-переменные контейнера
        env={
            "PYTHONPATH": "/opt/project",
        },
    )

    model_training = BashOperator(
        task_id="model_training",
        bash_command="cd /opt/project && python pipeline/train.py",
        append_env=True,
        env={
            "PYTHONPATH": "/opt/project",
        },
    )

    model_drift = BashOperator(
        task_id="model_drift",
        bash_command="cd /opt/project && python pipeline/drift.py",
        append_env=True,
        env={
            "PYTHONPATH": "/opt/project",
        },
    )

    model_validation = BashOperator(
        task_id="model_validation",
        bash_command="cd /opt/project && python pipeline/validate.py",
        append_env=True,
        env={
            "PYTHONPATH": "/opt/project",
        },
    )

    data_pipeline >> model_training >> model_drift >> model_validation
