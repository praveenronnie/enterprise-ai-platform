"""Pydantic models for logistics extraction."""

from __future__ import annotations

from pydantic import BaseModel, Field

from backend.app.plugins.base_models import PluginExtractionResult


class ShipmentItem(BaseModel):
    description: str = Field(description="Item description")
    quantity: int = Field(description="Quantity of items")
    weight: float = Field(description="Weight in kilograms")
    hazardous: bool = Field(default=False, description="Whether item is hazardous")


class LogisticsExtraction(PluginExtractionResult):
    shipment_id: str = Field(description="Unique shipment identifier")
    origin: str = Field(description="Origin location/city")
    destination: str = Field(description="Destination location/city")
    shipment_date: str = Field(default="", description="Date of shipment (YYYY-MM-DD)")
    delivery_date: str = Field(default="", description="Expected or actual delivery date")
    items: list[ShipmentItem] = Field(default_factory=list, description="List of items in shipment")
    carrier: str = Field(default="", description="Carrier company name")
    status: str = Field(default="pending", description="Current shipment status")