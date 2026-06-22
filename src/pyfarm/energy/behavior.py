"""EnergyBehavior — energy analysis and reporting."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pyfarm.energy.calculator import EnergyCalculator
from pyfarm.energy.models import EnergyCost, EnergyReport, PowerReading


class EnergyBehavior:
    """Async operations for energy tracking and reporting."""

    def __init__(self) -> None:
        self._readings: list[PowerReading] = []

    async def record_reading(self, reading: PowerReading) -> None:
        """Record a power reading."""
        self._readings.append(reading)

    async def get_readings(
        self,
        equipment_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[PowerReading]:
        """Query readings with optional filters."""
        readings = self._readings
        if equipment_id:
            readings = [r for r in readings if r.equipment_id == equipment_id]
        if start_time:
            readings = [r for r in readings if r.timestamp >= start_time]
        if end_time:
            readings = [r for r in readings if r.timestamp <= end_time]
        return readings

    async def generate_report(
        self,
        start_time: datetime,
        end_time: datetime,
        cost_model: EnergyCost,
    ) -> EnergyReport:
        """Generate energy report for a time period."""
        readings = await self.get_readings(start_time=start_time, end_time=end_time)
        if not readings:
            return EnergyReport(
                period_start=start_time,
                period_end=end_time,
                total_kwh=0.0,
                total_cost=0.0,
                peak_kwh=0.0,
                off_peak_kwh=0.0,
                kg_co2_emitted=0.0,
                average_power_w=0.0,
                equipment_breakdown={},
            )
        duration_seconds = (end_time - start_time).total_seconds()
        avg_watts = EnergyCalculator.average_power(
            [{"watts": r.watts} for r in readings]
        )
        total_kwh = EnergyCalculator.watts_to_kwh(avg_watts, duration_seconds)
        peak_kwh, off_peak_kwh = EnergyCalculator.peak_off_peak_split(
            [{"timestamp": r.timestamp, "watts": r.watts} for r in readings],
        )
        cost = EnergyCalculator.energy_cost(
            peak_kwh,
            off_peak_kwh,
            cost_model.rate_per_kwh,
            cost_model.peak_rate_multiplier,
        )
        emissions = EnergyCalculator.carbon_footprint(
            total_kwh,
            cost_model.carbon_factor_kg_co2_per_kwh,
        )
        equipment_breakdown = {}
        for eq_id in set(r.equipment_id for r in readings):
            eq_readings = [r for r in readings if r.equipment_id == eq_id]
            eq_watts = EnergyCalculator.average_power(
                [{"watts": r.watts} for r in eq_readings]
            )
            equipment_breakdown[eq_id] = EnergyCalculator.watts_to_kwh(
                eq_watts, duration_seconds
            )
        return EnergyReport(
            period_start=start_time,
            period_end=end_time,
            total_kwh=total_kwh,
            total_cost=cost,
            peak_kwh=peak_kwh,
            off_peak_kwh=off_peak_kwh,
            kg_co2_emitted=emissions,
            average_power_w=avg_watts,
            equipment_breakdown=equipment_breakdown,
        )

    async def get_top_consumers(self, limit: int = 5) -> list[tuple[str, float]]:
        """Get equipment consuming most power (average watts)."""
        equipment_avg: dict[str, list[float]] = {}
        for reading in self._readings:
            if reading.equipment_id not in equipment_avg:
                equipment_avg[reading.equipment_id] = []
            equipment_avg[reading.equipment_id].append(reading.watts)
        averages = [
            (eq_id, sum(watts) / len(watts))
            for eq_id, watts in equipment_avg.items()
        ]
        return sorted(averages, key=lambda x: x[1], reverse=True)[:limit]
