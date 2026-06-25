"""Logistics plugin manifest."""

from backend.app.plugins.logistics.models import LogisticsExtraction
from backend.app.plugins.logistics.extractor import LogisticsPlugin

MANIFEST = {
    "id": "logistics",
    "name": "Logistics",
    "version": "1.0.0",
    "description": "Parses logistics/shipment documents and extracts structured shipment data",
    "output_model": LogisticsExtraction,
    "graph_worthy": True,
    "class": "backend.app.plugins.logistics.extractor.LogisticsPlugin",
}