import os
from phoenix import trace
from phoenix.trace.openai import OpenAIInstrumentor
from openinference.semconv.resource import ResourceAttributes
from opentelemetry import trace as trace_api
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
import sqlite3
import json


def load_phoenix_settings():
    conn = sqlite3.connect("settings.db")
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='phoenix_settings'")
    result = c.fetchone()
    conn.close()

    if result:
        return json.loads(result[0])
    return {
        "project_name": "storm-wiki",
        "enabled": False,
        "collector_endpoint": "localhost:6006",
    }


def setup_phoenix():
    """
    Set up Phoenix for tracing and instrumentation.
    """
    # Load Phoenix settings
    phoenix_settings = load_phoenix_settings()

    # Check if Phoenix is enabled, default to False if the key doesn't exist
    if not phoenix_settings.get("enabled", False):
        return None

    resource = Resource(
        attributes={
            ResourceAttributes.PROJECT_NAME: phoenix_settings.get(
                "project_name", "storm-wiki"
            )
        }
    )
    tracer_provider = trace_sdk.TracerProvider(resource=resource)

    span_exporter = OTLPSpanExporter(
        endpoint=f"http://{phoenix_settings.get('collector_endpoint', 'localhost:6006')}/v1/traces"
    )

    span_processor = SimpleSpanProcessor(span_exporter=span_exporter)
    tracer_provider.add_span_processor(span_processor=span_processor)
    trace_api.set_tracer_provider(tracer_provider=tracer_provider)

    OpenAIInstrumentor().instrument()

    # Return the tracer provider in case it's needed elsewhere
    return tracer_provider
