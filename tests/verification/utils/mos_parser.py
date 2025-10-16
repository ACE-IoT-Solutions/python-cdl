"""Parser for Modelica .mos (Modelica Script) files.

This module provides utilities for parsing Modelica .mos files that contain
time-series data from simulations, particularly for the Building 33 cooling coil
validation data.

MOS file format example:
    #1
    double data(2,N)  # 2 variables, N time points
    0.0  273.15  # time, value1
    5.0  274.15  # time, value2
    ...
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field


class MOSMetadata(BaseModel):
    """Metadata from MOS file header."""

    version: int = Field(default=1, description="MOS format version")
    n_variables: int = Field(description="Number of variables in dataset")
    n_points: int = Field(description="Number of time points")
    variable_names: list[str] = Field(
        default_factory=list,
        description="Variable names (if specified in file)"
    )
    comments: list[str] = Field(
        default_factory=list,
        description="Comments from file"
    )
    source_file: str | None = Field(
        default=None,
        description="Source file path"
    )


@dataclass
class MOSData:
    """Parsed MOS file data."""

    metadata: MOSMetadata
    time: np.ndarray
    variables: dict[str, np.ndarray]
    raw_data: np.ndarray  # Full data matrix

    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame with time index.

        Returns:
            DataFrame with time as index and variables as columns
        """
        df = pd.DataFrame(self.variables, index=self.time)
        df.index.name = "time"
        return df

    def to_reference_data_format(self) -> dict[str, Any]:
        """Convert to verification framework ReferenceData format.

        Returns:
            Dictionary compatible with ReferenceData model
        """
        return {
            "time": self.time.tolist(),
            "variables": {
                name: values.tolist()
                for name, values in self.variables.items()
            },
            "metadata": {
                "source_file": self.metadata.source_file,
                "format": "mos",
                "n_points": self.metadata.n_points,
                "n_variables": self.metadata.n_variables,
            }
        }


