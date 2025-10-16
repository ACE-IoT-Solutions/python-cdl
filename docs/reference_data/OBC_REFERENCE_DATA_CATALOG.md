# OBC Reference Data Catalog

## Executive Summary

This document catalogs actual verification test data from the OpenBuildingControl (OBC) project and Modelica Buildings library that can be used for testing and validation of CDL implementations.

**Key Finding**: Real-world validation data from Building 33 at Lawrence Berkeley National Laboratory provides 3 days of 5-second timestep control data (75,564 samples) for cooling coil valve control validation.

---

## 1. Building 33 Cooling Coil Valve Data (REAL FIELD DATA)

### Overview
- **Location**: Building 33, Lawrence Berkeley National Laboratory, Berkeley, CA
- **System**: ALC EIKON controller
- **Data Period**: June 7-10, 2018 (3 days)
- **Start Time**: 2018-06-07 00:00:00 PDT (Unix: 1528354800)
- **Timestep**: 5 seconds
- **Total Samples**: 75,564 data points per variable

### Data Files

All files available at:
`https://github.com/lbl-srg/modelica-buildings/tree/master/Buildings/Resources/Data/Utilities/Plotters/Examples/ControlsVerification_CoolingCoilValve/`

#### 1.1 Cooling Coil Valve Position
- **File**: `Clg_Coil_Valve.mos`
- **URL**: https://raw.githubusercontent.com/lbl-srg/modelica-buildings/master/Buildings/Resources/Data/Utilities/Plotters/Examples/ControlsVerification_CoolingCoilValve/Clg_Coil_Valve.mos
- **Description**: Actual cooling coil valve position (0-100%)
- **Format**: MOS (Modelica Script)
- **Columns**: Seconds_Elapsed, Unix_Time, Value
- **Sample Data**:
```
0.0, 1528354800.0, 0.0
5.0, 1528354805.0, 0.0
10.0, 1528354810.0, 0.0
```

#### 1.2 Outdoor Air Temperature
- **File**: `OA_Temp.mos`
- **URL**: https://raw.githubusercontent.com/lbl-srg/modelica-buildings/master/Buildings/Resources/Data/Utilities/Plotters/Examples/ControlsVerification_CoolingCoilValve/OA_Temp.mos
- **Description**: Outdoor air temperature sensor reading
- **Units**: °F
- **Sample Values**: 50.39°F - 50.4°F (initially)
- **Sample Data**:
```
0.0, 1528354800.0, 50.389996000000004
5.0, 1528354805.0, 50.389996000000004
```

#### 1.3 Supply Air Temperature
- **File**: `Supply_Air_Temp.mos`
- **URL**: https://raw.githubusercontent.com/lbl-srg/modelica-buildings/master/Buildings/Resources/Data/Utilities/Plotters/Examples/ControlsVerification_CoolingCoilValve/Supply_Air_Temp.mos
- **Description**: Supply air temperature measurement
- **Units**: °F
- **Sample Values**: 55.0°F (constant in samples)
- **Sample Data**:
```
0.0, 1528354800.0, 55.0
5.0, 1528354805.0, 55.0
```

#### 1.4 Supply Air Cooling Setpoint
- **File**: `SA_Clg_Stpt.mos`
- **URL**: https://raw.githubusercontent.com/lbl-srg/modelica-buildings/master/Buildings/Resources/Data/Utilities/Plotters/Examples/ControlsVerification_CoolingCoilValve/SA_Clg_Stpt.mos
- **Description**: Supply air cooling temperature setpoint
- **Units**: °F
- **Sample Values**: 70.0°F (constant in samples)
- **Sample Data**:
```
0.0, 1528354800.0, 70.0
5.0, 1528354805.0, 70.0
```

#### 1.5 VFD Fan Enable
- **File**: `VFD_Fan_Enable.mos`
- **URL**: https://raw.githubusercontent.com/lbl-srg/modelica-buildings/master/Buildings/Resources/Data/Utilities/Plotters/Examples/ControlsVerification_CoolingCoilValve/VFD_Fan_Enable.mos
- **Description**: Fan enable/disable signal
- **Type**: Boolean or binary

