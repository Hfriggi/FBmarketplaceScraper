import os
import pathlib
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS


BASE_DIR = pathlib.Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env")

BRIGHTDATA_API_URL = "https://api.brightdata.com/datasets/v3"
BRIGHTDATA_DATASET_ID = os.getenv(
    "BRIGHTDATA_DATASET_ID", "gd_lvt9iwuh6fbcwmx1a"
)
POLL_TIMEOUT_SECONDS = int(os.getenv("BRIGHTDATA_POLL_TIMEOUT_SECONDS", "180"))
POLL_INTERVAL_SECONDS = float(os.getenv("BRIGHTDATA_POLL_INTERVAL_SECONDS", "3"))

# O ID de Indaial foi confirmado na URL do Marketplace usada pelo projeto.
# O ID de Blumenau corresponde ao Facebook location ID da cidade.
MARKETPLACE_LOCATIONS = {
    "indaial": {
        "label": "Indaial, SC",
        "path": "104032612966151",
    },
    "blumenau": {
        "label": "Blumenau, SC",
        "path": "106081109431806",
    },
}

ALLOWED_SORTS = {
    "suggested": None,
    "newest": "creation_time_descend",
    "distance": "distance_ascend",
    "price_asc": "price_ascend",
    "price_desc": "price_descend",
}

ALLOWED_DELIVERY_METHODS = {
    "all": None,
    "local_pick_up": "local_pick_up",
    "shipping": "shipping",
}

app = Flask(__name__)
CORS(app)


class ValidationError(ValueError):
    pass


class BrightDataError(RuntimeError):
    pass


def get_api_key():
    """Lê a chave do ambiente e usa o arquivo local apenas como fallback."""
    api_key = os.getenv("BRIGHTDATA_API_KEY", "").strip()
    if api_key:
        return api_key

    key_file = BASE_DIR / "brightdata_api_key.txt"
    if key_file.exists():
        return key_file.read_text(encoding="utf-8").strip()

    raise BrightDataError(
        "Configure BRIGHTDATA_API_KEY ou crie backend/brightdata_api_key.txt."
    )


def parse_integer(value, field, default=None, minimum=None, maximum=None):
    if value in (None, ""):
        if default is not None:
            return default
        return None

    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} deve ser um número inteiro.") from exc

    if minimum is not None and number < minimum:
        raise ValidationError(f"{field} deve ser maior ou igual a {minimum}.")
    if maximum is not None and number > maximum:
        raise ValidationError(f"{field} deve ser menor ou igual a {maximum}.")
    return number


def facebook_days_filter(days):
    """Converte dias arbitrários para uma faixa aceita pelo filtro do Facebook."""
    if days <= 1:
        return 1
    if days <= 7:
        return 7
    return 30


def parse_filters(payload):
    query = str(payload.get("query", "")).strip()
    if not query:
        raise ValidationError("Informe uma palavra-chave em query.")

    location_key = str(
        payload.get("baseLocation", payload.get("location", "indaial"))
    ).strip().lower()
    if location_key not in MARKETPLACE_LOCATIONS:
        allowed = ", ".join(MARKETPLACE_LOCATIONS)
        raise ValidationError(f"baseLocation inválida. Use: {allowed}.")

    min_price = parse_integer(payload.get("minPrice"), "minPrice", minimum=0)
    max_price = parse_integer(payload.get("maxPrice"), "maxPrice", minimum=0)
    if min_price is not None and max_price is not None and min_price > max_price:
        raise ValidationError("minPrice não pode ser maior que maxPrice.")

    days = parse_integer(
        payload.get("daysSinceListed"),
        "daysSinceListed",
        default=1,
        minimum=1,
        maximum=30,
    )
    radius = parse_integer(
        payload.get("radius"), "radius", default=20, minimum=1, maximum=500
    )
    limit = parse_integer(
        payload.get("limit"), "limit", default=20, minimum=1, maximum=50
    )

    sort = str(payload.get("sortBy", "newest")).strip().lower()
    if sort not in ALLOWED_SORTS:
        raise ValidationError(f"sortBy inválido. Use: {', '.join(ALLOWED_SORTS)}.")

    delivery = str(payload.get("deliveryMethod", "local_pick_up")).strip().lower()
    if delivery not in ALLOWED_DELIVERY_METHODS:
        raise ValidationError(
            f"deliveryMethod inválido. Use: {', '.join(ALLOWED_DELIVERY_METHODS)}."
        )

    exact_value = payload.get("exact", False)
    exact = exact_value if isinstance(exact_value, bool) else str(exact_value).lower() == "true"

    return {
        "query": query,
        "base_location": location_key,
        "min_price": min_price,
        "max_price": max_price,
        "days": days,
        "radius": radius,
        "limit": limit,
        "sort": sort,
        "delivery": delivery,
        "exact": exact,
    }


def build_marketplace_url(filters):
    location = MARKETPLACE_LOCATIONS[filters["base_location"]]
    params = {
        "query": filters["query"],
        "locale": "pt_BR",
        "daysSinceListed": facebook_days_filter(filters["days"]),
        "radius": filters["radius"],
        "exact": str(filters["exact"]).lower(),
    }

    if filters["min_price"] is not None:
        params["minPrice"] = filters["min_price"]
    if filters["max_price"] is not None:
        params["maxPrice"] = filters["max_price"]
    if ALLOWED_SORTS[filters["sort"]]:
        params["sortBy"] = ALLOWED_SORTS[filters["sort"]]
    if ALLOWED_DELIVERY_METHODS[filters["delivery"]]:
        params["deliveryMethod"] = ALLOWED_DELIVERY_METHODS[filters["delivery"]]

    return (
        f"https://www.facebook.com/marketplace/{location['path']}/search/?"
        f"{urlencode(params)}"
    )


