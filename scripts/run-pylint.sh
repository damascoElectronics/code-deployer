#!/bin/bash


NC='\033[0m'            # No Color

# Regular Colors
RED='\033[0;31m'        # Red
GREEN='\033[0;32m'      # Green
# Bold High Intensity
BIGreen='\033[1;92m'      # Green

# Script to execute pylint
set -e

echo "Executing pylint"

# make dir. to create
mkdir -p reports

# Executing pylint s
echo "Generating report txt format ..."
pylint src/ --output-format=text --reports=y > reports/pylint-report.txt

echo "Generating report  JSON format..."
pylint src/ --output-format=json > reports/pylint-report.json

echo "Generating parseable report ..."
pylint src/ --output-format=parseable > reports/pylint-parseable.txt

# Showing resumen
echo "=== RESUMEN PYLINT ==="
tail -n 20 reports/pylint-report.txt

echo "${RED}Reports generated en directorio ${BIGreen}'reports/'${NC}"