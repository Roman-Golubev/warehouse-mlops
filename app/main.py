from fastapi import FastAPI, UploadFile, File
from app.models.schemas import TaskResponse, ResultResponse
from app.services.task_store import create_task, save_task, load_task
from app.services.raw_batch_predictor import run_prediction_from_raw_files
from app.core.metrics import metrics_response

app = FastAPI(title="Warehouse Demand Forecast API")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/metrics")
async def metrics():
    return metrics_response()


@app.post("/predict", response_model=TaskResponse)
async def predict(
    products: UploadFile = File(...),
    warehouses: UploadFile = File(...),
    orders: UploadFile = File(...)
):
    task_id = create_task()

    result = run_prediction_from_raw_files(
        task_id=task_id,
        products_file=products,
        warehouses_file=warehouses,
        orders_file=orders
    )

    save_task(task_id, {
        "task_id": task_id,
        **result
    })

    return TaskResponse(
        task_id=task_id,
        status=result["status"],
        message="Batch raw CSV files processed"
    )


@app.get("/result/{task_id}", response_model=ResultResponse)
async def get_result(task_id: str):
    result = load_task(task_id)
    if result is None:
        return ResultResponse(task_id=task_id, status="not_found")
    return ResultResponse(**result)
