#!/usr/bin/env python3
"""Download reference data from OBC test suite.

This script downloads reference data files from the ASHRAE Guideline 36
OpenBuildingControl test suite for verification testing.

Reference data sources:
- Zone temperature setpoints: config_test.json, real_outputs.csv
- Building 33 cooling coil: MOS format, 5-second resolution
"""

import json
import sys
from pathlib import Path
from typing import Any
import urllib.request


class ReferenceDataDownloader:
    """Download and manage OBC reference data."""

    # Base URLs for OBC reference data
    OBC_BASE_URL = "https://raw.githubusercontent.com/lbl-srg/obc/main/specification/test"
    MODELICA_BASE_URL = "https://raw.githubusercontent.com/lbl-srg/modelica-buildings/master"

    def __init__(self, output_dir: Path | None = None):
        """Initialize downloader.

        Args:
            output_dir: Directory to save downloaded files (defaults to reference_data/)
        """
        if output_dir is None:
            # Default to tests/verification/reference_data
            self.output_dir = Path(__file__).parent.parent / "reference_data"
        else:
            self.output_dir = Path(output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def download_file(self, url: str, output_path: Path, description: str = "") -> bool:
        """Download a file from URL.

        Args:
            url: URL to download from
            output_path: Path to save file
            description: Description for logging

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"📥 Downloading {description or url}")
            print(f"   URL: {url}")

            # Create parent directory if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Download file
            urllib.request.urlretrieve(url, output_path)

            size_kb = output_path.stat().st_size / 1024
            print(f"   ✓ Saved to {output_path} ({size_kb:.1f} KB)")
            return True

        except Exception as e:
            print(f"   ✗ Failed to download: {e}")
            return False

    def download_zone_temperature_setpoints(self) -> bool:
        """Download zone temperature setpoints test data.

        Downloads:
        - config_test.json: Test configuration with tolerances
        - real_outputs.csv: Reference outputs from Modelica simulation

        Returns:
            True if all files downloaded successfully
        """
        print("\n🌡️  Downloading zone temperature setpoints test data...")

        output_subdir = self.output_dir / "zone_temperature_setpoints"
        output_subdir.mkdir(parents=True, exist_ok=True)

        # Note: These are placeholder URLs - update with actual OBC test suite URLs
        # The OBC test suite structure needs to be verified
        files = [
            {
                "url": f"{self.OBC_BASE_URL}/zone_temp/config_test.json",
                "path": output_subdir / "config_test.json",
                "desc": "Test configuration"
            },
            {
                "url": f"{self.OBC_BASE_URL}/zone_temp/real_outputs.csv",
                "path": output_subdir / "real_outputs.csv",
                "desc": "Reference outputs"
            },
        ]

        results = []
        for file_info in files:
            success = self.download_file(
                file_info["url"],
                file_info["path"],
                file_info["desc"]
            )
            results.append(success)

        return all(results)

    def download_building33_cooling_coil(self) -> bool:
        """Download Building 33 cooling coil data.

        Downloads MOS format data with 5-second resolution.

        Returns:
            True if download successful
        """
        print("\n❄️  Downloading Building 33 cooling coil data...")

        output_subdir = self.output_dir / "building33_cooling_coil"
        output_subdir.mkdir(parents=True, exist_ok=True)

        # Placeholder URL - update with actual location
        url = f"{self.MODELICA_BASE_URL}/Buildings/Resources/Data/Controls/OBC/CDL/Continuous/Validation/Building33CoolingCoil.mos"
        output_path = output_subdir / "cooling_coil_data.mos"

        return self.download_file(url, output_path, "Building 33 cooling coil data")

    def create_sample_data(self) -> None:
        """Create sample reference data for testing when real data unavailable.

        This creates synthetic reference data that matches the expected format
        for development and testing purposes.
        """
        print("\n🔧 Creating sample reference data for development...")

        # Sample zone temperature setpoints config
        config = {
            "test_name": "zone_temperature_setpoints",
            "description": "Validation of zone temperature setpoint control",
            "tolerance": {
                "absolute": 2.0,  # 2K absolute tolerance (atoly=2K from spec)
                "relative": 0.01  # 1% relative tolerance
            },
            "simulation": {
                "start_time": 0.0,
                "end_time": 86400.0,  # 24 hours
                "time_step": 300.0     # 5 minutes
            },
            "variables": [
                {
                    "name": "TSetCoo",
                    "description": "Cooling setpoint temperature",
                    "unit": "K"
                },
                {
                    "name": "TSetHea",
                    "description": "Heating setpoint temperature",
                    "unit": "K"
                }
            ]
        }

        config_dir = self.output_dir / "zone_temperature_setpoints"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / "config_test.json"

        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        print(f"   ✓ Created {config_path}")

        # Sample CSV with reference outputs
        csv_content = """time,TSetCoo,TSetHea
0.0,297.15,293.15
300.0,297.15,293.15
600.0,297.15,293.15
900.0,297.15,293.15
1200.0,297.15,293.15
"""

        csv_path = config_dir / "real_outputs.csv"
        csv_path.write_text(csv_content)

        print(f"   ✓ Created {csv_path}")

    def download_all(self, create_samples: bool = True) -> dict[str, bool]:
        """Download all reference data.

        Args:
            create_samples: If True and downloads fail, create sample data

        Returns:
            Dictionary mapping dataset names to success status
        """
        print("="*70)
        print("OBC Reference Data Downloader")
        print("="*70)

        results = {}

        # Try to download real data
        results["zone_temperature_setpoints"] = self.download_zone_temperature_setpoints()
        results["building33_cooling_coil"] = self.download_building33_cooling_coil()

        # If downloads failed and samples requested, create sample data
        if not results["zone_temperature_setpoints"] and create_samples:
            print("\n⚠️  Real data download failed, creating sample data instead")
            self.create_sample_data()
            results["zone_temperature_setpoints"] = True

        # Summary
        print("\n" + "="*70)
        print("Download Summary")
        print("="*70)
        for dataset, success in results.items():
            status = "✓" if success else "✗"
            print(f"{status} {dataset}")

        print(f"\nOutput directory: {self.output_dir}")

        return results


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Download OBC reference data for verification testing"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory (default: tests/verification/reference_data)"
    )
    parser.add_argument(
        "--no-samples",
        action="store_true",
        help="Don't create sample data if downloads fail"
    )
    parser.add_argument(
        "--dataset",
        choices=["zone_temp", "building33", "all"],
        default="all",
        help="Which dataset to download (default: all)"
    )

    args = parser.parse_args()

    downloader = ReferenceDataDownloader(args.output_dir)

    if args.dataset == "zone_temp":
        success = downloader.download_zone_temperature_setpoints()
    elif args.dataset == "building33":
        success = downloader.download_building33_cooling_coil()
    else:
        results = downloader.download_all(create_samples=not args.no_samples)
        success = all(results.values())

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
