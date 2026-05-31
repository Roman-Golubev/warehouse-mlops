import os
import time
import json
import requests

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def main():
    api_base = os.getenv("API_BASE_URL")
    if not api_base:
        raise ValueError("API_BASE_URL env var is required")

    raw_dir = os.getenv("RAW_DATA_DIR")
    if not raw_dir:
        raw_dir = os.path.join(PROJECT_ROOT, "artifacts", "data", "raw")
    
    products_path = os.path.join(raw_dir, "products.csv")
    warehouses_path = os.path.join(raw_dir, "warehouses.csv")
    orders_path = os.path.join(raw_dir, "orders.csv")

    required_files = [products_path, warehouses_path, orders_path]
    missing = [path for path in required_files if not os.path.exists(path)]
    if missing:
        raise FileNotFoundError(f"Missing required input files: {missing}")

    files = {
        "products": open(products_path, "rb"),
        "warehouses": open(warehouses_path, "rb"),
        "orders": open(orders_path, "rb"),
    }

    try:
        resp = requests.post(f"{api_base}/predict", files=files, timeout=300)
        resp.raise_for_status()

        task = resp.json()
        print("TASK_RESPONSE:")
        print(json.dumps(task, indent=2, ensure_ascii=False))

        task_id = task["task_id"]

        for _ in range(20):
            result = requests.get(f"{api_base}/result/{task_id}", timeout=300)
            if result.status_code == 200:
                print("RESULT_RESPONSE:")
                print(json.dumps(result.json(), indent=2, ensure_ascii=False))
                return
            time.sleep(3)

        result.raise_for_status()
    finally:
        for f in files.values():
            f.close()


if __name__ == "__main__":
    main()
