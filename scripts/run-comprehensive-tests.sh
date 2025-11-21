#!/bin/bash
# scripts/run-comprehensive-tests.sh - Comprehensive quality and security pipeline

# Colors
NC='\033[0m'            # No Color
RED='\033[0;31m'        # Red
GREEN='\033[0;32m'      # Green
YELLOW='\033[1;33m'     # Yellow
BLUE='\033[0;34m'       # Blue
PURPLE='\033[0;35m'     # Purple
CYAN='\033[0;36m'       # Cyan
BIGreen='\033[1;92m'    # Bold Green
BRed='\033[1;31m'       # Bold Red

# Configuration
COVERAGE_THRESHOLD=${COVERAGE_THRESHOLD:-80}
PYLINT_THRESHOLD=${PYLINT_THRESHOLD:-8.0}
SEMGREP_MAX_CRITICAL=${SEMGREP_MAX_CRITICAL:-0}
SEMGREP_MAX_HIGH=${SEMGREP_MAX_HIGH:-5}
SEMGREP_MAX_MEDIUM=${SEMGREP_MAX_MEDIUM:-10}

echo -e "${BIGreen}=== COMPREHENSIVE CODE QUALITY & SECURITY PIPELINE ===${NC}"
echo -e "${PURPLE}Coverage threshold: ${COVERAGE_THRESHOLD}%${NC}"
echo -e "${PURPLE}Pylint threshold: ${PYLINT_THRESHOLD}/10${NC}"
echo -e "${PURPLE}Security thresholds - Critical: ${SEMGREP_MAX_CRITICAL}, High: ${SEMGREP_MAX_HIGH}, Medium: ${SEMGREP_MAX_MEDIUM}${NC}"
echo ""

# Function to show step
show_step() {
    echo -e "${CYAN}▶ $1${NC}"
}

# Function to show success
show_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to show error
show_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to show warning
show_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to show section
show_section() {
    echo ""
    echo -e "${BIGreen}=== $1 ===${NC}"
}

set -e

# Create comprehensive reports directory
mkdir -p reports/{tests,coverage,pylint,semgrep,security,badges,quality-gate}

PIPELINE_START_TIME=$(date +%s)

# ===============================
# STAGE 1: CODE LINTING
# ===============================
show_section "STAGE 1: CODE LINTING & STYLE"

show_step "Running Pylint analysis..."
pylint src/ --output-format=text --reports=y > reports/pylint/pylint-report.txt || true
pylint src/ --output-format=json > reports/pylint/pylint-report.json || true
pylint src/ --output-format=parseable > reports/pylint/pylint-parseable.txt || true

# Extract Pylint score
PYLINT_SCORE=$(grep "Your code has been rated" reports/pylint/pylint-report.txt | cut -d' ' -f7 | cut -d'/' -f1 2>/dev/null || echo "0")
echo "Pylint Score: $PYLINT_SCORE/10"

if (( $(echo "$PYLINT_SCORE >= $PYLINT_THRESHOLD" | bc -l) )); then
    show_success "Pylint passed ($PYLINT_SCORE >= $PYLINT_THRESHOLD)"
    PYLINT_PASSED=true
else
    show_warning "Pylint below threshold ($PYLINT_SCORE < $PYLINT_THRESHOLD)"
    PYLINT_PASSED=false
fi

# ===============================
# STAGE 2: TESTING & COVERAGE
# ===============================
show_section "STAGE 2: TESTING & COVERAGE"

show_step "Running unit tests..."
if [ -d "tests/unit" ]; then
    pytest tests/unit/ -v -m "unit" --junitxml=reports/tests/unit-junit.xml || true
fi

show_step "Running integration tests..."
if [ -d "tests/integration" ]; then
    pytest tests/integration/ -v -m "integration" --junitxml=reports/tests/integration-junit.xml || true
fi

show_step "Running full test suite with coverage..."
coverage run -m pytest tests/ --junitxml=reports/tests/junit.xml

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
    COVERAGE_PASSED=true
    COVERAGE_COLOR="brightgreen"
else
    show_warning "Coverage below threshold ($COVERAGE_PERCENTAGE% < $COVERAGE_THRESHOLD%)"
    COVERAGE_PASSED=false
    COVERAGE_COLOR="red"
fi

