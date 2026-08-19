from fastapi import APIRouter, HTTPException, Query

from models.model_loader import model_loader
from services import dashboard_service
from services.dashboard_store import store_ready
from services.curve_service import get_evaluation_curves
from services.insights_service import get_global_feature_importance
from services.metrics_service import get_model_metrics

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _params(
    date_from=None,
    date_to=None,
    as_of=None,
    airline=None,
    origin=None,
    destination=None,
    flight_number=None,
    tail_number=None,
    risk=None,
    prediction=None,
    prob_min=None,
    prob_max=None,
    route_search=None,
):
    return {
        "date_from": date_from,
        "date_to": date_to,
        "as_of": as_of,
        "airline": airline,
        "origin": origin,
        "destination": destination,
        "flight_number": flight_number,
        "tail_number": tail_number,
        "risk": risk,
        "prediction": prediction,
        "prob_min": prob_min,
        "prob_max": prob_max,
        "route_search": route_search,
    }


def _require_store():
    if not store_ready():
        raise HTTPException(
            status_code=503,
            detail=(
                "Dashboard store is not built yet. From the backend directory run: "
                "python scripts/build_dashboard_store.py"
            ),
        )


@router.get("/status")
def dashboard_status():
    return {
        "store_ready": store_ready(),
        "model_loaded": model_loader.is_ready,
        "model_name": model_loader.model_name,
        "ml_threshold": model_loader.threshold,
        "model_unchanged": True,
    }


@router.get("/filters")
def dashboard_filters():
    _require_store()
    return dashboard_service.get_filter_options()


@router.get("/summary")
def dashboard_summary(
    date_from: str | None = None,
    date_to: str | None = None,
    as_of: str | None = None,
    airline: str | None = None,
    origin: str | None = None,
    destination: str | None = None,
    flight_number: str | None = None,
    tail_number: str | None = None,
    risk: str | None = None,
    prediction: str | None = None,
    prob_min: float | None = None,
    prob_max: float | None = None,
):
    _require_store()
    return dashboard_service.get_summary(
        _params(
            date_from, date_to, as_of, airline, origin, destination,
            flight_number, tail_number, risk, prediction, prob_min, prob_max,
        )
    )


@router.get("/trends")
def dashboard_trends(
    aggregation: str = Query("daily"),
    date_from: str | None = None,
    date_to: str | None = None,
    as_of: str | None = None,
    airline: str | None = None,
    origin: str | None = None,
    destination: str | None = None,
    flight_number: str | None = None,
    tail_number: str | None = None,
    risk: str | None = None,
    prediction: str | None = None,
    prob_min: float | None = None,
    prob_max: float | None = None,
):
    _require_store()
    return dashboard_service.get_trends(
        _params(
            date_from, date_to, as_of, airline, origin, destination,
            flight_number, tail_number, risk, prediction, prob_min, prob_max,
        ),
        aggregation=aggregation,
    )


@router.get("/airports")
def dashboard_airports(
    date_from: str | None = None,
    date_to: str | None = None,
    as_of: str | None = None,
    airline: str | None = None,
    origin: str | None = None,
    destination: str | None = None,
    risk: str | None = None,
    prediction: str | None = None,
    prob_min: float | None = None,
    prob_max: float | None = None,
):
    _require_store()
    return dashboard_service.get_airports(
        _params(
            date_from, date_to, as_of, airline, origin, destination,
            None, None, risk, prediction, prob_min, prob_max,
        )
    )


@router.get("/airlines")
def dashboard_airlines(
    date_from: str | None = None,
    date_to: str | None = None,
    as_of: str | None = None,
    origin: str | None = None,
    destination: str | None = None,
    risk: str | None = None,
    prediction: str | None = None,
    prob_min: float | None = None,
    prob_max: float | None = None,
):
    _require_store()
    return dashboard_service.get_airlines(
        _params(
            date_from, date_to, as_of, None, origin, destination,
            None, None, risk, prediction, prob_min, prob_max,
        )
    )


