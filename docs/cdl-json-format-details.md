# CDL-JSON Format Detailed Specification

## Overview

CDL-JSON is an intermediate JSON representation of Controls Description Language (CDL) control sequences. It serves as a bridge between the human-readable CDL (Modelica subset) and various target formats including building automation systems, documentation, and semantic models.

## Translation Workflow

```
┌──────────────┐
│  CDL (.mo)   │  Human-readable control sequences
└──────┬───────┘
       │
       │ modelica-json translator
       ↓
┌──────────────┐
│  CDL-JSON    │  Machine-readable intermediate format
└──────┬───────┘
       │
       ├─→ Building Automation Systems
       ├─→ Point Lists
       ├─→ Documentation (HTML)
       ├─→ Semantic Models
       └─→ CXF (JSON-LD)
```

## Schema Definition

### Schema Location
- **Repository**: https://github.com/lbl-srg/modelica-json
- **Schema File**: `schema-cdl.json`
- **Purpose**: Defines structure, constraints, and validation rules for CDL-JSON

### Schema Validation
```bash
# Validate existing JSON file
node modelica-json/validation.js -f filename.json
```

## JSON Output Formats

### 1. Raw JSON
**Description**: Complete representation with all metadata and details

**Use Case**: Full fidelity translation, debugging, comprehensive analysis

**Characteristics**:
- All block properties preserved
- Complete metadata included
- Annotations retained
- Nested structure maintained

### 2. Simplified JSON
**Description**: Streamlined format optimized for parsing and implementation

**Use Case**: Building automation system integration, code generation

**Characteristics**:
- Reduced metadata
- Flattened where appropriate
- Essential properties only
- Easier to parse programmatically

**Generation**:
```bash
node modelica-json/app.js -f CustomPWithLimiter.mo -o json-simplified
```

### 3. Semantic Model
**Description**: RDF/linked-data representation for semantic web applications

**Use Case**: Knowledge graphs, semantic queries, ontology integration

**Characteristics**:
- RDF triple format
- Linked data compatible
- Ontology-based
- SPARQL queryable

## CDL-JSON Structure

### Top-Level Structure
```json
{
  "modelicaFile": "path/to/file.mo",
  "within": "PackageName",
  "topClassName": "ControlSequenceName",
  "comment": "Description of the control sequence",
  "public": {
    "parameters": [...],
    "inputs": [...],
    "outputs": [...],
    "instances": [...]
  },
  "protected": {...},
  "equations": [...]
}
```

### Block Representation

#### Elementary Block
```json
{
  "className": "CDL.Continuous.Add",
  "name": "add1",
  "comment": "Sum of two inputs",
  "modifications": {
    "parameters": [
      {
        "name": "k1",
        "value": 1.0
      },
      {
        "name": "k2",
        "value": 1.0
      }
    ]
  }
}
```

#### Composite Block
```json
{
  "className": "MyPackage.CustomController",
  "name": "controller1",
  "comment": "Custom PID controller with limits",
  "instances": [
    {
      "className": "CDL.Continuous.PID",
      "name": "pid",
      "modifications": {...}
    },
    {
      "className": "CDL.Continuous.Limiter",
      "name": "limiter",
      "modifications": {...}
    }
  ],
  "connections": [...]
}
```

### Connector Representation

#### Input Connector
```json
{
  "type": "input",
  "dataType": "Real",
  "name": "u",
  "comment": "Input signal",
  "unit": "K",
  "quantity": "Temperature",
  "min": -273.15,
  "max": null
}
```

#### Output Connector
```json
{
  "type": "output",
  "dataType": "Boolean",
  "name": "y",
  "comment": "Control signal",
  "start": false
}
```

### Parameter Representation
```json
{
  "name": "k",
  "dataType": "Real",
  "value": 1.0,
  "comment": "Proportional gain",
  "unit": "1",
  "min": 0,
  "max": null,
  "final": false,
  "fixed": true
}
```

### Connection Representation
```json
{
  "from": "pid.y",
  "to": "limiter.u",
  "comment": "Connect PID output to limiter input"
}
```

## Data Types

### Real (Floating-Point)
```json
{
  "dataType": "Real",
  "value": 23.5,
  "unit": "degC",
  "quantity": "Temperature",
  "displayUnit": "degF",
  "min": -273.15,
  "max": 100.0,
  "start": 20.0,
  "nominal": 20.0
}
```

**Attributes**:
- `unit`: Physical unit (SI or compatible)
- `quantity`: Physical quantity type
- `displayUnit`: Preferred display unit
- `min`/`max`: Valid range
- `start`: Initial value
- `nominal`: Nominal/expected value

### Boolean
```json
{
  "dataType": "Boolean",
  "value": true,
  "start": false
}
```

**Attributes**:
- `start`: Initial value

### Integer
```json
{
  "dataType": "Integer",
  "value": 5,
  "min": 0,
  "max": 10,
  "start": 0
}
```

**Attributes**:
- `min`/`max`: Valid range
- `start`: Initial value

