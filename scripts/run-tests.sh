#!/bin/bash
# scripts/run-tests.sh - Script for execute test and quality

# Colors
NC='\033[0m'            # No Color
RED='\033[0;31m'        # Red
GREEN='\033[0;32m'      # Green
YELLOW='\033[1;33m'     # Yellow
BLUE='\033[0;34m'       # Blue
PURPLE='\033[0;35m'     # Purple
CYAN='\033[0;36m'       # Cyan
BIGreen='\033[1;92m'    # Bold Green

# Configuration
COVERAGE_THRESHOLD=${COVERAGE_THRESHOLD:-80}
PYLINT_THRESHOLD=${PYLINT_THRESHOLD:-8.0}

echo -e "${BLUE}Starting comprehensive test suite${NC}"
echo -e "${PURPLE}Coverage threshold: ${COVERAGE_THRESHOLD}%${NC}"
echo -e "${PURPLE}Pylint threshold: ${PYLINT_THRESHOLD}/10${NC}"
echo ""

# Create reports directory
mkdir -p reports/{tests,coverage,pylint,badges}

# Function to show step
show_step() {
    echo -e "${CYAN}->$1${NC}"
}

# Function to show success
show_success() {
    echo -e "${GREEN}$1${NC}"
}

# Function to show error
show_error() {
    echo -e "${RED}$1${NC}"
}

# Function to show warning
show_warning() {
    echo -e "${YELLOW}$1${NC}"
}

set -e

# Step 1: Run Pylint
show_step "Running Pylint analysis..."
pylint src/ --output-format=text --reports=y > reports/pylint/pylint-report.txt || true
pylint src/ --output-format=json > reports/pylint/pylint-report.json || true
pylint src/ --output-format=parseable > reports/pylint/pylint-parseable.txt || true

# Extract Pylint score
PYLINT_SCORE=$(grep "Your code has been rated" reports/pylint/pylint-report.txt | cut -d' ' -f7 | cut -d'/' -f1 2>/dev/null || echo "0")
echo "Pylint Score: $PYLINT_SCORE/10"

if (( $(echo "$PYLINT_SCORE >= $PYLINT_THRESHOLD" | bc -l) )); then
    show_success "Pylint passed ($PYLINT_SCORE >= $PYLINT_THRESHOLD)"
else
    show_warning "Pylint below threshold ($PYLINT_SCORE < $PYLINT_THRESHOLD)"
fi

echo ""

# Step 2: Run tests with coverage
show_step "Running tests with coverage..."

# Unit tests
if [ -d "tests/unit" ]; then
    echo "Running unit tests..."
    pytest tests/unit/ -v -m "unit" --junitxml=reports/tests/unit-junit.xml || true
fi

# Integration tests
if [ -d "tests/integration" ]; then
    echo "Running integration tests..."
    pytest tests/integration/ -v -m "integration" --junitxml=reports/tests/integration-junit.xml || true
fi

# Full test suite with coverage
echo "Running full test suite with coverage..."
coverage run -m pytest tests/ --junitxml=reports/tests/junit.xml

echo ""

# Step 3: Generate coverage reports
show_step "Generating coverage reports..."
coverage report --show-missing
coverage html -d reports/coverage/html
coverage xml -o reports/coverage/coverage.xml
coverage json -o reports/coverage/coverage.json

