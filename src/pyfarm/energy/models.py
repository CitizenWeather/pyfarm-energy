"""Models for energy management."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class PowerReading:
    """Instantaneous power measurement."""

    timestamp: datetime
    equipment_id: str
    watts: float
    voltage_v: float | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.equipment_id:
            raise ValueError("equipment_id cannot be empty")
        if self.watts < 0:
            raise ValueError("watts cannot be negative")
        if self.voltage_v is not None and self.voltage_v <= 0:
            raise ValueError("voltage_v must be positive")


@dataclass
class EnergyCost:
    """Tariff and carbon footprint."""

    rate_per_kwh: float
    demand_charge_per_kw: float | None = None
    carbon_factor_kg_co2_per_kwh: float = 0.5
    peak_hours: tuple[int, int] | None = None
    peak_rate_multiplier: float = 1.0

    def __post_init__(self) -> None:
        if self.rate_per_kwh < 0:
            raise ValueError("rate_per_kwh cannot be negative")
        if self.carbon_factor_kg_co2_per_kwh < 0:
            raise ValueError("carbon_factor cannot be negative")


@dataclass
class EnergyReport:
    """Aggregated energy consumption and cost."""

    period_start: datetime
    period_end: datetime
    total_kwh: float
    total_cost: float
    peak_kwh: float
    off_peak_kwh: float
    kg_co2_emitted: float
    average_power_w: float
    equipment_breakdown: dict[str, float]