#### 1.6 VFD Fan Feedback
- **File**: `VFD_Fan_Feedback.mos`
- **URL**: https://raw.githubusercontent.com/lbl-srg/modelica-buildings/master/Buildings/Resources/Data/Utilities/Plotters/Examples/ControlsVerification_CoolingCoilValve/VFD_Fan_Feedback.mos
- **Description**: Fan speed feedback signal

### Data Format Specification

**MOS File Structure**:
```
# Recorded trend: //mos//[filename].mos
# Columns: Seconds_Elapsed, Unix_Time, Value
double [variable_name]([num_rows], 3)
[elapsed_seconds], [unix_timestamp], [value]
[elapsed_seconds], [unix_timestamp], [value]
...
```

### Conversion Tool

**File**: `csv2mos.py`
**URL**: https://raw.githubusercontent.com/lbl-srg/modelica-buildings/master/Buildings/Resources/Data/Utilities/Plotters/Examples/ControlsVerification_CoolingCoilValve/csv2mos.py

**Purpose**: Converts CSV time-series data to MOS format

**Expected CSV Input Format**:
- Column 1: "Date" (timestamp string)
- Column 2: "Excel Time" (optional)
- Column 3: "Value" (numeric data)
- Column 4: "Notes" (optional)

**Usage Example**:
```python
from csv2mos import trend_data_csv2mos

inpath = "//csv//OA Temp.csv"
mospath = "//mos//"
starting_timestamp = "6/7/2018 00:00:00 PDT"
trend_data_csv2mos(inpath, mospath, starting_timestamp)
```

**Conversion Process**:
1. Reads CSV with timestamp and value columns
2. Converts timestamps to Unix time
3. Calculates elapsed seconds from start time
4. Outputs MOS format with (elapsed, unix_time, value)

### Control Logic Description

The validated sequence includes:
1. **PI Controller**: Tracks supply air temperature setpoint
2. **Enable Logic**: Upstream subsequence that enables the controller
3. **Output Limiter**: Downstream limiter active during low supply air temperatures

---

## 2. OBC Verification Software Configuration

### Repository
**URL**: https://github.com/lbl-srg/obc/tree/master/software/verification

### 2.1 Configuration Files

#### config.json (Production Configuration)
**URL**: https://github.com/lbl-srg/obc/blob/master/software/verification/config.json

**Structure**:
```json
{
  "references": [
    {
      "model": "Buildings.Controls.OBC.ASHRAE.G36_PR1.AHUs.SingleZone.VAV.SetPoints.Validation.Supply_u",
      "generateJson": false,
      "sequence": "setPoiVAV",
      "pointNameMapping": "realControllerPointMapping.json",
      "runController": false,
      "controllerOutput": "test/real_outputs.csv"
    },
    {
      "model": "Buildings.Controls.OBC.ASHRAE.G36_PR1.TerminalUnits.SetPoints.Validation.ZoneTemperatures",
      "generateJson": true,
      "sequence": "TZonSet",
      "pointNameMapping": "realControllerPointMapping.json",
      "runController": true,
      "controllerOutput": "test/real_outputs.csv",
      "outputs": {
        "TZonSet.TZon*": { "atoly": 0.5 }
      },
      "indicators": {
        "TZonSet.TZon*": [ "uOccSen" ]
      },
      "sampling": 60
    }
  ],
  "modelJsonDirectory": "test",
  "tolerances": {
    "rtolx": 0.002,
    "rtoly": 0.002,
    "atolx": 10,
    "atoly": 0
  },
  "sampling": 120,
  "controller": {
    "networkAddress": "192.168.0.115/24",
    "deviceAddress": "192.168.0.227",
    "deviceId": 240001
  }
}
```

#### config_test.json (Test Configuration)
**URL**: https://github.com/lbl-srg/obc/blob/master/software/verification/config_test.json

