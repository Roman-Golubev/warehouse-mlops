import os
import json
import datetime
from datetime import datetime as dt, timedelta
import numpy as np
import pandas as pd


def ensure_dir(path: str):
    """
    Функция создаёт отсутствующие папки
    """
    os.makedirs(path, exist_ok=True)


def generate_synthetic_data(
    data_dir,
    n_products=70,
    n_warehouses=5,
    n_days=180,
    random_state=42
):
    """
    Генерация данных
    """
    rng = np.random.default_rng(random_state)
    ensure_dir(data_dir)

    categories = ["electronics", "food", "household", "clothing", "sports"]
    product_rows = []
    for product_id in range(1, n_products + 1):
        category = rng.choice(categories)
        base_price = round(float(rng.uniform(5, 500)), 2)
        shelf_life_days = int(rng.integers(30, 730)) if category == "food" else int(rng.integers(180, 1500))
        lead_time_days = int(rng.integers(2, 21))
        product_rows.append({
            "product_id": product_id,
            "category": category,
            "base_price": base_price,
            "shelf_life_days": shelf_life_days,
            "lead_time_days": lead_time_days
        })
    products_df = pd.DataFrame(product_rows)

    cities = ["Moscow", "Saint_Petersburg", "Kazan", "Novosibirsk", "Yekaterinburg", "Samara"]
    warehouse_rows = []
    for warehouse_id in range(1, n_warehouses + 1):
        capacity = int(rng.integers(5000, 30000))
        region_demand_factor = round(float(rng.uniform(0.8, 1.3)), 3)
        warehouse_rows.append({
            "warehouse_id": warehouse_id,
            "city": rng.choice(cities),
            "capacity": capacity,
            "region_demand_factor": region_demand_factor
        })
    warehouses_df = pd.DataFrame(warehouse_rows)

    start_date = datetime.date.today() - timedelta(days=n_days)
    order_rows = []
    for day_idx in range(n_days):
        current_date = start_date + timedelta(days=day_idx)
        weekday = current_date.weekday()
        month = current_date.month

        weekday_factor = 1.15 if weekday in [4, 5] else 0.95 if weekday == 6 else 1.0
        month_factor = 1.2 if month in [11, 12] else 1.0

        for product_id in products_df["product_id"]:
            product = products_df.loc[products_df["product_id"] == product_id].iloc[0]
            category = product["category"]
            base_price = product["base_price"]

            category_factor = {
                "food": 1.5,
                "electronics": 0.8,
                "household": 1.1,
                "clothing": 1.0,
                "sports": 0.9
            }[category]

            for warehouse_id in warehouses_df["warehouse_id"]:
                warehouse = warehouses_df.loc[warehouses_df["warehouse_id"] == warehouse_id].iloc[0]
                region_factor = warehouse["region_demand_factor"]

                lambda_orders = 1.5 * category_factor * region_factor * weekday_factor * month_factor
                num_orders = rng.poisson(lambda_orders)

                for _ in range(num_orders):
                    base_qty = {
                        "food": rng.integers(1, 8),
                        "electronics": rng.integers(1, 3),
                        "household": rng.integers(1, 5),
                        "clothing": rng.integers(1, 4),
                        "sports": rng.integers(1, 3)
                    }[category]

                    promo_flag = int(rng.random() < 0.08)
                    promo_multiplier = 1.3 if promo_flag else 1.0
                    quantity = max(1, int(round(base_qty * promo_multiplier)))

                    order_rows.append({
                        "order_id": len(order_rows) + 1,
                        "order_date": current_date.isoformat(),
                        "product_id": int(product_id),
                        "warehouse_id": int(warehouse_id),
                        "quantity": int(quantity),
                        "unit_price": round(float(base_price * rng.uniform(0.9, 1.1)), 2),
                        "promo_flag": promo_flag
                    })

    orders_df = pd.DataFrame(order_rows)

    products_path = os.path.join(data_dir, "products.csv")
    warehouses_path = os.path.join(data_dir, "warehouses.csv")
    orders_path = os.path.join(data_dir, "orders.csv")

    products_df.to_csv(products_path, index=False)
    warehouses_df.to_csv(warehouses_path, index=False)
    orders_df.to_csv(orders_path, index=False)

    return products_df, warehouses_df, orders_df


def data_extraction(data_dir):
    """
    Извлечение данных из csv-файлов
    """
    products = pd.read_csv(os.path.join(data_dir, "products.csv"))
    warehouses = pd.read_csv(os.path.join(data_dir, "warehouses.csv"))
    orders = pd.read_csv(os.path.join(data_dir, "orders.csv"), parse_dates=["order_date"])
    return products, warehouses, orders


def data_validation(products, warehouses, orders):
    """
    Проверка валидности структуры датасетов
    """
    required_products = {"product_id", "category", "base_price", "shelf_life_days", "lead_time_days"}
    required_warehouses = {"warehouse_id", "city", "capacity", "region_demand_factor"}
    required_orders = {"order_id", "order_date", "product_id", "warehouse_id", "quantity", "unit_price", "promo_flag"}

    errors = []

    if not required_products.issubset(products.columns):
        errors.append("products.csv schema invalid")
    if not required_warehouses.issubset(warehouses.columns):
        errors.append("warehouses.csv schema invalid")
    if not required_orders.issubset(orders.columns):
        errors.append("orders.csv schema invalid")

    if products.empty:
        errors.append("products.csv is empty")
    if warehouses.empty:
        errors.append("warehouses.csv is empty")
    if orders.empty:
        errors.append("orders.csv is empty")

    if (orders["quantity"] < 0).any():
        errors.append("orders.csv contains negative quantity")
    if (orders["unit_price"] < 0).any():
        errors.append("orders.csv contains negative unit_price")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    }