# ===============================
# STAGE 3: SECURITY ANALYSIS
# ===============================
show_section "STAGE 3: SECURITY ANALYSIS"

show_step "Running Semgrep SAST scan..."
# Run with auto config (includes comprehensive rulesets)
semgrep --config=auto --json --output=reports/semgrep/semgrep-results.json --severity=INFO src/ || true
semgrep --config=auto --output=reports/semgrep/semgrep-results.txt --severity=INFO src/ || true
semgrep --config=auto --sarif --output=reports/semgrep/semgrep-results.sarif --severity=INFO src/ || true

# Run custom rules
if [ -f "custom-security-rules.yml" ]; then
    show_step "Running custom security rules..."
    semgrep --config=custom-security-rules.yml --json --output=reports/semgrep/custom-results.json src/ || true
fi

show_step "Running Supply Chain Analysis..."
if [ -f "requirements.txt" ]; then
    semgrep --config=p/supply-chain --json --output=reports/semgrep/sca-results.json requirements.txt || true
    
    # Run safety check for Python dependencies
    if command -v safety &> /dev/null; then
        safety check --json --output=reports/security/safety-report.json || true
        safety check --output=reports/security/safety-report.txt || true
    fi
fi

show_step "Running secrets detection..."
semgrep --config=p/secrets --json --output=reports/semgrep/secrets-results.json . || true

show_step "Running Bandit for Python-specific security analysis..."
if command -v bandit &> /dev/null; then
    bandit -r src/ -f json -o reports/security/bandit-results.json || true
    bandit -r src/ -f txt -o reports/security/bandit-results.txt || true
fi