**Structure**:
```json
{
    "references": [
        {
            "model": "Buildings.Controls.OBC.ASHRAE.G36_PR1.TerminalUnits.SetPoints.Validation.ZoneTemperatures",
            "generateJson": true,
            "sequence": "TZonSet",
            "pointNameMapping": "realControllerPointMapping.json",
            "runController": false,
            "controllerOutput": "test/real_outputs.csv",
            "outputs": {
                "TZonSet.TZon*": { "atoly": 0.5 }
            },
            "indicators": {
                "TZonSet.TZon*": [ "TZonSet.uOccSen" ]
            },
            "sampling": 60
        }
    ],
    "modelJsonDirectory": "test",
    "tolerances": {
        "rtolx": 0.002,
        "rtoly": 0.002,
        "atolx": 10,
        "atoly": 2
    },
    "sampling": 120
}
```

**Key Difference**: `runController: false` in test config (no live controller required)

### 2.2 Point Mapping Configuration

**File**: `realControllerPointMapping.json`
**URL**: https://github.com/lbl-srg/obc/blob/master/software/verification/realControllerPointMapping.json

**Purpose**: Maps CDL point names/units to real controller point names/units

**Example Mappings**:
```json
[
  {
    "cdl": {
      "name": "TZonCooSetOcc",
      "unit": "K",
      "type": "float"
    },
    "device": {
      "name": "Occupied Cooling Setpoint_1",
      "unit": "degF",
      "type": "float"
    }
  },
  {
    "cdl": {
      "name": "TZonHeaSetOcc",
      "unit": "K",
      "type": "float"
    },
    "device": {
      "name": "Occupied Heating Setpoint_1",
      "unit": "degF",
      "type": "float"
    }
  },
  {
    "cdl": {
      "name": "uOccSen",
      "unit": "1",
      "type": "bool"
    },
    "device": {
      "name": "Occupancy Sensor_1",
      "unit": "1",
      "type": "bool"
    }
  }
]
```

**Mapped Points Include**:
- Occupied Cooling/Heating Setpoints
- Unoccupied Cooling/Heating Setpoints
- Setpoint Adjustment
- Occupancy Sensor
- Window Status
- Effective Cooling/Heating Setpoints

### 2.3 Test Data Files

**Directory**: https://github.com/lbl-srg/obc/tree/master/software/verification/test

#### real_outputs.csv
**URL**: https://raw.githubusercontent.com/lbl-srg/obc/master/software/verification/test/real_outputs.csv

**Format**:
```csv
time,TZonSet.TZonCooSet,TZonSet.TZonHeaSet
0.11976385116577148,299.3722162882487,290.92777353922526
2.260979175567627,299.3722162882487,290.92777353922526
4.397479057312012,299.3722162882487,290.92777353922526
```

**Columns**:
- `time`: Simulation time (seconds)
- `TZonSet.TZonCooSet`: Zone cooling setpoint (K)
- `TZonSet.TZonHeaSet`: Zone heating setpoint (K)

#### Model JSON Definition
**File**: `Buildings.Controls.OBC.ASHRAE.G36_PR1.AHUs.SingleZone.VAV.SetPoints.Validation.Supply_u.json`

**Model Components**:
- Supply setpoint controllers (setPoiVAV, setPoiVAV1, setPoiVAV2)
- Constant sources for zone/outdoor temperatures
- Ramp sources for heating/cooling signals
- Configuration parameters:
  - Max heating signal: 0.7
  - Min fan speed: 0.3
  - Max supply temp: 303.15 K
  - Min supply temp: 289.15 K

---

## 3. Modelica Buildings Library Reference Results

### Repository Structure
**Base URL**: https://github.com/lbl-srg/modelica-buildings

### Reference Results Location
**Path**: `Buildings/Resources/ReferenceResults/Dymola/`

### 3.1 Available Validation Categories

#### ASHRAE G36 Controls
- **MultiZone VAV**: Economizers, SetPoints, Freeze Protection
- **SingleZone VAV**: Economizers, SetPoints, Supply Fan Control
- **Terminal Units**:
  - Cooling Only
  - Dual Duct (Snap Acting, Mixing)
  - Parallel Fan
  - Series Fan
  - Reheat
  - VAV Boxes

#### Control Description Language (CDL)
- Continuous Controls
- Discrete Controls
- Integer Controls
- Logical Controls
- Routing Controls
- Conversions
- Psychrometrics

#### Specific Control Sequences
- Active Airflow Setpoints
- Damper Controls
- Alarm Logic
- System Requests
- Zone State Tracking
- Trim and Respond Logic

