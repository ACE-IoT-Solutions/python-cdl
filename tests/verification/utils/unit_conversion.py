"""
Unit conversion utilities for OBC verification testing.

Uses Pint library for robust unit conversions between CDL (SI units) and
Building Automation System (BAS) units (typically Imperial).

Common conversions for HVAC control:
- Temperature: K ↔ °F, K ↔ °C
- Pressure: Pa ↔ inH2O, Pa ↔ psi
- Flow: kg/s ↔ CFM, L/s ↔ GPM
- Power: W ↔ Btu/h
- Percentage: fraction (0-1) ↔ percent (0-100)
"""

from typing import Any
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field
import pint

# Create a unit registry
ureg = pint.UnitRegistry()

# Define common HVAC units
# Pint already has most units, but we can add aliases for convenience
try:
    ureg.define('fraction = [] = frac')
    ureg.define('percent = 0.01 * fraction = pct = %')
except pint.errors.RedefinitionError:
    pass  # Already defined


class UnitConverter:
    """Convert values between different units using Pint."""

    def __init__(self):
        """Initialize unit converter with Pint registry."""
        self.ureg = ureg

    def convert(
        self,
        value: float | np.ndarray | pd.Series,
        from_unit: str,
        to_unit: str
    ) -> float | np.ndarray | pd.Series:
        """
        Convert value from one unit to another.

        Args:
            value: Value(s) to convert
            from_unit: Source unit (e.g., 'K', 'degF', 'Pa')
            to_unit: Target unit (e.g., 'degC', 'K', 'inH2O')

        Returns:
            Converted value(s) in target unit

        Example:
            >>> converter = UnitConverter()
            >>> converter.convert(273.15, 'K', 'degC')
            0.0
            >>> converter.convert(32.0, 'degF', 'K')
            273.15
        """
        # Handle special case for dimensionless units
        if from_unit in ['1', '', 'dimensionless']:
            from_unit = 'dimensionless'
        if to_unit in ['1', '', 'dimensionless']:
            to_unit = 'dimensionless'

        # Handle pandas Series
        if isinstance(value, pd.Series):
            return pd.Series(
                self.convert(value.values, from_unit, to_unit),
                index=value.index
            )

        # For offset temperature units (degC, degF), use Quantity directly
        # See: https://pint.readthedocs.io/en/stable/user/nonmult.html
        offset_units = ['degC', 'degF', 'degree_Celsius', 'degree_Fahrenheit']
        if from_unit in offset_units or to_unit in offset_units:
            quantity = self.ureg.Quantity(value, from_unit)
            converted = quantity.to(to_unit)
        else:
            # For non-offset units, use multiplication
            quantity = value * self.ureg(from_unit)
            converted = quantity.to(to_unit)

        # Return magnitude (numeric value without unit)
        return converted.magnitude

    def convert_temperature(
        self,
        value: float | np.ndarray,
        from_unit: str,
        to_unit: str
    ) -> float | np.ndarray:
        """
        Convert temperature values.

        Supports: K, degC, degF, degR

        Args:
            value: Temperature value(s)
            from_unit: Source unit (K, degC, degF, degR)
            to_unit: Target unit (K, degC, degF, degR)

        Returns:
            Converted temperature value(s)

        Example:
            >>> converter = UnitConverter()
            >>> converter.convert_temperature(273.15, 'K', 'degC')
            0.0
            >>> converter.convert_temperature(32.0, 'degF', 'degC')
            0.0
        """
        return self.convert(value, from_unit, to_unit)

    def convert_pressure(
        self,
        value: float | np.ndarray,
        from_unit: str,
        to_unit: str
    ) -> float | np.ndarray:
        """
        Convert pressure values.

        Supports: Pa, kPa, psi, inH2O, bar, atm

        Args:
            value: Pressure value(s)
            from_unit: Source unit
            to_unit: Target unit

        Returns:
            Converted pressure value(s)

        Example:
            >>> converter = UnitConverter()
            >>> converter.convert_pressure(101325, 'Pa', 'psi')
            14.696...
        """
        return self.convert(value, from_unit, to_unit)

    def convert_flow(
        self,
        value: float | np.ndarray,
        from_unit: str,
        to_unit: str
    ) -> float | np.ndarray:
        """
        Convert flow rate values.

        Supports: kg/s, L/s, m^3/s, CFM, GPM

        Args:
            value: Flow rate value(s)
            from_unit: Source unit
            to_unit: Target unit

        Returns:
            Converted flow rate value(s)

        Note:
            CFM (cubic feet per minute) and GPM (gallons per minute)
            are volumetric flows. Converting to/from mass flow (kg/s)
            requires density assumptions.
        """
        return self.convert(value, from_unit, to_unit)

    def convert_percentage(
        self,
        value: float | np.ndarray,
        from_unit: str,
        to_unit: str
    ) -> float | np.ndarray:
        """
        Convert between fraction (0-1) and percentage (0-100).

        Args:
            value: Value(s) to convert
            from_unit: 'fraction' or 'percent'
            to_unit: 'fraction' or 'percent'

        Returns:
            Converted value(s)

        Example:
            >>> converter = UnitConverter()
            >>> converter.convert_percentage(0.5, 'fraction', 'percent')
            50.0
            >>> converter.convert_percentage(75.0, 'percent', 'fraction')
            0.75
        """
        return self.convert(value, from_unit, to_unit)


