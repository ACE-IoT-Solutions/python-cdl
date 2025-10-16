"""Data loaders for reference data in verification tests.

This module provides utilities for loading time-series reference data
from various formats (CSV, JSON) for comparison with simulation results.
"""

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field


class ReferenceData(BaseModel):
    """Container for reference time-series data."""

    time: list[float] = Field(description="Time points")
    variables: dict[str, list[float]] = Field(
        description="Dictionary mapping variable names to value arrays"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata about the reference data",
    )

    def to_numpy(self) -> tuple[np.ndarray, dict[str, np.ndarray]]:
        """Convert to numpy arrays.

        Returns:
            Tuple of (time_array, variables_dict with numpy arrays)
        """
        time_array = np.array(self.time)
        var_arrays = {name: np.array(values) for name, values in self.variables.items()}
        return time_array, var_arrays

    def get_variable(self, name: str) -> np.ndarray:
        """Get variable as numpy array.

        Args:
            name: Variable name

        Returns:
            Numpy array of variable values

        Raises:
            KeyError: If variable not found
        """
        if name not in self.variables:
            raise KeyError(
                f"Variable '{name}' not found. Available: {list(self.variables.keys())}"
            )
        return np.array(self.variables[name])

    @property
    def variable_names(self) -> list[str]:
        """Get list of variable names."""
        return list(self.variables.keys())

    @property
    def n_points(self) -> int:
        """Get number of time points."""
        return len(self.time)


class CSVDataLoader:
    """Load reference data from CSV files.

    Expected CSV format:
    - First column: time
    - Subsequent columns: variable values
    - Header row with column names
    """

    @staticmethod
    def load(filepath: Path | str, time_column: str = "time") -> ReferenceData:
        """Load reference data from CSV file.

        Args:
            filepath: Path to CSV file
            time_column: Name of time column (default: "time")

        Returns:
            ReferenceData object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If time column not found or data is invalid
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"CSV file not found: {filepath}")

        # Read CSV with pandas
        df = pd.read_csv(filepath)

        # Validate time column exists
        if time_column not in df.columns:
            raise ValueError(
                f"Time column '{time_column}' not found. "
                f"Available columns: {list(df.columns)}"
            )

        # Extract time and variables
        time = df[time_column].tolist()
        variable_cols = [col for col in df.columns if col != time_column]
        variables = {col: df[col].tolist() for col in variable_cols}

        # Create metadata
        metadata = {
            "source_file": str(filepath),
            "format": "csv",
            "n_variables": len(variable_cols),
        }

        return ReferenceData(time=time, variables=variables, metadata=metadata)

    @staticmethod
    def load_multiple(
        directory: Path | str,
        pattern: str = "*.csv",
        time_column: str = "time",
    ) -> dict[str, ReferenceData]:
        """Load multiple CSV files from a directory.

        Args:
            directory: Directory containing CSV files
            pattern: Glob pattern for matching files (default: "*.csv")
            time_column: Name of time column

        Returns:
            Dictionary mapping filenames (without extension) to ReferenceData objects
        """
        directory = Path(directory)
        results = {}

        for filepath in directory.glob(pattern):
            key = filepath.stem  # Filename without extension
            results[key] = CSVDataLoader.load(filepath, time_column)

        return results


class JSONDataLoader:
    """Load reference data from JSON files.

    Expected JSON format:
    {
        "time": [0.0, 0.1, 0.2, ...],
        "variables": {
            "var1": [1.0, 2.0, 3.0, ...],
            "var2": [4.0, 5.0, 6.0, ...]
        },
        "metadata": {...}  // optional
    }
    """

    @staticmethod
    def load(filepath: Path | str) -> ReferenceData:
        """Load reference data from JSON file.

        Args:
            filepath: Path to JSON file

        Returns:
            ReferenceData object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON structure is invalid
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"JSON file not found: {filepath}")

        with open(filepath) as f:
            data = json.load(f)

        # Validate structure
        if "time" not in data:
            raise ValueError("JSON must contain 'time' field")
        if "variables" not in data:
            raise ValueError("JSON must contain 'variables' field")

        # Add source info to metadata
        metadata = data.get("metadata", {})
        metadata.update(
            {
                "source_file": str(filepath),
                "format": "json",
            }
        )

        return ReferenceData(
            time=data["time"],
            variables=data["variables"],
            metadata=metadata,
        )

    @staticmethod
    def load_multiple(
        directory: Path | str,
        pattern: str = "*.json",
    ) -> dict[str, ReferenceData]:
        """Load multiple JSON files from a directory.

        Args:
            directory: Directory containing JSON files
            pattern: Glob pattern for matching files (default: "*.json")

        Returns:
            Dictionary mapping filenames (without extension) to ReferenceData objects
        """
        directory = Path(directory)
        results = {}

        for filepath in directory.glob(pattern):
            key = filepath.stem  # Filename without extension
            results[key] = JSONDataLoader.load(filepath)

        return results


class ReferenceDataLoader:
    """Unified loader that automatically detects file format."""

    @staticmethod
    def load(filepath: Path | str, **kwargs) -> ReferenceData:
        """Load reference data, auto-detecting format from file extension.

        Args:
            filepath: Path to data file
            **kwargs: Additional arguments passed to format-specific loader

        Returns:
            ReferenceData object

        Raises:
            ValueError: If file format not supported
        """
        filepath = Path(filepath)
        suffix = filepath.suffix.lower()

        if suffix == ".csv":
            return CSVDataLoader.load(filepath, **kwargs)
        elif suffix == ".json":
            return JSONDataLoader.load(filepath, **kwargs)
        else:
            raise ValueError(
                f"Unsupported file format: {suffix}. "
                f"Supported formats: .csv, .json"
            )

    @staticmethod
    def load_multiple(
        directory: Path | str,
        pattern: str = "*",
        **kwargs,
    ) -> dict[str, ReferenceData]:
        """Load all supported files from a directory.

        Args:
            directory: Directory containing data files
            pattern: Glob pattern for matching files (default: all files)
            **kwargs: Additional arguments passed to format-specific loaders

        Returns:
            Dictionary mapping filenames to ReferenceData objects
        """
        directory = Path(directory)
        results = {}

        # Load CSV files
        csv_files = directory.glob(f"{pattern}.csv" if "*" not in pattern else "*.csv")
        for filepath in csv_files:
            key = filepath.stem
            results[key] = CSVDataLoader.load(filepath, **kwargs)

        # Load JSON files
        json_files = directory.glob(
            f"{pattern}.json" if "*" not in pattern else "*.json"
        )
        for filepath in json_files:
            key = filepath.stem
            results[key] = JSONDataLoader.load(filepath, **kwargs)

        return results
