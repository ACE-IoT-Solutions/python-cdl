"""
Unit conversion verification tests.

Tests the Pint-based unit conversion utilities for accuracy and correctness.
"""

import pytest
import numpy as np
import pandas as pd
from tests.verification.utils.unit_conversion import (
    UnitConverter,
    VariableMapping,
    PointMapping,
    kelvin_to_fahrenheit,
    fahrenheit_to_kelvin,
    kelvin_to_celsius,
    celsius_to_kelvin,
    fraction_to_percent,
    percent_to_fraction,
    pascal_to_inches_water,
    inches_water_to_pascal,
)


@pytest.fixture
def converter():
    """Create UnitConverter instance."""
    return UnitConverter()


@pytest.mark.verification
class TestTemperatureConversions:
    """Test temperature unit conversions."""

    def test_kelvin_to_celsius(self, converter):
        """Test K to °C conversion."""
        # Water freezing point
        assert converter.convert(273.15, 'K', 'degC') == pytest.approx(0.0, abs=1e-6)
        # Water boiling point
        assert converter.convert(373.15, 'K', 'degC') == pytest.approx(100.0, abs=1e-6)

    def test_kelvin_to_fahrenheit(self, converter):
        """Test K to °F conversion."""
        # Water freezing point
        assert converter.convert(273.15, 'K', 'degF') == pytest.approx(32.0, abs=1e-6)
        # Water boiling point
        assert converter.convert(373.15, 'K', 'degF') == pytest.approx(212.0, abs=1e-6)

    def test_fahrenheit_to_kelvin(self, converter):
        """Test °F to K conversion."""
        assert converter.convert(32.0, 'degF', 'K') == pytest.approx(273.15, abs=1e-6)
        assert converter.convert(212.0, 'degF', 'K') == pytest.approx(373.15, abs=1e-6)

    def test_celsius_to_fahrenheit(self, converter):
        """Test °C to °F conversion."""
        assert converter.convert(0.0, 'degC', 'degF') == pytest.approx(32.0, abs=1e-6)
        assert converter.convert(100.0, 'degC', 'degF') == pytest.approx(212.0, abs=1e-6)
        assert converter.convert(20.0, 'degC', 'degF') == pytest.approx(68.0, abs=1e-6)

    def test_temperature_arrays(self, converter):
        """Test temperature conversion with numpy arrays."""
        temps_k = np.array([273.15, 293.15, 313.15])
        temps_c = converter.convert(temps_k, 'K', 'degC')

        expected = np.array([0.0, 20.0, 40.0])
        np.testing.assert_allclose(temps_c, expected, atol=1e-6)

    def test_temperature_series(self, converter):
        """Test temperature conversion with pandas Series."""
        temps_k = pd.Series([273.15, 293.15, 313.15])
        temps_f = converter.convert(temps_k, 'K', 'degF')

        expected = pd.Series([32.0, 68.0, 104.0])
        pd.testing.assert_series_equal(temps_f, expected, atol=1e-6)

    def test_temperature_shortcuts(self):
        """Test temperature conversion shortcut functions."""
        assert kelvin_to_celsius(273.15) == pytest.approx(0.0, abs=1e-6)
        assert celsius_to_kelvin(0.0) == pytest.approx(273.15, abs=1e-6)
        assert kelvin_to_fahrenheit(273.15) == pytest.approx(32.0, abs=1e-6)
        assert fahrenheit_to_kelvin(32.0) == pytest.approx(273.15, abs=1e-6)


@pytest.mark.verification
class TestPressureConversions:
    """Test pressure unit conversions."""

    def test_pascal_to_psi(self, converter):
        """Test Pa to psi conversion."""
        # Standard atmospheric pressure
        atm_pa = 101325.0
        atm_psi = converter.convert(atm_pa, 'Pa', 'psi')
        assert atm_psi == pytest.approx(14.696, abs=0.001)

    def test_pascal_to_inches_water(self, converter):
        """Test Pa to inH2O conversion."""
        pa = 249.0
        inh2o = converter.convert(pa, 'Pa', 'inH2O')
        assert inh2o == pytest.approx(1.0, abs=0.01)

    def test_pressure_shortcuts(self):
        """Test pressure conversion shortcut functions."""
        assert pascal_to_inches_water(249.0) == pytest.approx(1.0, abs=0.01)
        assert inches_water_to_pascal(1.0) == pytest.approx(249.0, abs=1.0)