class VariableMapping(BaseModel):
    """Mapping between CDL variable and BAS device point."""

    cdl_name: str = Field(description="CDL variable name")
    cdl_unit: str = Field(description="CDL unit (SI)")
    device_name: str = Field(description="BAS device point name")
    device_unit: str = Field(description="BAS device unit")
    description: str | None = Field(default=None, description="Variable description")

    def convert_to_cdl(
        self,
        device_value: float | np.ndarray,
        converter: UnitConverter | None = None
    ) -> float | np.ndarray:
        """
        Convert device value to CDL units.

        Args:
            device_value: Value from BAS device
            converter: UnitConverter instance (creates new if None)

        Returns:
            Value in CDL units
        """
        if converter is None:
            converter = UnitConverter()

        return converter.convert(device_value, self.device_unit, self.cdl_unit)

    def convert_to_device(
        self,
        cdl_value: float | np.ndarray,
        converter: UnitConverter | None = None
    ) -> float | np.ndarray:
        """
        Convert CDL value to device units.

        Args:
            cdl_value: Value in CDL units
            converter: UnitConverter instance (creates new if None)

        Returns:
            Value in device units
        """
        if converter is None:
            converter = UnitConverter()

        return converter.convert(cdl_value, self.cdl_unit, self.device_unit)


class PointMapping(BaseModel):
    """Collection of variable mappings for a control sequence."""

    mappings: list[VariableMapping] = Field(
        default_factory=list,
        description="List of variable mappings"
    )

    def get_mapping(self, cdl_name: str) -> VariableMapping | None:
        """Get mapping by CDL variable name."""
        for mapping in self.mappings:
            if mapping.cdl_name == cdl_name:
                return mapping
        return None

    def convert_dataframe_to_cdl(
        self,
        df: pd.DataFrame,
        converter: UnitConverter | None = None
    ) -> pd.DataFrame:
        """
        Convert DataFrame with device units to CDL units.

        Args:
            df: DataFrame with device point names as columns
            converter: UnitConverter instance (creates new if None)

        Returns:
            DataFrame with CDL variable names and units
        """
        if converter is None:
            converter = UnitConverter()

        result = pd.DataFrame(index=df.index)

        for mapping in self.mappings:
            if mapping.device_name in df.columns:
                result[mapping.cdl_name] = mapping.convert_to_cdl(
                    df[mapping.device_name],
                    converter
                )

        return result

    def convert_dataframe_to_device(
        self,
        df: pd.DataFrame,
        converter: UnitConverter | None = None
    ) -> pd.DataFrame:
        """
        Convert DataFrame with CDL units to device units.

        Args:
            df: DataFrame with CDL variable names as columns
            converter: UnitConverter instance (creates new if None)

        Returns:
            DataFrame with device point names and units
        """
        if converter is None:
            converter = UnitConverter()

        result = pd.DataFrame(index=df.index)

        for mapping in self.mappings:
            if mapping.cdl_name in df.columns:
                result[mapping.device_name] = mapping.convert_to_device(
                    df[mapping.cdl_name],
                    converter
                )

        return result

    @classmethod
    def from_json_file(cls, filepath: str) -> 'PointMapping':
        """Load point mapping from JSON file (OBC format)."""
        import json
        from pathlib import Path

        with open(filepath) as f:
            data = json.load(f)

        mappings = []
        for item in data:
            mapping = VariableMapping(
                cdl_name=item['cdlName'],
                cdl_unit=item.get('cdlUnit', ''),
                device_name=item['deviceName'],
                device_unit=item.get('deviceUnit', ''),
                description=item.get('description')
            )
            mappings.append(mapping)

        return cls(mappings=mappings)


# Common HVAC unit conversion shortcuts
def kelvin_to_fahrenheit(k: float | np.ndarray) -> float | np.ndarray:
    """Convert Kelvin to Fahrenheit."""
    converter = UnitConverter()
    return converter.convert(k, 'K', 'degF')


def fahrenheit_to_kelvin(f: float | np.ndarray) -> float | np.ndarray:
    """Convert Fahrenheit to Kelvin."""
    converter = UnitConverter()
    return converter.convert(f, 'degF', 'K')


def kelvin_to_celsius(k: float | np.ndarray) -> float | np.ndarray:
    """Convert Kelvin to Celsius."""
    converter = UnitConverter()
    return converter.convert(k, 'K', 'degC')


def celsius_to_kelvin(c: float | np.ndarray) -> float | np.ndarray:
    """Convert Celsius to Kelvin."""
    converter = UnitConverter()
    return converter.convert(c, 'degC', 'K')


def fraction_to_percent(frac: float | np.ndarray) -> float | np.ndarray:
    """Convert fraction (0-1) to percentage (0-100)."""
    converter = UnitConverter()
    return converter.convert(frac, 'fraction', 'percent')


def percent_to_fraction(pct: float | np.ndarray) -> float | np.ndarray:
    """Convert percentage (0-100) to fraction (0-1)."""
    converter = UnitConverter()
    return converter.convert(pct, 'percent', 'fraction')


def pascal_to_inches_water(pa: float | np.ndarray) -> float | np.ndarray:
    """Convert Pascals to inches of water column."""
    converter = UnitConverter()
    return converter.convert(pa, 'Pa', 'inH2O')


def inches_water_to_pascal(inh2o: float | np.ndarray) -> float | np.ndarray:
    """Convert inches of water column to Pascals."""
    converter = UnitConverter()
    return converter.convert(inh2o, 'inH2O', 'Pa')
