# Verification Reference Data

This directory contains reference time-series data for verification testing.

## Directory Structure

```
reference_data/
├── README.md (this file)
├── elementary/          # Reference data for elementary blocks
├── composite/           # Reference data for composite blocks
└── control_flow/        # Reference data for control flow blocks
```

## Data Format

### CSV Format

CSV files should have the following structure:
- First column: `time` (time points)
- Subsequent columns: variable values
- Header row with column names

Example:
```csv
time,input_u,output_y
0.0,0.0,0.0
0.1,1.0,0.5
0.2,2.0,1.0
```

### JSON Format

JSON files should follow this structure:
```json
{
  "time": [0.0, 0.1, 0.2],
  "variables": {
    "input_u": [0.0, 1.0, 2.0],
    "output_y": [0.0, 0.5, 1.0]
  },
  "metadata": {
    "source": "Modelica.Blocks.Continuous.Limiter",
    "tool": "OpenModelica 1.21.0",
    "date": "2024-01-15"
  }
}
```

## Generating Reference Data

Reference data can be generated from:

1. **Modelica**: Export simulation results as CSV
   - Use `experimentSetupFile` with CSV output
   - Or use OMPython to run simulations programmatically

2. **MATLAB/Simulink**: Export to CSV or MAT files

3. **Python**: Generate analytical solutions for simple test cases

## Naming Convention

Use descriptive names that indicate the block type and test scenario:
- `limiter_basic.csv` - Basic test of Limiter block
- `pid_step_response.json` - PID controller step response
- `sequence_nested.csv` - Nested sequence blocks

## Metadata

Include metadata in JSON files or separate `*.meta.json` files:
- Source tool and version
- Date generated
- Test scenario description
- Expected behavior notes
- Known issues or limitations
