from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

prediction_requests_total = Counter(
    "prediction_requests_total",
    "Total number of prediction requests"
)

prediction_request_errors_total = Counter(
    "prediction_request_errors_total",
    "Total number of failed prediction requests"
)

prediction_batch_files_total = Counter(
    "prediction_batch_files_total",
    "Total uploaded batch files processed"
)

prediction_latency_seconds = Histogram(
    "prediction_latency_seconds",
    "Prediction latency in seconds"
)

incident_events_total = Counter(
    "incident_events_total",
    "Total incidents written by the system",
    ["incident_type"]
)


def metrics_response():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
