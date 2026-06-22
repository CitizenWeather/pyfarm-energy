"""pyfarm-energy — power usage and cost tracking.

Provides:
  PowerReading         — instantaneous power measurement (watts, voltage)
  EnergyCost           — tariff and carbon footprint model
  EnergyReport         — aggregated consumption and cost summary
  EnergyCalculator     — kWh aggregation and peak/off-peak analysis
  EnergyBehavior       — async operations for energy analysis and reporting
"""
from __future__ import annotations

from pyfarm.energy.models import EnergyCost, EnergyReport, PowerReading
from pyfarm.energy.calculator import EnergyCalculator
from pyfarm.energy.behavior import EnergyBehavior

__all__ = [
    "PowerReading",
    "EnergyCost",
    "EnergyReport",
    "EnergyCalculator",
    "EnergyBehavior",
]
__version__ = "0.1.0"