# Extract coverage percentage
COVERAGE_PERCENTAGE=$(coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//' || echo "0")
echo "Coverage: $COVERAGE_PERCENTAGE%"

if (( $(echo "$COVERAGE_PERCENTAGE >= $COVERAGE_THRESHOLD" | bc -l) )); then
    show_success "Coverage passed ($COVERAGE_PERCENTAGE% >= $COVERAGE_THRESHOLD%)"
    COVERAGE_STATUS="passed"
    COVERAGE_COLOR="brightgreen"
else
    show_warning "Coverage below threshold ($COVERAGE_PERCENTAGE% < $COVERAGE_THRESHOLD%)"
    COVERAGE_STATUS="failed"
    COVERAGE_COLOR="red"
fi

echo ""

# Step 4: Generate badges
show_step "Generating badges..."

# Coverage badge
cat > reports/badges/coverage.json << EOF
{
  "schemaVersion": 1,
  "label": "coverage",
  "message": "${COVERAGE_PERCENTAGE}%",
  "color": "${COVERAGE_COLOR}"
}
EOF

# Pylint badge
if (( $(echo "$PYLINT_SCORE >= 8" | bc -l) )); then
    PYLINT_COLOR="brightgreen"
elif (( $(echo "$PYLINT_SCORE >= 6" | bc -l) )); then
    PYLINT_COLOR="yellow"
else
    PYLINT_COLOR="red"
fi

cat > reports/badges/pylint.json << EOF
{
  "schemaVersion": 1,
  "label": "pylint",
  "message": "${PYLINT_SCORE}/10",
  "color": "${PYLINT_COLOR}"
}
EOF

# Tests badge
if [ -f "reports/tests/junit.xml" ]; then
    FAILED_TESTS=$(grep -o 'failures="[^"]*"' reports/tests/junit.xml | grep -o '[0-9]*' || echo "0")
    ERROR_TESTS=$(grep -o 'errors="[^"]*"' reports/tests/junit.xml | grep -o '[0-9]*' || echo "0")
    
    if [ "$FAILED_TESTS" = "0" ] && [ "$ERROR_TESTS" = "0" ]; then
        TESTS_MESSAGE="passing"
        TESTS_COLOR="brightgreen"
    else
        TESTS_MESSAGE="failing"
        TESTS_COLOR="red"
    fi
else
    TESTS_MESSAGE="unknown"
    TESTS_COLOR="lightgrey"
fi

cat > reports/badges/tests.json << EOF
{
  "schemaVersion": 1,
  "label": "tests",
  "message": "${TESTS_MESSAGE}",
  "color": "${TESTS_COLOR}"
}
EOF

show_success "Badges generated"

echo ""

# Step 5: Quality Gate Check
show_step "Quality Gate Check..."

QUALITY_GATE_PASSED=true

if (( $(echo "$COVERAGE_PERCENTAGE < $COVERAGE_THRESHOLD" | bc -l) )); then
    show_error "Coverage below threshold: $COVERAGE_PERCENTAGE% < $COVERAGE_THRESHOLD%"
    QUALITY_GATE_PASSED=false
else
    show_success "Coverage above threshold: $COVERAGE_PERCENTAGE% >= $COVERAGE_THRESHOLD%"
fi

if (( $(echo "$PYLINT_SCORE < $PYLINT_THRESHOLD" | bc -l) )); then
    show_error "Pylint score below threshold: $PYLINT_SCORE < $PYLINT_THRESHOLD"
    QUALITY_GATE_PASSED=false
else
    show_success "Pylint score above threshold: $PYLINT_SCORE >= $PYLINT_THRESHOLD"
fi

# Generate quality gate report
mkdir -p reports/quality-gate
cat > reports/quality-gate/summary.json << EOF
{
  "coverage": $COVERAGE_PERCENTAGE,
  "pylint_score": $PYLINT_SCORE,
  "coverage_threshold": $COVERAGE_THRESHOLD,
  "pylint_threshold": $PYLINT_THRESHOLD,
  "quality_gate_passed": $QUALITY_GATE_PASSED,
  "timestamp": "$(date -Iseconds)"
}
EOF

echo ""

# Step 6: Final Summary
show_step "Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}Coverage:${NC} $COVERAGE_PERCENTAGE% (threshold: $COVERAGE_THRESHOLD%)"
echo -e "${BLUE}Pylint:${NC} $PYLINT_SCORE/10 (threshold: $PYLINT_THRESHOLD)"
echo -e "${BLUE}Tests:${NC} $TESTS_MESSAGE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$QUALITY_GATE_PASSED" = true ]; then
    show_success "🎉 QUALITY GATE PASSED - Ready to commit!"
    echo ""
    echo -e "${BIGreen}View reports:${NC}"
    echo -e "   Coverage: ${CYAN}reports/coverage/html/index.html${NC}"
    echo -e "   Tests: ${CYAN}reports/tests/junit.xml${NC}"
    echo -e "   Pylint: ${CYAN}reports/pylint/pylint-report.txt${NC}"
    exit 0
else
    show_error "QUALITY GATE FAILED - Fix issues before committing!"
    echo ""
    echo -e "${RED}🔧 Recommendations:${NC}"
    if (( $(echo "$COVERAGE_PERCENTAGE < $COVERAGE_THRESHOLD" | bc -l) )); then
        echo -e "   • Add more tests to increase coverage to $COVERAGE_THRESHOLD%+"
    fi
    if (( $(echo "$PYLINT_SCORE < $PYLINT_THRESHOLD" | bc -l) )); then
        echo -e "   • Fix pylint issues to reach $PYLINT_THRESHOLD+ score"
    fi
    exit 1
fi