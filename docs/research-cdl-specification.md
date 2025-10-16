# CDL Specification Research Report

## Executive Summary

The Controls Description Language (CDL) is a declarative, block-diagram-based language for expressing control sequences in building automation systems. It is being standardized through ASHRAE Standard 231P and designed to enable vendor-independent control logic representation.

## 1. CDL Specification Overview

### Purpose and Design Goals
- **Vendor Independence**: Enable control logic sharing across different building automation systems
- **Declarative Approach**: Express "what" should happen rather than "how"
- **Reusability**: Support hierarchical modeling and reuse of preconfigured control sequences
- **Interoperability**: Support translation between control systems via intermediate formats

### Core Language Features
- Based on subset of Modelica modeling language
- Synchronous data flow computation model
- Single assignment rule for variables
- Typed connectors (Real, Boolean, Integer)
- Strict connection rules between inputs/outputs
- Metadata support for semantic information

## 2. CDL Block Architecture

### Block Types

#### Elementary Blocks
- Built-in, predefined computational blocks
- Over 130 elementary functions (Add, PID, Min, Max, etc.)
- Cannot be decomposed into smaller blocks
- Implementation details are platform-specific

#### Composite Blocks
- Hierarchically composed using elementary blocks
- Reusable control sequence patterns
- Defined using CDL syntax
- Explicit composition via equation sections

#### Extension Blocks
- Allow implementation of complex functionality
- Used when composite blocks are insufficient
- Can include platform-specific implementations

### Block Structure
```modelica
block ExampleBlock
  parameter Real k "Gain parameter";
  input Real e "Error signal";
  input Real yMax "Maximum output";
  output Real y "Output signal";
equation
  y = min(yMax, k*e);
end ExampleBlock;
```

## 3. Control Flow Semantics

### Execution Model
- **Event-based**: Computation occurs at discrete event instants
- **Zero-time computation**: Events take no simulation time
- **Value persistence**: Variables maintain values between events
- **Acyclic dependency**: Directed, acyclic graph required between inputs/outputs

### Connection Rules
- Inputs must be connected to exactly one output
- Outputs can connect to multiple inputs
- Type compatibility enforced at connections
- No algebraic loops permitted

### Data Types
- **Real**: Floating-point numbers
- **Boolean**: True/false values
- **Integer**: Whole numbers
- **Enumeration**: Named discrete values

## 4. CDL-JSON Format

### Translation Architecture
```
CDL (.mo files) → modelica-json → CDL-JSON → Target Systems
                                          ↓
                              Point Lists, Documentation, Semantic Models
```

### JSON Schema
- Schema location: https://github.com/lbl-srg/modelica-json/blob/master/schema-cdl.json
- Validates JSON representation structure
- Defines required/optional properties
- Ensures data format consistency

### Translation Modes
1. **Raw JSON**: Complete representation with all metadata
2. **Simplified JSON**: Streamlined format for easier parsing
3. **Semantic Model**: RDF/linked-data representation
4. **CXF**: JSON-LD format per ASHRAE 231P

### Translation Tool: modelica-json
```bash
node modelica-json/app.js -f ControlSequence.mo -o json-simplified
```

**Key Features:**
- Parses Modelica packages or individual CDL files
- Multiple output formats
- Schema validation
- Supports Linux and Windows
- Requires Java and Node.js (>= v18)

## 5. Control eXchange Format (CXF)

### CXF Architecture
- **Format**: JSON-LD (JSON for Linked Data)
- **Purpose**: Machine-readable control logic exchange
- **Compatibility**: Shares 130+ elementary functions with CDL
- **Workflow**: Design → Specification → Implementation → Verification

### CXF-Core.jsonld Structure

#### Key Classes
- **Package**: Container for related blocks
- **Blocks**: ElementaryBlock, CompositeBlock, ExtensionBlock
- **Connectors**: InputConnector, OutputConnector
- **Parameters**: Configurable values
- **Constants**: Fixed values
- **DataTypes**: Boolean, Integer, Real, Enumeration

#### Instance Representation
```json
{
  "@type": "cdl:CompositeBlock",
  "cdl:instance": [
    {
      "@id": "packagePath.BlockName.instanceName",
      "@type": "cdl:ElementaryBlock",
      "cdl:hasParameter": [...],
      "cdl:hasInput": [...],
      "cdl:hasOutput": [...]
    }
  ]
}
```

### Translation Options
- **Array Handling**: Preserve or flatten multidimensional arrays
- **Expression Handling**: Preserve or evaluate expressions
- **Metadata**: Optional software/translator information
- **Type Conversion**: Automatic when necessary