class MOSParser:
    """Parser for Modelica .mos files."""

    # Regex patterns for MOS format
    HEADER_PATTERN = re.compile(r"#(\d+)")  # Version number
    DATA_DECL_PATTERN = re.compile(r"(double|float|int)\s+(\w+)\s*\((\d+)\s*,\s*(\d+)\)")
    COMMENT_PATTERN = re.compile(r"#\s*(.+)")

    @staticmethod
    def parse(filepath: Path | str, variable_names: list[str] | None = None) -> MOSData:
        """Parse MOS file into structured data.

        Args:
            filepath: Path to .mos file
            variable_names: Optional list of variable names. If not provided,
                           will use generic names (var1, var2, etc.)

        Returns:
            MOSData object containing parsed data

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"MOS file not found: {filepath}")

        with open(filepath) as f:
            lines = f.readlines()

        # Parse header and metadata
        version = 1
        n_variables = 0
        n_points = 0
        comments = []
        data_start_line = 0

        for i, line in enumerate(lines):
            line = line.strip()

            # Version header
            if match := MOSParser.HEADER_PATTERN.match(line):
                version = int(match.group(1))
                continue

            # Data declaration: double data(n_vars, n_points)
            if match := MOSParser.DATA_DECL_PATTERN.match(line):
                n_variables = int(match.group(3))
                n_points = int(match.group(4))
                data_start_line = i + 1
                break

            # Comments
            if match := MOSParser.COMMENT_PATTERN.match(line):
                comments.append(match.group(1).strip())

        if n_variables == 0 or n_points == 0:
            raise ValueError(
                f"Invalid MOS file: could not find data declaration. "
                f"Expected format: 'double data(n_vars, n_points)'"
            )

        # Parse data rows
        data_lines = []
        for line in lines[data_start_line:]:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Split on whitespace and convert to floats
            try:
                values = [float(x) for x in line.split()]
                if values:
                    data_lines.append(values)
            except ValueError as e:
                raise ValueError(f"Invalid data line: {line}") from e

        if not data_lines:
            raise ValueError("No data found in MOS file")

        # Convert to numpy array
        # MOS format: each row is [time, var1, var2, ...]
        try:
            data_array = np.array(data_lines)
        except Exception as e:
            raise ValueError(f"Failed to parse data into array: {e}") from e

        # Validate dimensions
        expected_cols = n_variables + 1  # +1 for time column
        if data_array.shape[1] != expected_cols:
            raise ValueError(
                f"Data dimension mismatch: expected {expected_cols} columns "
                f"(time + {n_variables} variables), got {data_array.shape[1]}"
            )

        actual_points = len(data_array)
        if actual_points != n_points:
            # Warning but not error - some files may have different counts
            import warnings
            warnings.warn(
                f"Number of data points ({actual_points}) doesn't match "
                f"header declaration ({n_points}). Using actual count."
            )
            n_points = actual_points

        # Extract time and variables
        time = data_array[:, 0]

        # Generate variable names if not provided
        if variable_names is None:
            # Try to extract from comments or use generic names
            if len(comments) > 0 and "," in comments[0]:
                # Some MOS files have variable names in first comment
                variable_names = [name.strip() for name in comments[0].split(",")]
                if len(variable_names) != n_variables:
                    variable_names = [f"var{i+1}" for i in range(n_variables)]
            else:
                variable_names = [f"var{i+1}" for i in range(n_variables)]
        elif len(variable_names) != n_variables:
            raise ValueError(
                f"Number of variable names ({len(variable_names)}) doesn't "
                f"match number of variables in file ({n_variables})"
            )

        # Create variable dictionary
        variables = {}
        for i, name in enumerate(variable_names):
            variables[name] = data_array[:, i + 1]  # +1 to skip time column

        # Create metadata
        metadata = MOSMetadata(
            version=version,
            n_variables=n_variables,
            n_points=n_points,
            variable_names=variable_names,
            comments=comments,
            source_file=str(filepath)
        )

        return MOSData(
            metadata=metadata,
            time=time,
            variables=variables,
            raw_data=data_array
        )

    @staticmethod
    def parse_building33_format(filepath: Path | str) -> MOSData:
        """Parse Building 33 cooling coil MOS file with known variable names.

        The Building 33 data contains cooling coil measurements with 5-second
        resolution.

        Args:
            filepath: Path to Building 33 .mos file

        Returns:
            MOSData with Building 33 variable names
        """
        # Known variable names for Building 33 cooling coil data
        # These should be updated based on actual file structure
        variable_names = [
            "T_air_in",      # Inlet air temperature
            "T_air_out",     # Outlet air temperature
            "T_water_in",    # Inlet water temperature
            "T_water_out",   # Outlet water temperature
            "m_flow_air",    # Air mass flow rate
            "m_flow_water",  # Water mass flow rate
        ]

        return MOSParser.parse(filepath, variable_names)


def load_mos_as_reference_data(
    filepath: Path | str,
    variable_names: list[str] | None = None
) -> dict[str, Any]:
    """Load MOS file and convert to ReferenceData format.

    This is a convenience function for loading MOS files directly into
    the format expected by the verification framework.

    Args:
        filepath: Path to .mos file
        variable_names: Optional variable names

    Returns:
        Dictionary compatible with ReferenceData model
    """
    mos_data = MOSParser.parse(filepath, variable_names)
    return mos_data.to_reference_data_format()


# Convenience function for common use case
def load_mos_as_dataframe(
    filepath: Path | str,
    variable_names: list[str] | None = None
) -> pd.DataFrame:
    """Load MOS file directly as pandas DataFrame.

    Args:
        filepath: Path to .mos file
        variable_names: Optional variable names

    Returns:
        DataFrame with time index and variables as columns
    """
    mos_data = MOSParser.parse(filepath, variable_names)
    return mos_data.to_dataframe()
