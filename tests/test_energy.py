"""Smoke tests for pyfarm-energy."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from pyfarm.energy import (
    EnergyBehavior,
    EnergyCalculator,
    EnergyCost,
    EnergyReport,
    PowerReading,
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

def test_power_reading_valid():
    now = datetime.now(timezone.utc)
    reading = PowerReading(
        timestamp=now,
        equipment_id="heater-1",
        watts=1500.0,
        voltage_v=240.0,
    )
    assert reading.equipment_id == "heater-1"
    assert reading.watts == 1500.0


def test_power_reading_invalid_watts():
    now = datetime.now(timezone.utc)
    with pytest.raises(ValueError, match="watts cannot be negative"):
        PowerReading(
            timestamp=now,
            equipment_id="heater-1",
            watts=-100.0,
        )


def test_energy_cost_model():
    cost = EnergyCost(
        rate_per_kwh=0.12,
        carbon_factor_kg_co2_per_kwh=0.5,
    )
    assert cost.rate_per_kwh == 0.12
    assert cost.peak_rate_multiplier == 1.0


# ---------------------------------------------------------------------------
# EnergyCalculator
# ---------------------------------------------------------------------------

def test_watts_to_kwh():
    kwh = EnergyCalculator.watts_to_kwh(1000.0, 3600.0)
    assert kwh == pytest.approx(1.0, rel=0.01)


def test_average_power():
    readings = [
        {"watts": 1000.0},
        {"watts": 1500.0},
        {"watts": 2000.0},
    ]
    avg = EnergyCalculator.average_power(readings)
    assert avg == pytest.approx(1500.0, rel=0.01)


def test_carbon_footprint():
    emissions = EnergyCalculator.carbon_footprint(
        kwh=10.0,
        factor_kg_co2_per_kwh=0.5,
    )
    assert emissions == pytest.approx(5.0, rel=0.01)


def test_energy_cost():
    cost = EnergyCalculator.energy_cost(
        peak_kwh=10.0,
        off_peak_kwh=20.0,
        base_rate=0.10,
        peak_multiplier=1.5,
    )
    expected = (10.0 * 0.10 * 1.5) + (20.0 * 0.10)
    assert cost == pytest.approx(expected, rel=0.01)


# ---------------------------------------------------------------------------
# EnergyBehavior
# ---------------------------------------------------------------------------

async def test_behavior_record_reading():
    behavior = EnergyBehavior()
    now = datetime.now(timezone.utc)
    reading = PowerReading(
        timestamp=now,
        equipment_id="heater",
        watts=1000.0,
    )
    await behavior.record_reading(reading)
    readings = await behavior.get_readings()
    assert len(readings) == 1
    assert readings[0].equipment_id == "heater"


async def test_behavior_get_readings_by_equipment():
    behavior = EnergyBehavior()
    now = datetime.now(timezone.utc)
    r1 = PowerReading(timestamp=now, equipment_id="heater", watts=1000.0)
    r2 = PowerReading(timestamp=now, equipment_id="fan", watts=500.0)
    await behavior.record_reading(r1)
    await behavior.record_reading(r2)
    heater_readings = await behavior.get_readings(equipment_id="heater")
    assert len(heater_readings) == 1
    assert heater_readings[0].equipment_id == "heater"


async def test_behavior_generate_report():
    behavior = EnergyBehavior()
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=1)
    for i in range(6):
        reading = PowerReading(
            timestamp=start + timedelta(minutes=10 * i),
            equipment_id="heater",
            watts=1000.0,
        )
        await behavior.record_reading(reading)
    cost_model = EnergyCost(rate_per_kwh=0.12)
    report = await behavior.generate_report(start, now, cost_model)
    assert isinstance(report, EnergyReport)
    assert report.total_kwh > 0
    assert report.total_cost > 0


async def test_behavior_get_top_consumers():
    behavior = EnergyBehavior()
    now = datetime.now(timezone.utc)
    r1 = PowerReading(timestamp=now, equipment_id="heater", watts=2000.0)
    r2 = PowerReading(timestamp=now, equipment_id="fan", watts=500.0)
    await behavior.record_reading(r1)
    await behavior.record_reading(r2)
    top = await behavior.get_top_consumers(limit=2)
    assert len(top) == 2
    assert top[0][0] == "heater"
    assert top[0][1] == 2000.0