## 6. Python Implementation Requirements

### Architecture Considerations

#### 1. Parser Layer
- Parse CDL (.mo files) using Modelica syntax subset
- Lexical analysis (tokenization)
- Syntax analysis (AST generation)
- Semantic validation

**Recommended Approach:**
- Use existing Modelica parser or create custom parser
- Consider ANTLR or PLY (Python Lex-Yacc) for grammar definition
- Build Abstract Syntax Tree (AST) representation

#### 2. Object Model Layer
- Represent CDL blocks as Python objects
- Type system for Real, Boolean, Integer
- Connection graph management
- Parameter handling with validation

**Design Pattern:**
```python
from pydantic import BaseModel
from typing import List, Optional, Union

class Connector(BaseModel):
    name: str
    type: str  # Real, Boolean, Integer
    value: Optional[Union[float, bool, int]]

class CDLBlock(BaseModel):
    name: str
    parameters: List[Parameter]
    inputs: List[Connector]
    outputs: List[Connector]
```

#### 3. Execution Engine
- Dependency graph construction
- Topological sorting for execution order
- Event-based computation
- Value propagation through connections

**Key Challenges:**
- Cycle detection in connection graph
- Type checking and conversion
- State management between events
- Efficient execution for large sequences

#### 4. Translation Layer
- CDL to CDL-JSON serialization
- CDL-JSON to CDL deserialization
- CXF export (JSON-LD generation)
- Schema validation

**Implementation:**
```python
class CDLTranslator:
    def to_json(self, block: CDLBlock) -> dict:
        """Convert CDL block to JSON representation"""

    def to_cxf(self, block: CDLBlock) -> dict:
        """Convert CDL block to CXF JSON-LD"""

    def validate_schema(self, json_data: dict) -> bool:
        """Validate against CDL-JSON schema"""
```

### Required Python Libraries

#### Core Dependencies
- **pydantic**: Data validation and serialization/deserialization
- **typing**: Type hints and annotations
- **jsonschema**: JSON schema validation
- **rdflib**: RDF/JSON-LD support for CXF

#### Optional Dependencies
- **networkx**: Graph operations for dependency analysis
- **antlr4-python3-runtime**: Parser generation (if using ANTLR)
- **ply**: Alternative parser generator
- **lark**: Modern parsing library

#### Development Tools
- **ruff**: Linting
- **pyright**: Type checking
- **pytest**: Testing framework
- **uv**: Package management

## 7. Implementation Challenges

### Technical Challenges

#### 1. Modelica Subset Parsing
- **Challenge**: Parse Modelica syntax correctly
- **Complexity**: Medium-High
- **Solution**: Use existing parser or grammar-based approach
- **Risk**: Modelica syntax is complex and evolving

#### 2. Type System
- **Challenge**: Implement CDL type system in Python
- **Complexity**: Medium
- **Solution**: Use Python type hints + runtime validation
- **Risk**: Type mismatches at runtime

#### 3. Dependency Resolution
- **Challenge**: Build and validate acyclic dependency graphs
- **Complexity**: Medium
- **Solution**: Topological sort with cycle detection
- **Risk**: Performance with large control sequences

#### 4. Schema Validation
- **Challenge**: Validate against CDL-JSON and CXF schemas
- **Complexity**: Low-Medium
- **Solution**: Use jsonschema library
- **Risk**: Schema evolution and version compatibility

#### 5. Event-Based Execution
- **Challenge**: Implement synchronous data flow model
- **Complexity**: High
- **Solution**: Build execution engine with event queue
- **Risk**: Correctness and performance

### Standards Compliance

#### ASHRAE 231P Compliance
- Must support all 130+ elementary functions
- Strict adherence to CXF JSON-LD format
- Schema validation required
- Metadata preservation

#### Modelica Subset Compliance
- Limited to CDL-approved Modelica constructs
- No dynamic behavior (only discrete events)
- Single assignment rule enforcement
- No algebraic loops

## 8. Recommended Architecture

### Layered Architecture

```
┌─────────────────────────────────────────┐
│         Application Layer               │
│  (Control Sequence Design & Deployment) │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Translation Layer               │
│    (CDL-JSON, CXF Export/Import)       │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Execution Engine                │
│  (Dependency Graph, Event Processing)   │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Object Model Layer              │
│    (Blocks, Connectors, Parameters)     │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Parser Layer                    │
│      (CDL Syntax Processing)            │
└─────────────────────────────────────────┘
```

### Component Breakdown