### 3.2 Reference Result File Format

**File Type**: `.txt` files (CSV-like format)
**Location Pattern**: `Buildings/Resources/ReferenceResults/Dymola/Buildings_Controls_OBC_[...]_Validation_[test_name].txt`

**Example Files**:
```
Buildings_Controls_OBC_ASHRAE_G36_PR1_AHUs_SingleZone_VAV_SetPoints_Validation_Supply_u.txt
Buildings_Controls_OBC_ASHRAE_G36_PR1_TerminalUnits_SetPoints_Validation_ZoneTemperatures.txt
Buildings_Controls_OBC_CDL_Continuous_Validation_LimPID.txt
```

### 3.3 Accessing Reference Results

**Method 1: Clone Repository**
```bash
git clone https://github.com/lbl-srg/modelica-buildings.git
cd modelica-buildings/Buildings/Resources/ReferenceResults/Dymola/
```

**Method 2: Download Release**
- Latest Release: https://github.com/lbl-srg/modelica-buildings/releases
- Extract and navigate to `Buildings/Resources/ReferenceResults/Dymola/`

**Method 3: Direct Raw File Access**
```
https://raw.githubusercontent.com/lbl-srg/modelica-buildings/master/Buildings/Resources/ReferenceResults/Dymola/[filename].txt
```

---

## 4. Test Scenarios We Can Use

### 4.1 P-Controller Examples

**Source**: CDL Continuous Controls Validation

**Models Available**:
- `Buildings.Controls.OBC.CDL.Continuous.Validation.PID`
- `Buildings.Controls.OBC.CDL.Continuous.Validation.LimPID`
- PI controller with limits and anti-windup

**Test Characteristics**:
- Simple ramp and step inputs
- Known analytical solutions
- Tolerance-based validation
- Unit conversion examples

### 4.2 VAV Zone Controller Examples

**Primary Test**: `Buildings.Controls.OBC.ASHRAE.G36_PR1.TerminalUnits.SetPoints.Validation.ZoneTemperatures`

**Available in**:
- config_test.json (reference configuration)
- real_outputs.csv (sample output data)

**Test Parameters**:
- Sampling: 60 seconds
- Output tolerance (atoly): 0.5 K
- Indicators: Occupancy sensor (uOccSen)
- Outputs: Zone cooling/heating setpoints

**Input Variables**:
- Zone temperature
- Occupancy status
- Window status
- Time of day

**Output Variables**:
- Zone cooling setpoint
- Zone heating setpoint
- Effective setpoints

### 4.3 Cooling Coil Sequence Examples

**Real-World Test**: Building 33 Cooling Coil Valve

**Control Logic**:
1. Read supply air temperature
2. Read supply air temperature setpoint
3. Calculate error
4. PI controller computes valve position
5. Apply output limits based on conditions
6. Enable/disable based on fan status

**Test Inputs Available**:
- Outdoor air temperature (5s resolution, 3 days)
- Supply air temperature (5s resolution, 3 days)
- Supply air cooling setpoint (5s resolution, 3 days)
- VFD fan enable status (5s resolution, 3 days)
- VFD fan feedback (5s resolution, 3 days)

**Test Output Available**:
- Cooling coil valve position (5s resolution, 3 days)

**Validation Method**:
- Compare actual valve position vs CDL-computed position
- Use "funnel" tolerance checking
- Configurable time and value tolerances

### 4.4 Single Zone VAV AHU Example

**Model**: `Buildings.Controls.OBC.ASHRAE.G36_PR1.AHUs.SingleZone.VAV.SetPoints.Validation.Supply_u`

**Test Configuration**:
- Max heating signal: 0.7
- Min fan speed: 0.3
- Max supply temp: 303.15 K (86°F)
- Min supply temp: 289.15 K (61°F)

**Available Test Data**:
- JSON model definition
- Reference results in Dymola format

---

## 5. Data Format Notes and Limitations

### 5.1 MOS Format (Modelica Script)

**Advantages**:
- Native format for Modelica simulations
- Includes metadata (array dimensions)
- Three-column structure clear and simple

