"""Pure math for energy calculations."""
from __future__ import annotations

from datetime import datetime
from typing import Any


class EnergyCalculator:
    """Static methods for energy calculations."""

    @staticmethod
    def watts_to_kwh(watts: float, duration_seconds: float) -> float:
        """Convert watts and duration to kWh."""
        return (watts * duration_seconds) / (3.6e6)

    @staticmethod
    def average_power(readings: list[dict[str, Any]]) -> float:
        """Calculate average power from readings (in watts)."""
        if not readings:
            return 0.0
        return sum(r["watts"] for r in readings) / len(readings)

    @staticmethod
    def peak_off_peak_split(
        readings: list[dict[str, Any]],
        peak_hours: tuple[int, int] = (9, 17),
    ) -> tuple[float, float]:
        """Split readings into peak and off-peak kWh.
        
        Args:
            readings: List of {timestamp, watts} dicts
            peak_hours: (start_hour, end_hour) in 24h format
            
        Returns:
            (peak_kwh, off_peak_kwh)
        """
        peak_total = 0.0
        off_peak_total = 0.0
        for i, reading in enumerate(readings):
            ts = reading.get("timestamp")
            watts = reading.get("watts", 0.0)
            hour = ts.hour if hasattr(ts, "hour") else 0
            is_peak = peak_hours[0] <= hour < peak_hours[1]
            duration = 1.0 if i == len(readings) - 1 else 3600
            kwh = EnergyCalculator.watts_to_kwh(watts, duration)
            if is_peak:
                peak_total += kwh
            else:
                off_peak_total += kwh
        return peak_total, off_peak_total

    @staticmethod
    def carbon_footprint(kwh: float, factor_kg_co2_per_kwh: float) -> float:
        """Calculate carbon emissions from kWh."""
        return kwh * factor_kg_co2_per_kwh

    @staticmethod
    def energy_cost(
        peak_kwh: float,
        off_peak_kwh: float,
        base_rate: float,
        peak_multiplier: float = 1.5,
    ) -> float:
        """Calculate total cost with peak/off-peak rates."""
        peak_cost = peak_kwh * base_rate * peak_multiplier
        off_peak_cost = off_peak_kwh * base_rate
        return peak_cost + off_peak_cost