#### Parser Module (`parser/`)
- `lexer.py`: Tokenization
- `grammar.py`: CDL grammar definition
- `parser.py`: Syntax analysis
- `ast_builder.py`: AST construction

#### Model Module (`model/`)
- `block.py`: Block definitions
- `connector.py`: Input/Output connectors
- `parameter.py`: Parameters and constants
- `types.py`: CDL type system

#### Engine Module (`engine/`)
- `graph.py`: Dependency graph
- `executor.py`: Execution engine
- `validator.py`: Validation logic

#### Translation Module (`translation/`)
- `json_serializer.py`: CDL to JSON
- `json_deserializer.py`: JSON to CDL
- `cxf_exporter.py`: CXF generation
- `schema_validator.py`: Schema validation

## 9. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
1. Setup project structure with uv and pyproject.toml
2. Define core data models using Pydantic
3. Implement basic type system
4. Create simple block representations

### Phase 2: Parser (Weeks 3-4)
1. Design CDL grammar
2. Implement lexer and parser
3. Build AST representation
4. Add syntax validation

### Phase 3: Object Model (Weeks 5-6)
1. Implement all block types
2. Add connection management
3. Parameter validation
4. Type checking

### Phase 4: Execution Engine (Weeks 7-8)
1. Build dependency graph
2. Implement topological sorting
3. Create execution engine
4. Add state management

### Phase 5: Translation (Weeks 9-10)
1. CDL-JSON serialization
2. CDL-JSON deserialization
3. CXF export support
4. Schema validation

### Phase 6: Testing & Documentation (Weeks 11-12)
1. Comprehensive test suite
2. Integration tests
3. Documentation
4. Example control sequences

## 10. Similar Projects and References

### Existing Implementations
1. **modelica-json**: Official translator (Node.js/Java)
   - Reference implementation
   - Production-ready
   - Comprehensive schema support

2. **CREST DSL**: Python-based CPS DSL
   - Internal DSL approach
   - Formal semantics
   - Cyber-physical systems focus

3. **OpenModelica Python Interface**:
   - Modelica simulation in Python
   - FMU export/import
   - Not CDL-specific

### Python DSL Patterns
- **Operator Overloading**: For intuitive syntax
- **Context Managers**: For scope management
- **Decorators**: For block definitions
- **Metaclasses**: For automatic registration

## 11. Key Takeaways for Implementation

### Critical Success Factors
1. **Standards Compliance**: Strict adherence to ASHRAE 231P and CDL specification
2. **Type Safety**: Robust type system with validation
3. **Performance**: Efficient execution for large sequences
4. **Interoperability**: Full CDL-JSON and CXF support
5. **Testing**: Comprehensive test coverage

### Design Principles
1. **Simplicity**: Keep API intuitive and Pythonic
2. **Modularity**: Separate concerns clearly
3. **Extensibility**: Support custom blocks and extensions
4. **Validation**: Fail fast with clear error messages
5. **Documentation**: Comprehensive examples and guides

### Risk Mitigation
1. Start with simple elementary blocks
2. Validate against reference implementation (modelica-json)
3. Build comprehensive test suite early
4. Use existing schemas for validation
5. Consider wrapping modelica-json as initial approach

## 12. Recommended Initial Approach

### Option A: Pure Python Implementation
**Pros:**
- Full control over implementation
- Native Python integration
- No external dependencies on Node.js/Java

**Cons:**
- Higher development effort
- Risk of standards divergence
- Need to maintain parser

### Option B: Hybrid Approach (RECOMMENDED)
**Pros:**
- Leverage modelica-json for parsing
- Focus on Python object model and execution
- Faster time to market
- Standards compliance guaranteed

**Cons:**
- Dependency on external tool
- May need Node.js runtime

**Implementation:**
```python
class CDLTranslator:
    def parse_cdl(self, mo_file: str) -> CDLBlock:
        # Use modelica-json for parsing
        json_output = subprocess.run([
            'node', 'modelica-json/app.js',
            '-f', mo_file,
            '-o', 'json-simplified'
        ], capture_output=True)

        # Parse JSON into Python objects
        cdl_json = json.loads(json_output.stdout)
        return self.from_json(cdl_json)
```

## Conclusion

The CDL specification provides a robust foundation for vendor-independent building automation control logic. A Python implementation should focus on:

1. **Correct parsing** of CDL syntax (leverage existing tools)
2. **Rich object model** using Pydantic for validation
3. **Efficient execution** with dependency graph resolution
4. **Standards compliance** for CDL-JSON and CXF
5. **Comprehensive testing** against reference implementation

The hybrid approach leveraging modelica-json for parsing while building native Python execution and object model is recommended for initial implementation.