### Enumeration
```json
{
  "dataType": "Enumeration",
  "typeName": "ControlMode",
  "values": ["Off", "Heating", "Cooling"],
  "value": "Off",
  "start": "Off"
}
```

## Array Handling

### Multidimensional Arrays
**Option 1: Preserve Structure**
```json
{
  "name": "matrix",
  "dataType": "Real",
  "dimensions": [3, 2],
  "value": [
    [1.0, 2.0],
    [3.0, 4.0],
    [5.0, 6.0]
  ]
}
```

**Option 2: Flatten (Row-Major)**
```json
{
  "name": "matrix_flat",
  "dataType": "Real",
  "dimensions": [3, 2],
  "value": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
}
```

### Array Indexing
- **Zero-based**: JSON uses zero-based indexing
- **Modelica**: Uses one-based indexing
- **Translation**: Automatic conversion required

## Expression Handling

### Option 1: Preserve Expression
```json
{
  "name": "result",
  "expression": "k * (u1 + u2) / 2.0"
}
```

### Option 2: Evaluate Expression
```json
{
  "name": "result",
  "value": 12.5,
  "evaluatedFrom": "k * (u1 + u2) / 2.0"
}
```

**Considerations**:
- Variable references in expressions
- Parameter dependencies
- Evaluation context

## Metadata Support

### Translation Metadata
```json
{
  "metadata": {
    "translator": "modelica-json",
    "version": "2.0.0",
    "translationDate": "2025-10-15T12:00:00Z",
    "sourceFile": "path/to/source.mo",
    "targetFormat": "json-simplified"
  }
}
```

### Vendor Annotations
```json
{
  "annotations": {
    "vendor": "VendorName",
    "productLine": "ProductX",
    "customProperties": {
      "nodeId": "12345",
      "priority": "high"
    }
  }
}
```

### Documentation Metadata
```json
{
  "documentation": {
    "info": "<html>Detailed description...</html>",
    "revisions": [
      {
        "date": "2025-01-15",
        "author": "John Doe",
        "comment": "Initial version"
      }
    ]
  }
}
```

## Translation Examples

### Example 1: Simple Gain Block

**CDL Input (CustomGain.mo):**
```modelica
block CustomGain "Gain with limits"
  parameter Real k=1.0 "Gain value";
  input Real u "Input signal";
  input Real yMax "Maximum output";
  output Real y "Output signal";
equation
  y = min(yMax, k*u);
end CustomGain;
```

**JSON Output (Simplified):**
```json
{
  "modelicaFile": "CustomGain.mo",
  "topClassName": "CustomGain",
  "comment": "Gain with limits",
  "public": {
    "parameters": [
      {
        "name": "k",
        "dataType": "Real",
        "value": 1.0,
        "comment": "Gain value"
      }
    ],
    "inputs": [
      {
        "name": "u",
        "dataType": "Real",
        "comment": "Input signal"
      },
      {
        "name": "yMax",
        "dataType": "Real",
        "comment": "Maximum output"
      }
    ],
    "outputs": [
      {
        "name": "y",
        "dataType": "Real",
        "comment": "Output signal"
      }
    ]
  },
  "equations": [
    {
      "lhs": "y",
      "rhs": "min(yMax, k*u)"
    }
  ]
}
```

### Example 2: Composite Block with Instances

**CDL Input (PIDWithLimiter.mo):**
```modelica
block PIDWithLimiter "PID controller with output limiting"
  parameter Real k=1.0 "Proportional gain";
  parameter Real Ti=1.0 "Integrator time constant";
  parameter Real yMax=1.0 "Maximum output";
  parameter Real yMin=0.0 "Minimum output";

  input Real u_s "Setpoint";
  input Real u_m "Measured value";
  output Real y "Control signal";

  CDL.Continuous.PID pid(k=k, Ti=Ti);
  CDL.Continuous.Limiter limiter(uMax=yMax, uMin=yMin);
equation
  connect(u_s, pid.u_s);
  connect(u_m, pid.u_m);
  connect(pid.y, limiter.u);
  connect(limiter.y, y);
end PIDWithLimiter;
```

**JSON Output (Simplified):**
```json
{
  "modelicaFile": "PIDWithLimiter.mo",
  "topClassName": "PIDWithLimiter",
  "comment": "PID controller with output limiting",
  "public": {
    "parameters": [
      {"name": "k", "dataType": "Real", "value": 1.0},
      {"name": "Ti", "dataType": "Real", "value": 1.0},
      {"name": "yMax", "dataType": "Real", "value": 1.0},
      {"name": "yMin", "dataType": "Real", "value": 0.0}
    ],
    "inputs": [
      {"name": "u_s", "dataType": "Real", "comment": "Setpoint"},
      {"name": "u_m", "dataType": "Real", "comment": "Measured value"}
    ],
    "outputs": [
      {"name": "y", "dataType": "Real", "comment": "Control signal"}
    ],
    "instances": [
      {
        "className": "CDL.Continuous.PID",
        "name": "pid",
        "modifications": {
          "k": 1.0,
          "Ti": 1.0
        }
      },
      {
        "className": "CDL.Continuous.Limiter",
        "name": "limiter",
        "modifications": {
          "uMax": 1.0,
          "uMin": 0.0
        }
      }
    ]
  },
  "connections": [
    {"from": "u_s", "to": "pid.u_s"},
    {"from": "u_m", "to": "pid.u_m"},
    {"from": "pid.y", "to": "limiter.u"},
    {"from": "limiter.y", "to": "y"}
  ]
}
```

