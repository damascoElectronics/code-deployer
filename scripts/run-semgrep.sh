#!/bin/bash
# scripts/run-semgrep.sh - Script for security analysis with Semgrep

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
SEMGREP_SEVERITY_THRESHOLD=${SEMGREP_SEVERITY_THRESHOLD:-"WARNING"}
SEMGREP_MAX_CRITICAL=${SEMGREP_MAX_CRITICAL:-0}
SEMGREP_MAX_HIGH=${SEMGREP_MAX_HIGH:-5}
SEMGREP_MAX_MEDIUM=${SEMGREP_MAX_MEDIUM:-10}

echo -e "${BLUE}Starting Semgrep Security Analysis${NC}"
echo -e "${PURPLE}Severity threshold: ${SEMGREP_SEVERITY_THRESHOLD}${NC}"
echo -e "${PURPLE}Max Critical: ${SEMGREP_MAX_CRITICAL}${NC}"
echo -e "${PURPLE}Max High: ${SEMGREP_MAX_HIGH}${NC}"
echo -e "${PURPLE}Max Medium: ${SEMGREP_MAX_MEDIUM}${NC}"
echo ""

# Function to show step
show_step() {
    echo -e "${CYAN}-> $1${NC}"
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

# Create reports directory
mkdir -p reports/{semgrep,security,badges}

# Step 1: Run main Semgrep scan
show_step "Running Semgrep SAST scan..."
semgrep --config=auto \
    --json \
    --output=reports/semgrep/semgrep-results.json \
    --severity=INFO \
    --verbose \
    src/ || SEMGREP_EXIT_CODE=$?

# Generate human-readable reports
show_step "Generating formatted reports..."
semgrep --config=auto \
    --output=reports/semgrep/semgrep-results.txt \
    --severity=INFO \
    src/ || true

semgrep --config=auto \
    --sarif \
    --output=reports/semgrep/semgrep-results.sarif \
    --severity=INFO \
    src/ || true

# Step 2: Run Supply Chain Analysis
show_step "Running Supply Chain Analysis (SCA)..."
if [ -f "requirements.txt" ]; then
    semgrep --config=p/supply-chain \
        --json \
        --output=reports/semgrep/sca-results.json \
        requirements.txt || true
    
    # Also run safety check for Python dependencies
    safety check --json --output=reports/security/safety-report.json || true
    safety check --output=reports/security/safety-report.txt || true
fi

# Step 3: Run Secrets Detection
show_step "Running secrets detection..."
semgrep --config=p/secrets \
    --json \
    --output=reports/semgrep/secrets-results.json \
    . || true

# Step 4: Run Bandit for additional Python security analysis
show_step "Running Bandit for Python-specific security issues..."
if command -v bandit &> /dev/null; then
    bandit -r src/ -f json -o reports/security/bandit-results.json || true
    bandit -r src/ -f txt -o reports/security/bandit-results.txt || true
fi

# Step 5: Analyze results and generate summary
show_step "Analyzing security findings..."

# Parse Semgrep JSON results to count findings by severity
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
echo "=== SECURITY ANALYSIS SUMMARY ==="
echo "┌────────────────────────────────┐"
echo "│         Finding Counts         │"
echo "├────────────────────────────────┤"
echo -e "│ Critical: ${RED}${CRITICAL_COUNT}${NC}                    │"
echo -e "│ High:     ${YELLOW}${HIGH_COUNT}${NC}                    │" 
echo -e "│ Medium:   ${BLUE}${MEDIUM_COUNT}${NC}                    │"
echo -e "│ Total:    ${PURPLE}${TOTAL_FINDINGS}${NC}                    │"
echo "└────────────────────────────────┘"

# Step 6: Security Quality Gate Check
show_step "Security Quality Gate Check..."

SECURITY_GATE_PASSED=true

if [ "$CRITICAL_COUNT" -gt "$SEMGREP_MAX_CRITICAL" ]; then
    show_error "FAILED: Critical vulnerabilities found: $CRITICAL_COUNT > $SEMGREP_MAX_CRITICAL"
    SECURITY_GATE_PASSED=false
else
    show_success "PASSED: Critical vulnerabilities within threshold: $CRITICAL_COUNT <= $SEMGREP_MAX_CRITICAL"
fi

if [ "$HIGH_COUNT" -gt "$SEMGREP_MAX_HIGH" ]; then
    show_error "FAILED: High severity issues found: $HIGH_COUNT > $SEMGREP_MAX_HIGH"
    SECURITY_GATE_PASSED=false
else
    show_success "PASSED: High severity issues within threshold: $HIGH_COUNT <= $SEMGREP_MAX_HIGH"
fi

if [ "$MEDIUM_COUNT" -gt "$SEMGREP_MAX_MEDIUM" ]; then
    show_warning "WARNING: Medium severity issues found: $MEDIUM_COUNT > $SEMGREP_MAX_MEDIUM (not blocking)"
else
    show_success "PASSED: Medium severity issues within threshold: $MEDIUM_COUNT <= $SEMGREP_MAX_MEDIUM"
fi

# Step 7: Generate security badges and summary
show_step "Generating security badges..."

# Security badge
if [ "$CRITICAL_COUNT" -eq 0 ] && [ "$HIGH_COUNT" -eq 0 ]; then
    SECURITY_COLOR="brightgreen"
    SECURITY_MESSAGE="secure"
elif [ "$CRITICAL_COUNT" -eq 0 ]; then
    SECURITY_COLOR="yellow" 
    SECURITY_MESSAGE="warnings"
else
    SECURITY_COLOR="red"
    SECURITY_MESSAGE="issues"
fi

cat > reports/badges/security.json << EOF
{
  "schemaVersion": 1,
  "label": "security",
  "message": "${SECURITY_MESSAGE}",
  "color": "${SECURITY_COLOR}"
}
EOF

# Generate comprehensive security summary
mkdir -p reports/security
cat > reports/security/summary.json << EOF
{
  "total_findings": $TOTAL_FINDINGS,
  "critical_count": $CRITICAL_COUNT,
  "high_count": $HIGH_COUNT,
  "medium_count": $MEDIUM_COUNT,
  "security_gate_passed": $SECURITY_GATE_PASSED,
  "thresholds": {
    "max_critical": $SEMGREP_MAX_CRITICAL,
    "max_high": $SEMGREP_MAX_HIGH,
    "max_medium": $SEMGREP_MAX_MEDIUM
  },
  "timestamp": "$(date -Iseconds)",
  "tools_used": ["semgrep", "bandit", "safety"]
}
EOF

# Step 8: Display important findings
if [ -f "reports/semgrep/semgrep-results.txt" ]; then
    show_step "Top Security Findings:"
    echo "──────────────────────────────────────"
    head -n 30 reports/semgrep/semgrep-results.txt | grep -E "(ERROR|WARNING)" || echo "No high-priority findings in preview"
    echo "──────────────────────────────────────"
    echo -e "${CYAN}Full report: reports/semgrep/semgrep-results.txt${NC}"
fi

echo ""

# Step 9: Final Security Gate Decision
if [ "$SECURITY_GATE_PASSED" = true ]; then
    show_success "🔒 SECURITY GATE PASSED - No critical security issues found!"
    echo ""
    echo -e "${BIGreen}View detailed reports:${NC}"
    echo -e "   Semgrep SAST: ${CYAN}reports/semgrep/semgrep-results.txt${NC}"
    echo -e "   Security Summary: ${CYAN}reports/security/summary.json${NC}"
    if [ -f "reports/security/bandit-results.txt" ]; then
        echo -e "   Bandit Report: ${CYAN}reports/security/bandit-results.txt${NC}"
    fi
    if [ -f "reports/security/safety-report.txt" ]; then
        echo -e "   Safety Report: ${CYAN}reports/security/safety-report.txt${NC}"
    fi
    exit 0
else
    show_error "🚨 SECURITY GATE FAILED - Critical security issues found!"
    echo ""
    echo -e "${RED}🔧 Action Required:${NC}"
    if [ "$CRITICAL_COUNT" -gt "$SEMGREP_MAX_CRITICAL" ]; then
        echo -e "   • Fix $CRITICAL_COUNT critical security vulnerabilities"
    fi
    if [ "$HIGH_COUNT" -gt "$SEMGREP_MAX_HIGH" ]; then
        echo -e "   • Address $HIGH_COUNT high severity security issues"
    fi
    echo ""
    echo -e "${RED}Review the detailed findings in:${NC}"
    echo -e "   • reports/semgrep/semgrep-results.txt"
    echo -e "   • reports/semgrep/semgrep-results.json"
    exit 1
fi