**Limitations**:
- Not standard CSV (requires parsing)
- Header format specific to Modelica tools
- May need conversion for Python tools

**Conversion Strategy**:
- Use provided csv2mos.py script (reverse it)
- Parse as space-delimited, skip header
- Extract columns: elapsed_time, unix_time, value

### 5.2 CSV Format

**OBC real_outputs.csv**:
- Standard CSV with header row
- Time in seconds (floating point)
- SI units (Kelvin for temperatures)
- Compatible with pandas, numpy

### 5.3 Tolerance Specifications

**Configuration Parameters**:
```json
"tolerances": {
  "rtolx": 0.002,  // Relative tolerance in time (0.2%)
  "rtoly": 0.002,  // Relative tolerance in output (0.2%)
  "atolx": 10,     // Absolute tolerance in time (seconds)
  "atoly": 0       // Absolute tolerance in output
}
```

**Per-Output Overrides**:
```json
"outputs": {
  "TZonSet.TZon*": { "atoly": 0.5 }  // 0.5 K tolerance for zone temps
}
```

### 5.4 Unit Conversions

**Common Conversions Needed**:
- °F ↔ K: K = (°F - 32) × 5/9 + 273.15
- °F ↔ °C: °C = (°F - 32) × 5/9
- Percentage (0-100) ↔ Fraction (0-1)

**Point Mapping**:
- CDL uses SI units (K, kg/s, Pa)
- Controllers often use Imperial (°F, CFM, inH2O)
- Point mapping JSON provides conversion info

### 5.5 Sampling Considerations

**Building 33 Data**:
- 5-second timestep = 0.2 Hz sampling
- High resolution for control loop analysis
- 3 days = ~260,000 seconds = 52,000 samples per variable

**OBC Test Data**:
- 60-second sampling for zone temps
- 120-second sampling for other variables
- Lower resolution suitable for setpoint validation

**Recommendation**: Use 5-second data for control loop tuning, 60-120 second data for setpoint logic validation

---

## 6. Download Checklist and URLs

### 6.1 Building 33 Data (All Files)

Create download script:
```bash
#!/bin/bash
BASE_URL="https://raw.githubusercontent.com/lbl-srg/modelica-buildings/master/Buildings/Resources/Data/Utilities/Plotters/Examples/ControlsVerification_CoolingCoilValve/"

wget ${BASE_URL}Clg_Coil_Valve.mos
wget ${BASE_URL}OA_Temp.mos
wget ${BASE_URL}Supply_Air_Temp.mos
wget ${BASE_URL}SA_Clg_Stpt.mos
wget ${BASE_URL}VFD_Fan_Enable.mos
wget ${BASE_URL}VFD_Fan_Feedback.mos
wget ${BASE_URL}csv2mos.py
```

### 6.2 OBC Verification Files

```bash
BASE_URL="https://raw.githubusercontent.com/lbl-srg/obc/master/software/verification/"

wget ${BASE_URL}config.json
wget ${BASE_URL}config_test.json
wget ${BASE_URL}realControllerPointMapping.json
wget ${BASE_URL}test/real_outputs.csv
wget ${BASE_URL}test/Buildings.Controls.OBC.ASHRAE.G36_PR1.AHUs.SingleZone.VAV.SetPoints.Validation.Supply_u.json
```

### 6.3 Modelica Buildings Library (Full)

**Option 1: Latest Release**
```bash
wget https://github.com/lbl-srg/modelica-buildings/archive/refs/tags/v11.1.0.zip
unzip v11.1.0.zip
```

**Option 2: Development Version**
```bash
git clone https://github.com/lbl-srg/modelica-buildings.git
```

**Option 3: Specific Reference Results Only**
```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/lbl-srg/modelica-buildings.git
cd modelica-buildings
git sparse-checkout set Buildings/Resources/ReferenceResults
```

---

## 7. Recommended Test Implementation Strategy

### Phase 1: Simple P-Controller
1. Use synthetic data (ramps, steps)
2. Validate against analytical solution
3. Implement tolerance checking
4. Test unit conversions

### Phase 2: Zone Temperature Setpoints
1. Use real_outputs.csv as reference
2. Implement config_test.json scenario
3. Validate ZoneTemperatures model
4. Test point mapping functionality