def brightdata_headers():
    return {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
    }


def response_error(response):
    try:
        detail = response.json()
    except ValueError:
        detail = response.text[:500]
    return f"Bright Data retornou HTTP {response.status_code}: {detail}"


def download_snapshot(snapshot_id, headers):
    response = requests.get(
        f"{BRIGHTDATA_API_URL}/snapshot/{snapshot_id}",
        params={"format": "json"},
        headers=headers,
        timeout=30,
    )
    if not response.ok:
        raise BrightDataError(response_error(response))

    data = response.json()
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("data"), list):
        return data["data"]
    raise BrightDataError("A Bright Data retornou um snapshot em formato inesperado.")


def wait_for_snapshot(snapshot_id, headers):
    deadline = time.monotonic() + POLL_TIMEOUT_SECONDS

    while time.monotonic() < deadline:
        response = requests.get(
            f"{BRIGHTDATA_API_URL}/progress/{snapshot_id}",
            headers=headers,
            timeout=20,
        )
        if not response.ok:
            raise BrightDataError(response_error(response))

        progress = response.json()
        status = str(progress.get("status", "")).lower()
        if status == "ready":
            return download_snapshot(snapshot_id, headers)
        if status in {"failed", "error", "cancelled", "canceled"}:
            raise BrightDataError(
                f"A coleta {snapshot_id} terminou com status {status}: {progress}"
            )

        time.sleep(POLL_INTERVAL_SECONDS)

    raise BrightDataError(
        f"A coleta {snapshot_id} não terminou em {POLL_TIMEOUT_SECONDS} segundos."
    )


def collect_marketplace(search_url, limit):
    headers = brightdata_headers()
    response = requests.post(
        f"{BRIGHTDATA_API_URL}/trigger",
        params={
            "dataset_id": BRIGHTDATA_DATASET_ID,
            "type": "discover_new",
            "discover_by": "url",
            "limit_per_input": limit,
            "include_errors": "true",
            "notify": "false",
        },
        json=[{"url": search_url}],
        headers=headers,
        timeout=30,
    )
    if not response.ok:
        raise BrightDataError(response_error(response))

    result = response.json()
    snapshot_id = result.get("snapshot_id") if isinstance(result, dict) else None
    if not snapshot_id:
        raise BrightDataError("A Bright Data não retornou o snapshot_id da coleta.")

    return wait_for_snapshot(snapshot_id, headers), snapshot_id


def parse_listing_date(value):
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def format_price(value, currency):
    if value is None:
        return "Preço não informado"
    if currency == "BRL":
        formatted = f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatted}"
    return f"{currency or ''} {value}".strip()


def first_image(images):
    if isinstance(images, list) and images:
        first = images[0]
        if isinstance(first, str):
            return first
        if isinstance(first, dict):
            return first.get("url", "")
    return ""


def normalize_and_filter(rows, filters):
    cutoff = datetime.now(timezone.utc) - timedelta(days=filters["days"])
    listings = []

    for row in rows:
        if not isinstance(row, dict) or row.get("error"):
            continue

        price = row.get("final_price")
        try:
            numeric_price = float(price) if price is not None else None
        except (TypeError, ValueError):
            numeric_price = None

        if filters["min_price"] is not None and (
            numeric_price is None or numeric_price < filters["min_price"]
        ):
            continue
        if filters["max_price"] is not None and (
            numeric_price is None or numeric_price > filters["max_price"]
        ):
            continue

        listing_date = parse_listing_date(row.get("listing_date"))
        if listing_date and listing_date < cutoff:
            continue

        listings.append(
            {
                "id": row.get("product_id"),
                "titulo": row.get("title") or "Sem título",
                "preco": format_price(numeric_price, row.get("currency")),
                "precoNumerico": numeric_price,
                "moeda": row.get("currency"),
                "link": row.get("url") or "",
                "imagem": first_image(row.get("images")),
                "localizacao": row.get("location") or "Localização não informada",
                "dataPublicacao": row.get("listing_date"),
                "condicao": row.get("condition"),
                "distanciaKm": None,
            }
        )

    return listings


@app.get("/health")
def health():
    return jsonify({"status": "ok", "provider": "brightdata"})


@app.post("/scrape")
def scrape():
    try:
        payload = request.get_json(silent=True) or {}
        filters = parse_filters(payload)
        search_url = build_marketplace_url(filters)
        rows, snapshot_id = collect_marketplace(search_url, filters["limit"])
        listings = normalize_and_filter(rows, filters)
        location = MARKETPLACE_LOCATIONS[filters["base_location"]]

        return jsonify(
            {
                "resultados": listings,
                "total": len(listings),
                "snapshotId": snapshot_id,
                "consulta": {
                    "url": search_url,
                    "baseLocation": filters["base_location"],
                    "baseLocationLabel": location["label"],
                    "radiusKm": filters["radius"],
                    "distanceIsApproximate": True,
                    "avisoDistancia": (
                        "O raio é aplicado pelo Facebook ao redor da cidade-base. "
                        "O dataset não fornece coordenadas para confirmar a distância exata."
                    ),
                },
            }
        )
    except ValidationError as exc:
        return jsonify({"erro": str(exc)}), 400
    except requests.RequestException as exc:
        app.logger.exception("Falha de comunicação com a Bright Data")
        return jsonify({"erro": f"Falha de comunicação com a Bright Data: {exc}"}), 502
    except BrightDataError as exc:
        app.logger.error("Erro da Bright Data: %s", exc)
        return jsonify({"erro": str(exc)}), 502
    except Exception:
        app.logger.exception("Erro inesperado durante a coleta")
        return jsonify({"erro": "Erro inesperado durante a coleta."}), 500


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=5000, debug=debug)
