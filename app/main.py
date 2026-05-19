import time
import random
from flask import Flask, jsonify
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST
)
from flask import Response

app = Flask(__name__)

# -----------------------------------------------
# Prometheus metrics
# -----------------------------------------------
REQUEST_COUNT = Counter(
    'app_request_count_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'app_request_latency_seconds',
    'Request latency in seconds',
    ['endpoint']
)

ERROR_COUNT = Counter(
    'app_error_count_total',
    'Total number of errors',
    ['endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'app_active_requests',
    'Number of active requests'
)

# -----------------------------------------------
# Routes
# -----------------------------------------------
@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200


@app.route('/ready')
def ready():
    return jsonify({'status': 'ready'}), 200


@app.route('/')
def index():
    start_time = time.time()
    ACTIVE_REQUESTS.inc()

    try:
        REQUEST_COUNT.labels(
            method='GET',
            endpoint='/',
            status='200'
        ).inc()

        # Simulate variable latency
        time.sleep(random.uniform(0.01, 0.1))

        return jsonify({
            'message': 'SRE Sample App',
            'status': 'ok'
        }), 200

    except Exception as e:
        ERROR_COUNT.labels(endpoint='/').inc()
        REQUEST_COUNT.labels(
            method='GET',
            endpoint='/',
            status='500'
        ).inc()
        return jsonify({'error': str(e)}), 500

    finally:
        REQUEST_LATENCY.labels(endpoint='/').observe(
            time.time() - start_time
        )
        ACTIVE_REQUESTS.dec()


@app.route('/error')
def simulate_error():
    """Endpoint to simulate errors for SLO testing"""
    ERROR_COUNT.labels(endpoint='/error').inc()
    REQUEST_COUNT.labels(
        method='GET',
        endpoint='/error',
        status='500'
    ).inc()
    return jsonify({'error': 'Simulated error for SLO testing'}), 500


@app.route('/slow')
def simulate_slow():
    """Endpoint to simulate slow requests for latency SLO testing"""
    start_time = time.time()
    time.sleep(random.uniform(1, 3))
    REQUEST_LATENCY.labels(endpoint='/slow').observe(
        time.time() - start_time
    )
    REQUEST_COUNT.labels(
        method='GET',
        endpoint='/slow',
        status='200'
    ).inc()
    return jsonify({'message': 'Slow response for SLO testing'}), 200


@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        generate_latest(),
        mimetype=CONTENT_TYPE_LATEST
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)