@pytest.mark.verification
class TestPercentageConversions:
    """Test percentage/fraction conversions."""

    def test_fraction_to_percent(self, converter):
        """Test fraction to percentage conversion."""
        assert converter.convert(0.0, 'fraction', 'percent') == pytest.approx(0.0)
        assert converter.convert(0.5, 'fraction', 'percent') == pytest.approx(50.0)
        assert converter.convert(1.0, 'fraction', 'percent') == pytest.approx(100.0)

    def test_percent_to_fraction(self, converter):
        """Test percentage to fraction conversion."""
        assert converter.convert(0.0, 'percent', 'fraction') == pytest.approx(0.0)
        assert converter.convert(50.0, 'percent', 'fraction') == pytest.approx(0.5)
        assert converter.convert(100.0, 'percent', 'fraction') == pytest.approx(1.0)

    def test_percentage_shortcuts(self):
        """Test percentage conversion shortcut functions."""
        assert fraction_to_percent(0.75) == pytest.approx(75.0)
        assert percent_to_fraction(25.0) == pytest.approx(0.25)

    def test_percentage_arrays(self, converter):
        """Test percentage conversion with arrays."""
        fractions = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        percents = converter.convert(fractions, 'fraction', 'percent')

        expected = np.array([0.0, 25.0, 50.0, 75.0, 100.0])
        np.testing.assert_allclose(percents, expected)


@pytest.mark.verification
class TestFlowConversions:
    """Test flow rate unit conversions."""

    def test_volumetric_flow(self, converter):
        """Test volumetric flow conversions."""
        # m³/s to L/s
        m3_s = 0.001
        l_s = converter.convert(m3_s, 'm^3/s', 'L/s')
        assert l_s == pytest.approx(1.0)

        # CFM to m³/s
        cfm = 2118.88  # ~1 m³/s
        m3_s = converter.convert(cfm, 'ft^3/min', 'm^3/s')
        assert m3_s == pytest.approx(1.0, abs=0.01)


@pytest.mark.verification
class TestVariableMapping:
    """Test VariableMapping class."""

    def test_create_mapping(self):
        """Test creating a variable mapping."""
        mapping = VariableMapping(
            cdl_name="TZonCooSet",
            cdl_unit="K",
            device_name="Zone_Cooling_Setpoint",
            device_unit="degF",
            description="Zone cooling setpoint temperature"
        )

        assert mapping.cdl_name == "TZonCooSet"
        assert mapping.cdl_unit == "K"
        assert mapping.device_name == "Zone_Cooling_Setpoint"
        assert mapping.device_unit == "degF"

    def test_convert_to_cdl(self):
        """Test converting device value to CDL units."""
        mapping = VariableMapping(
            cdl_name="TZonCooSet",
            cdl_unit="K",
            device_name="Zone_Cooling_Setpoint",
            device_unit="degF"
        )

        # 75°F to Kelvin
        device_value = 75.0
        cdl_value = mapping.convert_to_cdl(device_value)

        # 75°F = 297.0389 K
        assert cdl_value == pytest.approx(297.0389, abs=0.01)

    def test_convert_to_device(self):
        """Test converting CDL value to device units."""
        mapping = VariableMapping(
            cdl_name="TZonCooSet",
            cdl_unit="K",
            device_name="Zone_Cooling_Setpoint",
            device_unit="degF"
        )

        # 297.15 K to Fahrenheit
        cdl_value = 297.15
        device_value = mapping.convert_to_device(cdl_value)

        # 297.15 K ≈ 75°F
        assert device_value == pytest.approx(75.2, abs=0.1)