# Parse Semgrep results
show_step "Analyzing security findings..."
if [ -f "reports/semgrep/semgrep-results.json" ]; then
    CRITICAL_COUNT=$(python3 -c "
import json
try:
    with open('reports/semgrep/semgrep-results.json') as f:
        data = json.load(f)
    critical = sum(1 for r in data.get('results', []) if r.get('extra', {}).get('severity') == 'ERROR')
    print(critical)
except:
    print(0)
" 2>/dev/null || echo "0")

    HIGH_COUNT=$(python3 -c "
import json
try:
    with open('reports/semgrep/semgrep-results.json') as f:
        data = json.load(f)
    high = sum(1 for r in data.get('results', []) if r.get('extra', {}).get('severity') == 'WARNING')
    print(high)
except:
    print(0)
" 2>/dev/null || echo "0")

    MEDIUM_COUNT=$(python3 -c "
import json
try:
    with open('reports/semgrep/semgrep-results.json') as f:
        data = json.load(f)
    medium = sum(1 for r in data.get('results', []) if r.get('extra', {}).get('severity') == 'INFO')
    print(medium)
except:
    print(0)
" 2>/dev/null || echo "0")

    TOTAL_FINDINGS=$((CRITICAL_COUNT + HIGH_COUNT + MEDIUM_COUNT))
else
    CRITICAL_COUNT=0
    HIGH_COUNT=0
    MEDIUM_COUNT=0
    TOTAL_FINDINGS=0
fi

echo ""
echo "┌─────────────────────────────────┐"
echo "│      SECURITY FINDINGS          │"
echo "├─────────────────────────────────┤"
echo -e "│ Critical: ${RED}${CRITICAL_COUNT}${NC}                     │"
echo -e "│ High:     ${YELLOW}${HIGH_COUNT}${NC}                     │"
echo -e "│ Medium:   ${BLUE}${MEDIUM_COUNT}${NC}                     │"
echo -e "│ Total:    ${PURPLE}${TOTAL_FINDINGS}${NC}                     │"
echo "└─────────────────────────────────┘"

# Security gate checks
SECURITY_PASSED=true

if [ "$CRITICAL_COUNT" -gt "$SEMGREP_MAX_CRITICAL" ]; then
    show_error "Critical vulnerabilities: $CRITICAL_COUNT > $SEMGREP_MAX_CRITICAL"
    SECURITY_PASSED=false
    SECURITY_COLOR="red"
    SECURITY_MESSAGE="critical-issues"
else
    show_success "Critical vulnerabilities within threshold: $CRITICAL_COUNT <= $SEMGREP_MAX_CRITICAL"
fi

if [ "$HIGH_COUNT" -gt "$SEMGREP_MAX_HIGH" ]; then
    show_error "High severity issues: $HIGH_COUNT > $SEMGREP_MAX_HIGH"
    SECURITY_PASSED=false
    if [ "$SECURITY_COLOR" != "red" ]; then
        SECURITY_COLOR="orange"
        SECURITY_MESSAGE="high-issues"
    fi
else
    show_success "High severity issues within threshold: $HIGH_COUNT <= $SEMGREP_MAX_HIGH"
fi

if [ "$MEDIUM_COUNT" -gt "$SEMGREP_MAX_MEDIUM" ]; then
    show_warning "Medium severity issues: $MEDIUM_COUNT > $SEMGREP_MAX_MEDIUM (not blocking)"
    if [ "$SECURITY_COLOR" != "red" ] && [ "$SECURITY_COLOR" != "orange" ]; then
        SECURITY_COLOR="yellow"
        SECURITY_MESSAGE="medium-issues"
    fi
fi

# Set security status if all passed
if [ "$SECURITY_PASSED" = true ]; then
    if [ "$TOTAL_FINDINGS" -eq 0 ]; then
        SECURITY_COLOR="brightgreen"
        SECURITY_MESSAGE="secure"
    else
        SECURITY_COLOR="green"
        SECURITY_MESSAGE="low-risk"
    fi
fi

# ===============================
# STAGE 4: GENERATE REPORTS & BADGES
# ===============================
show_section "STAGE 4: GENERATING REPORTS & BADGES"

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

# Security badge
cat > reports/badges/security.json << EOF
{
  "schemaVersion": 1,
  "label": "security",
  "message": "${SECURITY_MESSAGE}",
  "color": "${SECURITY_COLOR}"
}
EOF

# Tests badge
if [ -f "reports/tests/junit.xml" ]; then
    FAILED_TESTS=$(grep -o 'failures="[^"]*"' reports/tests/junit.xml | grep -o '[0-9]*' || echo "0")
    ERROR_TESTS=$(grep -o 'errors="[^"]*"' reports/tests/junit.xml | grep -o '[0-9]*' || echo "0")
    
    if [ "$FAILED_TESTS" = "0" ] && [ "$ERROR_TESTS" = "0" ]; then
        TESTS_MESSAGE="passing"
        TESTS_COLOR="brightgreen"
        TESTS_PASSED=true
    else
        TESTS_MESSAGE="failing"
        TESTS_COLOR="red"
        TESTS_PASSED=false
    fi
else
    TESTS_MESSAGE="unknown"
    TESTS_COLOR="lightgrey"
    TESTS_PASSED=false
fi

cat > reports/badges/tests.json << EOF
{
  "schemaVersion": 1,
  "label": "tests",
  "message": "${TESTS_MESSAGE}",
  "color": "${TESTS_COLOR}"
}
EOF

# Generate comprehensive security summary
cat > reports/security/summary.json << EOF
{
  "total_findings": $TOTAL_FINDINGS,
  "critical_count": $CRITICAL_COUNT,
  "high_count": $HIGH_COUNT,
  "medium_count": $MEDIUM_COUNT,
  "security_gate_passed": $SECURITY_PASSED,
  "thresholds": {
    "max_critical": $SEMGREP_MAX_CRITICAL,
    "max_high": $SEMGREP_MAX_HIGH,
    "max_medium": $SEMGREP_MAX_MEDIUM
  },
  "timestamp": "$(date -Iseconds)",
  "tools_used": ["semgrep", "bandit", "safety"]
}
EOF

# ===============================
# STAGE 5: QUALITY GATE
# ===============================
show_section "STAGE 5: QUALITY GATE"

OVERALL_PASSED=true

echo "┌─────────────────────────────────────────────────┐"
echo "│                QUALITY GATE                     │"
echo "├─────────────────────────────────────────────────┤"

# Tests check
if [ "$TESTS_PASSED" = true ]; then
    echo -e "│ Tests:     ${GREEN}PASSED${NC}                           │"
else
    echo -e "│ Tests:     ${RED}FAILED${NC}                           │"
    OVERALL_PASSED=false
fi

# Coverage check
if [ "$COVERAGE_PASSED" = true ]; then
    echo -e "│ Coverage:  ${GREEN}PASSED${NC} (${COVERAGE_PERCENTAGE}%)                   │"
else
    echo -e "│ Coverage:  ${RED}FAILED${NC} (${COVERAGE_PERCENTAGE}% < ${COVERAGE_THRESHOLD}%)           │"
    OVERALL_PASSED=false
fi

# Pylint check
if [ "$PYLINT_PASSED" = true ]; then
    echo -e "│ Pylint:    ${GREEN}PASSED${NC} (${PYLINT_SCORE}/10)                 │"
else
    echo -e "│ Pylint:    ${RED}FAILED${NC} (${PYLINT_SCORE}/10 < ${PYLINT_THRESHOLD})            │"
    OVERALL_PASSED=false
fi

# Security check
if [ "$SECURITY_PASSED" = true ]; then
    echo -e "│ Security:  ${GREEN}PASSED${NC}                           │"
else
    echo -e "│ Security:  ${RED}FAILED${NC}                           │"
    OVERALL_PASSED=false
fi

echo "└─────────────────────────────────────────────────┘"

# Calculate pipeline duration
PIPELINE_END_TIME=$(date +%s)
PIPELINE_DURATION=$((PIPELINE_END_TIME - PIPELINE_START_TIME))

# Generate final quality gate report
cat > reports/quality-gate/summary.json << EOF
{
  "overall_passed": $OVERALL_PASSED,
  "tests_passed": $TESTS_PASSED,
  "coverage_passed": $COVERAGE_PASSED,
  "pylint_passed": $PYLINT_PASSED,
  "security_passed": $SECURITY_PASSED,
  "metrics": {
    "coverage_percentage": $COVERAGE_PERCENTAGE,
    "pylint_score": $PYLINT_SCORE,
    "security_critical": $CRITICAL_COUNT,
    "security_high": $HIGH_COUNT,
    "security_total": $TOTAL_FINDINGS
  },
  "thresholds": {
    "coverage_threshold": $COVERAGE_THRESHOLD,
    "pylint_threshold": $PYLINT_THRESHOLD,
    "security_max_critical": $SEMGREP_MAX_CRITICAL,
    "security_max_high": $SEMGREP_MAX_HIGH
  },
  "pipeline_duration_seconds": $PIPELINE_DURATION,
  "timestamp": "$(date -Iseconds)"
}
EOF

echo ""

# ===============================
# FINAL RESULT
# ===============================
if [ "$OVERALL_PASSED" = true ]; then
    show_section "PIPELINE SUCCESS"
    show_success "All quality gates passed! Ready to commit/deploy."
    echo ""
    echo -e "${BIGreen}📊 View Reports:${NC}"
    echo -e "   Coverage:  ${CYAN}reports/coverage/html/index.html${NC}"
    echo -e "   Tests:     ${CYAN}reports/tests/junit.xml${NC}"
    echo -e "   Pylint:    ${CYAN}reports/pylint/pylint-report.txt${NC}"
    echo -e "   Security:  ${CYAN}reports/semgrep/semgrep-results.txt${NC}"
    echo -e "   Summary:   ${CYAN}reports/quality-gate/summary.json${NC}"
    echo ""
    echo -e "${GREEN}Pipeline completed in ${PIPELINE_DURATION} seconds${NC}"
    exit 0
else
    show_section "PIPELINE FAILED"
    show_error "Quality gate failed! Fix issues before committing."
    echo ""
    echo -e "${BRed}🔧 Action Required:${NC}"
    
    if [ "$TESTS_PASSED" = false ]; then
        echo -e "   • Fix failing tests"
    fi
    
    if [ "$COVERAGE_PASSED" = false ]; then
        echo -e "   • Increase test coverage to ${COVERAGE_THRESHOLD}%+ (currently ${COVERAGE_PERCENTAGE}%)"
    fi
    
    if [ "$PYLINT_PASSED" = false ]; then
        echo -e "   • Improve code quality to reach ${PYLINT_THRESHOLD}+ pylint score (currently ${PYLINT_SCORE}/10)"
    fi
    
    if [ "$SECURITY_PASSED" = false ]; then
        echo -e "   • Fix security vulnerabilities (${CRITICAL_COUNT} critical, ${HIGH_COUNT} high)"
    fi
    
    echo ""
    echo -e "${RED}Pipeline failed after ${PIPELINE_DURATION} seconds${NC}"
    exit 1
fi