## Python Implementation Considerations

### JSON Parsing
```python
import json
from pathlib import Path

def load_cdl_json(file_path: Path) -> dict:
    """Load and parse CDL-JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)

def validate_cdl_json(cdl_json: dict, schema_path: Path) -> bool:
    """Validate CDL-JSON against schema"""
    import jsonschema

    with open(schema_path, 'r') as f:
        schema = json.load(f)

    try:
        jsonschema.validate(cdl_json, schema)
        return True
    except jsonschema.ValidationError as e:
        print(f"Validation error: {e.message}")
        return False
```

### Pydantic Models
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Union, Literal

class CDLConnector(BaseModel):
    name: str
    dataType: Literal["Real", "Boolean", "Integer"]
    comment: Optional[str] = None
    unit: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None
    start: Optional[Union[float, bool, int]] = None

class CDLParameter(BaseModel):
    name: str
    dataType: Literal["Real", "Boolean", "Integer"]
    value: Union[float, bool, int]
    comment: Optional[str] = None
    unit: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None

class CDLInstance(BaseModel):
    className: str
    name: str
    comment: Optional[str] = None
    modifications: Optional[dict] = None

class CDLConnection(BaseModel):
    from_: str = Field(..., alias="from")
    to: str
    comment: Optional[str] = None

class CDLBlockJSON(BaseModel):
    modelicaFile: str
    topClassName: str
    comment: Optional[str] = None
    public: dict
    protected: Optional[dict] = None
    equations: Optional[List[dict]] = None
    connections: Optional[List[CDLConnection]] = None

# Usage
cdl_data = load_cdl_json(Path("control_sequence.json"))
block = CDLBlockJSON(**cdl_data)
```

### Serialization
```python
def block_to_json(block: CDLBlock) -> dict:
    """Convert CDL block to JSON representation"""
    return {
        "modelicaFile": block.source_file,
        "topClassName": block.name,
        "comment": block.description,
        "public": {
            "parameters": [p.to_json() for p in block.parameters],
            "inputs": [i.to_json() for i in block.inputs],
            "outputs": [o.to_json() for o in block.outputs],
            "instances": [inst.to_json() for inst in block.instances]
        },
        "connections": [c.to_json() for c in block.connections]
    }

def save_cdl_json(block: CDLBlock, output_path: Path):
    """Save CDL block as JSON file"""
    json_data = block_to_json(block)
    with open(output_path, 'w') as f:
        json.dump(json_data, f, indent=2)
```

## Best Practices

### 1. Validation
- Always validate against schema before processing
- Check for required fields
- Verify data type consistency
- Validate connection references

### 2. Error Handling
- Provide clear error messages
- Include source location information
- Validate before translation
- Log warnings for non-critical issues

### 3. Metadata Preservation
- Maintain documentation strings
- Preserve vendor annotations
- Include translation metadata
- Track source file references

### 4. Performance
- Stream large files when possible
- Use efficient JSON parsing
- Cache schema validation
- Optimize for repeated translations

### 5. Compatibility
- Support multiple schema versions
- Handle optional fields gracefully
- Provide migration tools
- Document format changes

## Common Pitfalls

### 1. Array Indexing
**Problem**: Modelica uses 1-based, JSON uses 0-based
**Solution**: Explicit conversion functions

### 2. Expression References
**Problem**: Unresolved variable references in expressions
**Solution**: Maintain symbol table during parsing

### 3. Type Mismatches
**Problem**: Incompatible type assignments
**Solution**: Strict type checking and validation

### 4. Missing Connections
**Problem**: Dangling input/output references
**Solution**: Connection graph validation

### 5. Schema Compliance
**Problem**: Invalid JSON structure
**Solution**: Schema validation before export

## Resources

- **Schema Repository**: https://github.com/lbl-srg/modelica-json
- **CDL Specification**: https://obc.lbl.gov/specification/cdl.html
- **JSON Schema Validator**: https://json-schema.org/
- **Modelica Specification**: https://modelica.org/documents/

## Summary

CDL-JSON provides a robust intermediate format for control sequence translation. Python implementation should focus on:

1. **Schema compliance** using jsonschema validation
2. **Type safety** with Pydantic models
3. **Efficient parsing** for large sequences
4. **Complete metadata** preservation
5. **Clear error messages** for debugging

The format enables seamless integration with building automation systems while maintaining standards compliance and vendor independence.