def data_preparation(products, warehouses, orders):
    """
    Подготовка датасетов для работы модели
    """
    daily = (
        orders.groupby(["order_date", "product_id", "warehouse_id"], as_index=False)
        .agg(
            quantity=("quantity", "sum"),
            avg_unit_price=("unit_price", "mean"),
            promo_flag=("promo_flag", "max")
        )
        .sort_values(["product_id", "warehouse_id", "order_date"])
    )

    min_date = daily["order_date"].min()
    max_date = daily["order_date"].max()
    all_dates = pd.date_range(min_date, max_date, freq="D")
    product_ids = products["product_id"].unique()
    warehouse_ids = warehouses["warehouse_id"].unique()

    full_index = pd.MultiIndex.from_product(
        [all_dates, product_ids, warehouse_ids],
        names=["order_date", "product_id", "warehouse_id"]
    )
    full_df = pd.DataFrame(index=full_index).reset_index()

    df = full_df.merge(
        daily,
        on=["order_date", "product_id", "warehouse_id"],
        how="left"
    )
    df["quantity"] = df["quantity"].fillna(0)
    df["avg_unit_price"] = df["avg_unit_price"].fillna(0)
    df["promo_flag"] = df["promo_flag"].fillna(0)

    df = df.merge(products, on="product_id", how="left")
    df = df.merge(warehouses, on="warehouse_id", how="left")

    df["day_of_week"] = df["order_date"].dt.dayofweek
    df["month"] = df["order_date"].dt.month
    df["day_of_month"] = df["order_date"].dt.day

    df = df.sort_values(["product_id", "warehouse_id", "order_date"])
    grouped = df.groupby(["product_id", "warehouse_id"], group_keys=False)

    df["lag_1"] = grouped["quantity"].shift(1)
    df["lag_7"] = grouped["quantity"].shift(7)
    df["rolling_mean_7"] = grouped["quantity"].shift(1).rolling(7).mean()
    df["rolling_sum_7"] = grouped["quantity"].shift(1).rolling(7).sum()
    df["rolling_mean_14"] = grouped["quantity"].shift(1).rolling(14).mean()

    df["target_demand_next_7d"] = grouped["quantity"].transform(
        lambda s: s.rolling(7).sum().shift(-7)
    )

    df = df.dropna(subset=[
        "lag_1", "lag_7", "rolling_mean_7",
        "rolling_sum_7", "rolling_mean_14",
        "target_demand_next_7d"
    ]).copy()

    feature_cols = [
        "product_id",
        "warehouse_id",
        "category",
        "base_price",
        "shelf_life_days",
        "lead_time_days",
        "city",
        "capacity",
        "region_demand_factor",
        "day_of_week",
        "month",
        "day_of_month",
        "promo_flag",
        "avg_unit_price",
        "lag_1",
        "lag_7",
        "rolling_mean_7",
        "rolling_sum_7",
        "rolling_mean_14"
    ]
    target_col = "target_demand_next_7d"

    X = df[feature_cols].copy()
    y = df[target_col].copy()

    split_date = df["order_date"].quantile(0.8)
    train_mask = df["order_date"] <= split_date
    test_mask = df["order_date"] > split_date

    X_train = X.loc[train_mask].copy()
    y_train = y.loc[train_mask].copy()
    X_test = X.loc[test_mask].copy()
    y_test = y.loc[test_mask].copy()

    return X_train, X_test, y_train, y_test, df


def save_processed_data(base_dir, X_train, X_test, y_train, y_test, full_df):
    """
    Сохранение обработанных датасетов и таргетов
    """
    processed_dir = os.path.join(base_dir, "processed")
    reference_dir = os.path.join(base_dir, "reference")
    ensure_dir(processed_dir)
    ensure_dir(reference_dir)

    train_df = X_train.copy()
    train_df["target_demand_next_7d"] = y_train.values

    test_df = X_test.copy()
    test_df["target_demand_next_7d"] = y_test.values

    train_df.to_csv(os.path.join(processed_dir, "train.csv"), index=False)
    test_df.to_csv(os.path.join(processed_dir, "test.csv"), index=False)

    # reference - последние 5000 строк полного датасета для отчётов drift
    reference = full_df.tail(5000).copy()
    reference.to_csv(os.path.join(reference_dir, "reference.csv"), index=False)


def run_data_pipeline(data_dir="artifacts/data/raw", artifacts_dir="artifacts/data"):
    """
    Запускает паплайн подготовки и обработки данных
    """
    if not all(os.path.exists(os.path.join(data_dir, f)) for f in ["products.csv", "warehouses.csv", "orders.csv"]):
        generate_synthetic_data(data_dir)

    products, warehouses, orders = data_extraction(data_dir)
    validation = data_validation(products, warehouses, orders)
    if not validation["is_valid"]:
        raise ValueError(f"Validation failed: {validation['errors']}")

    X_train, X_test, y_train, y_test, full_df = data_preparation(products, warehouses, orders)
    save_processed_data(artifacts_dir, X_train, X_test, y_train, y_test, full_df)

    return {
        "train_rows": len(X_train),
        "test_rows": len(X_test),
        "validation": validation
    }


if __name__ == "__main__":
    result = run_data_pipeline()
    # логируемый результат, добавлял для локального тестирования
    print(json.dumps(result, indent=2, default=str))