@pytest.mark.verification
class TestPointMapping:
    """Test PointMapping class."""

    @pytest.fixture
    def sample_point_mapping(self):
        """Create sample point mapping."""
        mappings = [
            VariableMapping(
                cdl_name="TZonCooSet",
                cdl_unit="K",
                device_name="Zone_Cooling_Setpoint",
                device_unit="degF"
            ),
            VariableMapping(
                cdl_name="TZonHeaSet",
                cdl_unit="K",
                device_name="Zone_Heating_Setpoint",
                device_unit="degF"
            ),
            VariableMapping(
                cdl_name="yValve",
                cdl_unit="fraction",
                device_name="Valve_Position",
                device_unit="percent"
            ),
        ]
        return PointMapping(mappings=mappings)

    def test_get_mapping(self, sample_point_mapping):
        """Test retrieving mapping by CDL name."""
        mapping = sample_point_mapping.get_mapping("TZonCooSet")
        assert mapping is not None
        assert mapping.device_name == "Zone_Cooling_Setpoint"

    def test_convert_dataframe_to_cdl(self, sample_point_mapping):
        """Test converting DataFrame from device to CDL units."""
        # Create device data
        device_df = pd.DataFrame({
            'Zone_Cooling_Setpoint': [75.0, 76.0, 77.0],
            'Zone_Heating_Setpoint': [68.0, 69.0, 70.0],
            'Valve_Position': [0.0, 50.0, 100.0],
        })

        # Convert to CDL units
        cdl_df = sample_point_mapping.convert_dataframe_to_cdl(device_df)

        # Check columns
        assert 'TZonCooSet' in cdl_df.columns
        assert 'TZonHeaSet' in cdl_df.columns
        assert 'yValve' in cdl_df.columns

        # Check temperature conversions (°F to K)
        assert cdl_df['TZonCooSet'].iloc[0] == pytest.approx(297.04, abs=0.1)
        assert cdl_df['TZonHeaSet'].iloc[0] == pytest.approx(293.15, abs=0.1)

        # Check valve positions (% to fraction)
        assert cdl_df['yValve'].iloc[0] == pytest.approx(0.0)
        assert cdl_df['yValve'].iloc[1] == pytest.approx(0.5)
        assert cdl_df['yValve'].iloc[2] == pytest.approx(1.0)

    def test_convert_dataframe_to_device(self, sample_point_mapping):
        """Test converting DataFrame from CDL to device units."""
        # Create CDL data
        cdl_df = pd.DataFrame({
            'TZonCooSet': [297.15, 298.15, 299.15],
            'TZonHeaSet': [293.15, 294.15, 295.15],
            'yValve': [0.0, 0.5, 1.0],
        })

        # Convert to device units
        device_df = sample_point_mapping.convert_dataframe_to_device(cdl_df)

        # Check columns
        assert 'Zone_Cooling_Setpoint' in device_df.columns
        assert 'Zone_Heating_Setpoint' in device_df.columns
        assert 'Valve_Position' in device_df.columns

        # Check temperature conversions (K to °F)
        assert device_df['Zone_Cooling_Setpoint'].iloc[0] == pytest.approx(75.2, abs=0.5)

        # Check valve positions (fraction to %)
        assert device_df['Valve_Position'].iloc[0] == pytest.approx(0.0)
        assert device_df['Valve_Position'].iloc[1] == pytest.approx(50.0)
        assert device_df['Valve_Position'].iloc[2] == pytest.approx(100.0)


@pytest.mark.verification
class TestDimensionlessUnits:
    """Test handling of dimensionless units."""

    def test_dimensionless_conversion(self, converter):
        """Test that dimensionless units pass through unchanged."""
        value = 5.0

        # All these should be equivalent
        result1 = converter.convert(value, '1', 'dimensionless')
        result2 = converter.convert(value, 'dimensionless', '1')
        result3 = converter.convert(value, '', 'dimensionless')

        assert result1 == pytest.approx(value)
        assert result2 == pytest.approx(value)
        assert result3 == pytest.approx(value)


@pytest.mark.verification
def test_obc_example_conversions():
    """Test conversions from OBC specification examples."""
    converter = UnitConverter()

    # Building 33 example: Outdoor air temperature
    # Range in data: ~60-90°F
    temp_f = 75.0  # Typical outdoor temp
    temp_k = converter.convert(temp_f, 'degF', 'K')
    assert temp_k == pytest.approx(297.04, abs=0.1)

    # Cooling coil valve position: 0-100% to 0-1 fraction
    valve_pct = 50.0
    valve_frac = converter.convert(valve_pct, 'percent', 'fraction')
    assert valve_frac == pytest.approx(0.5)

    # Supply air temperature setpoint
    sa_temp_f = 55.0  # 55°F supply air
    sa_temp_k = converter.convert(sa_temp_f, 'degF', 'K')
    assert sa_temp_k == pytest.approx(285.93, abs=0.1)


@pytest.mark.verification
def test_round_trip_conversions():
    """Test that round-trip conversions preserve values."""
    converter = UnitConverter()

    # Temperature round-trip
    original_k = 293.15
    temp_f = converter.convert(original_k, 'K', 'degF')
    back_to_k = converter.convert(temp_f, 'degF', 'K')
    assert back_to_k == pytest.approx(original_k, abs=1e-6)

    # Pressure round-trip
    original_pa = 1000.0
    pressure_psi = converter.convert(original_pa, 'Pa', 'psi')
    back_to_pa = converter.convert(pressure_psi, 'psi', 'Pa')
    assert back_to_pa == pytest.approx(original_pa, abs=0.01)

    # Percentage round-trip
    original_frac = 0.75
    pct = converter.convert(original_frac, 'fraction', 'percent')
    back_to_frac = converter.convert(pct, 'percent', 'fraction')
    assert back_to_frac == pytest.approx(original_frac, abs=1e-10)
