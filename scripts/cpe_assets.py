#!/usr/bin/env python3
"""Generate CPE-compatible asset list from requirements.txt files.

This module provides functionality to parse Python requirements.txt files
and generate CPE (Common Platform Enumeration) 2.3 format asset manifests
for vulnerability management and security scanning purposes.
"""

import json
import re
from pathlib import Path
from typing import Dict, List


"""Parse requirements.txt and generate CPE format assets.

Reads a Python requirements.txt file and extracts package names and versions,
converting them to CPE 2.3 format for security vulnerability tracking.

Args:
    file_path (str): Path to the requirements.txt file to parse.

Returns:
    List[Dict[str, str]]: List of asset dictionaries containing:
        - name: Package name
        - version: Package version
        - cpe: CPE 2.3 formatted string
        - type: Asset type (python_package)
        - source_file: Source requirements file path

Raises:
    FileNotFoundError: If the specified requirements file doesn't exist.
    IOError: If there's an error reading the requirements file.

Note:
    Currently only supports exact version specifications (package==version).
    Comments and blank lines in requirements.txt are ignored.

Example:
    >>> assets = parse_requirements("requirements.txt")
    >>> print(assets[0])
    {
        'name': 'requests',
        'version': '2.28.1',
        'cpe': 'cpe:2.3:a:python:requests:2.28.1:*:*:*:*:*:*:*',
        'type': 'python_package',
        'source_file': 'requirements.txt'
    }
"""

def parse_requirements(file_path: str) -> List[Dict[str, str]]:

    assets = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Parse package==version format
                match = re.match(r'^([a-zA-Z0-9_-]+)==([0-9.]+)', line)
                if match:
                    package, version = match.groups()

                    # Generate CPE 2.3 format
                    cpe = f"cpe:2.3:a:python:{package}:{version}:*:*:*:*:*:*:*"

                    assets.append({
                        "name": package,
                        "version": version,
                        "cpe": cpe,
                        "type": "python_package",
                        "source_file": file_path
                    })

    return assets

"""Main function to generate CPE asset manifest.

Processes all configured requirements.txt files and generates a comprehensive
CPE asset manifest in JSON format. The manifest includes metadata and all
discovered Python package assets with their CPE identifiers.

The function:
    1. Iterates through predefined requirements.txt file paths
    2. Parses each existing file for Python packages
    3. Aggregates all assets into a single manifest
    4. Writes the manifest to 'cpe-assets.json'
    5. Reports the total number of assets generated

Raises:
    IOError: If there's an error writing the output file.
    json.JSONEncodeError: If there's an error serializing the manifest.

Note:
    Only processes files that exist; missing files are silently skipped.
    Output file is always named 'cpe-assets.json' in the current directory.
"""

def main() -> None:
   
    all_assets = []

    # Process both requirements files
    requirements_files = [
        "local/log_processor/requirements.txt",
        "remote/log_collector/requirements.txt"
    ]

    for req_file in requirements_files:
        if Path(req_file).exists():
            assets = parse_requirements(req_file)
            all_assets.extend(assets)

    # Generate asset manifest
    manifest = {
        "metadata": {
            "generated_at": "2025-08-05T00:00:00Z",
            "generator": "CPE Asset Generator v1.0",
            "total_assets": len(all_assets)
        },
        "assets": all_assets
    }

    # Save CPE asset list
    with open("cpe-assets.json", "w", encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    print(f"Generated CPE asset list with {len(all_assets)} assets")


if __name__ == "__main__":
    main()