@router.get("/routes")
def dashboard_routes(
    limit: int = 10,
    route_search: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    as_of: str | None = None,
    airline: str | None = None,
    origin: str | None = None,
    destination: str | None = None,
    risk: str | None = None,
    prediction: str | None = None,
    prob_min: float | None = None,
    prob_max: float | None = None,
):
    _require_store()
    return dashboard_service.get_routes(
        _params(
            date_from, date_to, as_of, airline, origin, destination,
            None, None, risk, prediction, prob_min, prob_max, route_search,
        ),
        limit=limit,
    )


@router.get("/high-risk-flights")
def dashboard_high_risk(
    page: int = 1,
    page_size: int = 20,
    sort: str = "probability",
    order: str = "desc",
    date_from: str | None = None,
    date_to: str | None = None,
    as_of: str | None = None,
    airline: str | None = None,
    origin: str | None = None,
    destination: str | None = None,
    flight_number: str | None = None,
    tail_number: str | None = None,
    risk: str = "HIGH",
    prediction: str | None = None,
    prob_min: float | None = None,
    prob_max: float | None = None,
):
    _require_store()
    return dashboard_service.get_high_risk_flights(
        _params(
            date_from, date_to, as_of, airline, origin, destination,
            flight_number, tail_number, risk, prediction, prob_min, prob_max,
        ),
        page=page,
        page_size=page_size,
        sort=sort,
        order=order,
    )


@router.get("/map")
def dashboard_map(
    date_from: str | None = None,
    date_to: str | None = None,
    as_of: str | None = None,
    airline: str | None = None,
    origin: str | None = None,
    destination: str | None = None,
    flight_number: str | None = None,
    tail_number: str | None = None,
    risk: str | None = None,
    prediction: str | None = None,
    prob_min: float | None = None,
    prob_max: float | None = None,
):
    _require_store()
    return dashboard_service.get_map_payload(
        _params(
            date_from, date_to, as_of, airline, origin, destination,
            flight_number, tail_number, risk, prediction, prob_min, prob_max,
        )
    )


@router.get("/flights/{flight_id}")
def dashboard_flight(flight_id: int):
    _require_store()
    payload = dashboard_service.get_flight(flight_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Flight not found")
    return payload


@router.get("/aircraft/{tail_number}")
def dashboard_aircraft(
    tail_number: str,
    date_from: str | None = None,
    date_to: str | None = None,
    as_of: str | None = None,
):
    _require_store()
    return dashboard_service.get_aircraft(
        tail_number,
        _params(date_from, date_to, as_of),
    )


@router.get("/delay-distribution")
def dashboard_delay_distribution(
    date_from: str | None = None,
    date_to: str | None = None,
    as_of: str | None = None,
    airline: str | None = None,
    origin: str | None = None,
    destination: str | None = None,
    risk: str | None = None,
    prediction: str | None = None,
):
    _require_store()
    return dashboard_service.get_delay_distribution(
        _params(date_from, date_to, as_of, airline, origin, destination, None, None, risk, prediction)
    )


@router.get("/probability-distribution")
def dashboard_probability_distribution(
    date_from: str | None = None,
    date_to: str | None = None,
    as_of: str | None = None,
    airline: str | None = None,
    origin: str | None = None,
    destination: str | None = None,
    risk: str | None = None,
    prediction: str | None = None,
):
    _require_store()
    return dashboard_service.get_probability_distribution(
        _params(date_from, date_to, as_of, airline, origin, destination, None, None, risk, prediction)
    )


@router.get("/timeline")
def dashboard_timeline():
    _require_store()
    return dashboard_service.get_timeline_bounds()


@router.get("/model-analytics")
def dashboard_model_analytics():
    metrics = get_model_metrics()
    metrics["model_loaded"] = model_loader.is_ready
    importance = get_global_feature_importance(top_n=68)
    try:
        curves = get_evaluation_curves()
    except Exception as exc:
        curves = {"error": str(exc)}
    response = metrics.copy()
    response["feature_importance"] = importance
    response["curves"] = curves
    return response