### Phase 3: Cooling Coil Validation
1. Convert Building 33 MOS files to CSV
2. Implement PI controller with limits
3. Compare outputs using funnel method
4. Analyze 3-day performance

### Phase 4: Full VAV System
1. Use complete Buildings library reference results
2. Test multi-zone scenarios
3. Validate economizer sequences
4. Integrate with OpenModelica

---

## 8. Additional Resources

### Documentation
- OBC Specification: https://obc.lbl.gov/specification/
- CDL Documentation: https://obc.lbl.gov/specification/cdl.html
- Verification Guide: https://obc.lbl.gov/specification/verification.html
- Buildings Library User Guide: https://simulationresearch.lbl.gov/modelica/releases/latest/help/Buildings_UsersGuide.html

### Tools
- OpenModelica: https://openmodelica.org/
- Buildings Library: https://simulationresearch.lbl.gov/modelica/
- OBC Verification Software: https://github.com/lbl-srg/obc/tree/master/software/verification

### Support
- Buildings Library Issues: https://github.com/lbl-srg/modelica-buildings/issues
- OBC Issues: https://github.com/lbl-srg/obc/issues

---

## 9. Summary Statistics

### Data Availability
- **Real field data**: 6 variables × 75,564 samples = 453,384 data points
- **Reference results**: 200+ validation test files
- **Configuration examples**: 2 complete configs + point mapping
- **Test scenarios**: 4+ ready-to-use scenarios

### Data Quality
- **Temporal resolution**: 5 seconds (high-quality control data)
- **Duration**: 3 days continuous operation
- **Source**: Validated field installation (Building 33, LBNL)
- **Controller**: Commercial system (ALC EIKON)

### Recommended Starting Point
**File**: `real_outputs.csv` from OBC verification test suite
**Reason**:
- Standard CSV format
- Simple 3-column structure
- Well-documented test configuration
- No controller connection required
- Representative of typical validation workflow

---

## Appendix: Quick Start Commands

### Download Essential Files Only
```bash
mkdir -p obc_reference_data
cd obc_reference_data

# Building 33 cooling coil data
wget -P building33/ https://raw.githubusercontent.com/lbl-srg/modelica-buildings/master/Buildings/Resources/Data/Utilities/Plotters/Examples/ControlsVerification_CoolingCoilValve/Clg_Coil_Valve.mos
wget -P building33/ https://raw.githubusercontent.com/lbl-srg/modelica-buildings/master/Buildings/Resources/Data/Utilities/Plotters/Examples/ControlsVerification_CoolingCoilValve/OA_Temp.mos
wget -P building33/ https://raw.githubusercontent.com/lbl-srg/modelica-buildings/master/Buildings/Resources/Data/Utilities/Plotters/Examples/ControlsVerification_CoolingCoilValve/Supply_Air_Temp.mos

# OBC test configuration
wget -P obc_test/ https://raw.githubusercontent.com/lbl-srg/obc/master/software/verification/config_test.json
wget -P obc_test/ https://raw.githubusercontent.com/lbl-srg/obc/master/software/verification/realControllerPointMapping.json
wget -P obc_test/ https://raw.githubusercontent.com/lbl-srg/obc/master/software/verification/test/real_outputs.csv
```

### Convert MOS to CSV (Python)
```python
import pandas as pd

def mos_to_csv(mos_file, csv_file):
    """Convert MOS file to standard CSV"""
    data = []
    with open(mos_file, 'r') as f:
        for line in f:
            if line.startswith('#') or line.startswith('double'):
                continue
            parts = line.strip().split(',')
            if len(parts) == 3:
                data.append([float(x) for x in parts])

    df = pd.DataFrame(data, columns=['elapsed_sec', 'unix_time', 'value'])
    df.to_csv(csv_file, index=False)
    return df

# Usage
df = mos_to_csv('Clg_Coil_Valve.mos', 'cooling_coil_valve.csv')
print(df.head())
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-16
**Author**: Research Agent (Hive Mind Swarm)
**Data Sources**: LBL-SRG GitHub Repositories (obc, modelica-buildings)
