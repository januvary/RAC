#!/bin/bash

# RAC - Registros Alto Custo - Quality Check Script
# Comprehensive quality checks: pyright, mypy, ruff, black, pytest, coverage
# Additional: radon, vulture, refurb, deptry, pip-audit
# Usage: ./quality_check.sh [--quick]
#   --quick  : Skip slower checks (pyright, full test suite)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# Parse command line arguments
QUICK_MODE=false
for arg in "$@"; do
    case $arg in
        --quick)
            QUICK_MODE=true
            ;;
        -h|--help)
            echo "Usage: $0 [--quick]"
            echo "  --quick      Skip slower checks (pyright, full test suite)"
            echo "  -h, --help   Show this help message"
            exit 0
            ;;
    esac
done

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BOLD}${BLUE}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║      RAC - Registros Alto Custo - Quality Check Suite    ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Thresholds
COVERAGE_THRESHOLD=80

# Track results
PYRIGHT_STATUS="✅ PASS"
MYPY_STATUS="✅ PASS"
RUFF_STATUS="✅ PASS"
BLACK_STATUS="✅ PASS"
RADON_STATUS="✅ PASS"
VULTURE_STATUS="✅ PASS"
REFURB_STATUS="✅ PASS"
PYTEST_STATUS="✅ PASS"
COVERAGE_STATUS="✅ PASS"
BRANCH_COVERAGE_STATUS="✅ PASS"
DEPTRY_STATUS="✅ PASS"
PIPAUDIT_STATUS="✅ PASS"

# Initialize counters
PYRIGHT_ERRORS=0
MYPY_ERRORS=0
RUFF_ERRORS=0
BLACK_ISSUES=0
RADON_COMPLEX=0
VULTURE_ITEMS=0
REFURB_ITEMS=0
PYTEST_PASSED=0
PYTEST_FAILED=0
COVERAGE_PCT=0
BRANCH_COVERAGE_PCT=0
DEPTRY_ISSUES=0
PIPAUDIT_VULNS=0

# Function to print section header
print_header() {
    echo -e "\n${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${YELLOW}  $1${NC}"
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# Function to print result
print_result() {
    local tool=$1
    local status=$2
    local details=$3

    printf "${BOLD}%-15s${NC} %s %s\n" "$tool" "$status" "$details"
}

# =============================================================================
# Check 1: PYRIGHT - Type Checking (Strict)
# =============================================================================
print_header "1️⃣  PYRIGHT - Type Checking (Strict)"

if [ "$QUICK_MODE" = true ]; then
    PYRIGHT_STATUS="⏭️  SKIP"
    print_result "pyright" "⏭️  SKIP" "(quick mode)"
elif command -v pyright &> /dev/null; then
    PYRIGHT_OUTPUT=$(pyright src/ 2>&1)
    PYRIGHT_EXIT_CODE=$?

    PYRIGHT_ERRORS=$(echo "$PYRIGHT_OUTPUT" | grep -c " error " || echo 0)

    if [ "$PYRIGHT_EXIT_CODE" -eq 0 ]; then
        print_result "pyright" "✅ PASS" "(0 errors)"
    else
        PYRIGHT_STATUS="❌ FAIL"
        print_result "pyright" "❌ FAIL" "($PYRIGHT_ERRORS errors)"
        echo "$PYRIGHT_OUTPUT" | grep -E "error |warning "
    fi
else
    PYRIGHT_STATUS="⚠️  SKIP"
    print_result "pyright" "⚠️  SKIP" "(not installed)"
fi

# =============================================================================
# Check 2: MYPY - Type Checking (Fast)
# =============================================================================
print_header "2️⃣  MYPY - Type Checking (Fast)"

if command -v mypy &> /dev/null; then
    MYPY_OUTPUT=$(mypy src/ 2>&1)
    MYPY_EXIT_CODE=$?

    MYPY_ERRORS=$(echo "$MYPY_OUTPUT" | grep "error:" | wc -l)

    if [ "$MYPY_EXIT_CODE" -eq 0 ] && [ "$MYPY_ERRORS" -eq 0 ]; then
        print_result "mypy" "✅ PASS" "(0 errors)"
    else
        if [ "$MYPY_ERRORS" -gt 0 ]; then
            MYPY_STATUS="❌ FAIL"
            print_result "mypy" "❌ FAIL" "($MYPY_ERRORS errors)"
            echo "$MYPY_OUTPUT" | grep "error:"
        else
            print_result "mypy" "✅ PASS" "(0 errors)"
        fi
    fi
else
    MYPY_STATUS="⚠️  SKIP"
    print_result "mypy" "⚠️  SKIP" "(not installed)"
fi

# =============================================================================
# Check 3: RUFF - Linting
# =============================================================================
print_header "3️⃣  RUFF - Linting"

if command -v ruff &> /dev/null; then
    RUFF_OUTPUT=$(ruff check src/ tests/ 2>&1)
    RUFF_EXIT_CODE=$?

    if [ $RUFF_EXIT_CODE -eq 0 ]; then
        RUFF_ERRORS=0
        print_result "ruff" "✅ PASS" "(0 errors)"
    else
        RUFF_ERRORS=$(echo "$RUFF_OUTPUT" | grep -E "^src/|^tests/" | wc -l)
        if [ "$RUFF_ERRORS" -eq 0 ]; then
            RUFF_ERRORS=$(echo "$RUFF_OUTPUT" | grep -oP 'Found \K[0-9]+' || echo 0)
        fi
        RUFF_STATUS="❌ FAIL"
        print_result "ruff" "❌ FAIL" "($RUFF_ERRORS errors)"
        echo "$RUFF_OUTPUT" | head -30
    fi
else
    RUFF_STATUS="⚠️  SKIP"
    print_result "ruff" "⚠️  SKIP" "(not installed)"
fi

# =============================================================================
# Check 4: BLACK - Code Formatting
# =============================================================================
print_header "4️⃣  BLACK - Code Formatting"

if command -v black &> /dev/null; then
    BLACK_OUTPUT=$(black --check src/ tests/ 2>&1)
    BLACK_EXIT_CODE=$?

    if [ $BLACK_EXIT_CODE -eq 0 ]; then
        BLACK_ISSUES=0
        print_result "black" "✅ PASS" "(0 files need reformatting)"
    else
        BLACK_ISSUES=$(echo "$BLACK_OUTPUT" | grep -c "would reformat" || echo 0)
        if [ "$BLACK_ISSUES" -gt 0 ]; then
            BLACK_STATUS="❌ FAIL"
            print_result "black" "❌ FAIL" "($BLACK_ISSUES files need reformatting)"
            echo "$BLACK_OUTPUT" | grep "would reformat"
        else
            BLACK_STATUS="❌ FAIL"
            print_result "black" "❌ FAIL" "(formatting issues found)"
            echo "$BLACK_OUTPUT"
        fi
    fi
else
    BLACK_STATUS="⚠️  SKIP"
    print_result "black" "⚠️  SKIP" "(not installed)"
fi

# =============================================================================
# Check 5: RADON - Code Complexity
# =============================================================================
print_header "5️⃣  RADON - Code Complexity"

if command -v radon &> /dev/null; then
    RADON_OUTPUT=$(radon cc src/ -a -nc 2>&1)

    RADON_COMPLEX=$(echo "$RADON_OUTPUT" | grep -E "^\s+[A-Z]\s+[0-9]+:" | wc -l)
    RADON_AVG=$(echo "$RADON_OUTPUT" | grep -oP "Average complexity: \K[A-Z]" || echo "A")

    if [ "$RADON_COMPLEX" -eq 0 ]; then
        print_result "radon" "✅ PASS" "(avg complexity: $RADON_AVG)"
    else
        print_result "radon" "ℹ️  INFO" "($RADON_COMPLEX complex functions, avg: $RADON_AVG)"
        if [ "$RADON_COMPLEX" -le 10 ]; then
            echo "$RADON_OUTPUT"
        fi
    fi
else
    RADON_STATUS="⚠️  SKIP"
    print_result "radon" "⚠️  SKIP" "(not installed)"
fi

# =============================================================================
# Check 6: VULTURE - Dead Code Detection
# =============================================================================
print_header "6️⃣  VULTURE - Dead Code Detection"

if command -v vulture &> /dev/null; then
    if [ -f ".vulture_whitelist.py" ]; then
        VULTURE_OUTPUT=$(vulture src/ .vulture_whitelist.py --min-confidence 80 2>&1)
    else
        VULTURE_OUTPUT=$(vulture src/ --min-confidence 80 2>&1)
    fi

    if [ -z "$VULTURE_OUTPUT" ]; then
        VULTURE_ITEMS=0
        print_result "vulture" "✅ PASS" "(0 dead code items)"
    else
        VULTURE_ITEMS=$(echo "$VULTURE_OUTPUT" | grep -c . || echo 0)
        if [ "$VULTURE_ITEMS" -gt 0 ]; then
            VULTURE_STATUS="⚠️  WARN"
            print_result "vulture" "⚠️  WARN" "($VULTURE_ITEMS potential dead code items)"
            echo "$VULTURE_OUTPUT" | head -20
            if [ "$VULTURE_ITEMS" -gt 20 ]; then
                echo "  ... and $((VULTURE_ITEMS - 20)) more"
            fi
        else
            print_result "vulture" "✅ PASS" "(0 dead code items)"
        fi
    fi
else
    VULTURE_STATUS="⚠️  SKIP"
    print_result "vulture" "⚠️  SKIP" "(not installed)"
fi

# =============================================================================
# Check 7: REFURB - Code Modernization
# =============================================================================
print_header "7️⃣  REFURB - Code Modernization"

if command -v refurb &> /dev/null; then
    REFURB_OUTPUT=$(refurb src/ 2>&1)

    if [ -z "$REFURB_OUTPUT" ]; then
        REFURB_ITEMS=0
        print_result "refurb" "✅ PASS" "(0 modernization suggestions)"
    else
        REFURB_ITEMS=$(echo "$REFURB_OUTPUT" | grep -c . || echo 0)
        if [ "$REFURB_ITEMS" -gt 0 ]; then
            REFURB_STATUS="ℹ️  INFO"
            print_result "refurb" "ℹ️  INFO" "($REFURB_ITEMS modernization suggestions)"
            echo "$REFURB_OUTPUT"
        else
            print_result "refurb" "✅ PASS" "(0 modernization suggestions)"
        fi
    fi
else
    REFURB_STATUS="⚠️  SKIP"
    print_result "refurb" "⚠️  SKIP" "(not installed)"
fi

# =============================================================================
# Check 8: PYTEST + COVERAGE (with branch coverage)
# =============================================================================
print_header "8️⃣  PYTEST + COVERAGE - Test Suite"

PYTEST_ARGS="tests/ -v --cov=src --cov-branch --cov-report=term-missing --tb=short"

if [ "$QUICK_MODE" = true ]; then
    PYTEST_ARGS="tests/ --cov=src --cov-report=term --tb=short"
fi

if [ -f "venv/bin/pytest" ]; then
    PYTEST_OUTPUT=$(venv/bin/pytest $PYTEST_ARGS 2>&1)
    PYTEST_EXIT_CODE=$?

    PYTEST_PASSED=$(echo "$PYTEST_OUTPUT" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo 0)
    PYTEST_FAILED=$(echo "$PYTEST_OUTPUT" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo 0)

    TOTAL_LINE=$(echo "$PYTEST_OUTPUT" | grep -E '^TOTAL +')
    COVERAGE_PCT=$(echo "$TOTAL_LINE" | awk '{print $NF}' | tr -d '%' || echo 0)
    if [ -n "$TOTAL_LINE" ]; then
        BRANCHES_TOTAL=$(echo "$TOTAL_LINE" | awk '{print $4}')
        BRANCHES_PARTIAL=$(echo "$TOTAL_LINE" | awk '{print $5}')
        if [ -n "$BRANCHES_TOTAL" ] && [ "$BRANCHES_TOTAL" != "0" ]; then
            if [ -n "$BRANCHES_PARTIAL" ]; then
                BRANCH_COVERAGE_PCT=$(( ((BRANCHES_TOTAL - BRANCHES_PARTIAL) * 100) / BRANCHES_TOTAL ))
            else
                BRANCH_COVERAGE_PCT=100
            fi
        else
            BRANCH_COVERAGE_PCT=0
        fi
    fi

    if [ $PYTEST_FAILED -gt 0 ]; then
        PYTEST_STATUS="❌ FAIL"
        print_result "pytest" "❌ FAIL" "($PYTEST_PASSED passed, $PYTEST_FAILED failed)"
    else
        print_result "pytest" "✅ PASS" "($PYTEST_PASSED tests passed)"
    fi

    if [ -n "$COVERAGE_PCT" ] && [ "$COVERAGE_PCT" -lt "$COVERAGE_THRESHOLD" ]; then
        COVERAGE_STATUS="⚠️  WARN"
        print_result "coverage" "⚠️  WARN" "($COVERAGE_PCT% line coverage, need $COVERAGE_THRESHOLD%)"
    elif [ -n "$COVERAGE_PCT" ]; then
        print_result "coverage" "✅ PASS" "($COVERAGE_PCT% line coverage)"
    fi

    if [ -n "$BRANCH_COVERAGE_PCT" ]; then
        if [ "$BRANCH_COVERAGE_PCT" -lt "$COVERAGE_THRESHOLD" ]; then
            BRANCH_COVERAGE_STATUS="⚠️  WARN"
            print_result "branch-cov" "⚠️  WARN" "($BRANCH_COVERAGE_PCT% branch coverage)"
        else
            print_result "branch-cov" "✅ PASS" "($BRANCH_COVERAGE_PCT% branch coverage)"
        fi
    fi
elif command -v pytest &> /dev/null; then
    PYTEST_OUTPUT=$(pytest $PYTEST_ARGS 2>&1)
    PYTEST_EXIT_CODE=$?

    PYTEST_PASSED=$(echo "$PYTEST_OUTPUT" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo 0)
    PYTEST_FAILED=$(echo "$PYTEST_OUTPUT" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo 0)

    TOTAL_LINE=$(echo "$PYTEST_OUTPUT" | grep -E '^TOTAL +')
    COVERAGE_PCT=$(echo "$TOTAL_LINE" | awk '{print $NF}' | tr -d '%' || echo 0)
    if [ -n "$TOTAL_LINE" ]; then
        BRANCHES_TOTAL=$(echo "$TOTAL_LINE" | awk '{print $4}')
        BRANCHES_PARTIAL=$(echo "$TOTAL_LINE" | awk '{print $5}')
        if [ -n "$BRANCHES_TOTAL" ] && [ "$BRANCHES_TOTAL" != "0" ]; then
            if [ -n "$BRANCHES_PARTIAL" ]; then
                BRANCH_COVERAGE_PCT=$(( ((BRANCHES_TOTAL - BRANCHES_PARTIAL) * 100) / BRANCHES_TOTAL ))
            else
                BRANCH_COVERAGE_PCT=100
            fi
        else
            BRANCH_COVERAGE_PCT=0
        fi
    fi

    if [ $PYTEST_FAILED -gt 0 ]; then
        PYTEST_STATUS="❌ FAIL"
        print_result "pytest" "❌ FAIL" "($PYTEST_PASSED passed, $PYTEST_FAILED failed)"
    else
        print_result "pytest" "✅ PASS" "($PYTEST_PASSED tests passed)"
    fi

    if [ -n "$COVERAGE_PCT" ] && [ "$COVERAGE_PCT" -lt "$COVERAGE_THRESHOLD" ]; then
        COVERAGE_STATUS="⚠️  WARN"
        print_result "coverage" "⚠️  WARN" "($COVERAGE_PCT% line coverage, need $COVERAGE_THRESHOLD%)"
    elif [ -n "$COVERAGE_PCT" ]; then
        print_result "coverage" "✅ PASS" "($COVERAGE_PCT% line coverage)"
    fi

    if [ -n "$BRANCH_COVERAGE_PCT" ]; then
        if [ "$BRANCH_COVERAGE_PCT" -lt "$COVERAGE_THRESHOLD" ]; then
            BRANCH_COVERAGE_STATUS="⚠️  WARN"
            print_result "branch-cov" "⚠️  WARN" "($BRANCH_COVERAGE_PCT% branch coverage)"
        else
            print_result "branch-cov" "✅ PASS" "($BRANCH_COVERAGE_PCT% branch coverage)"
        fi
    fi
else
    PYTEST_STATUS="⚠️  SKIP"
    COVERAGE_STATUS="⚠️  SKIP"
    print_result "pytest" "⚠️  SKIP" "(not installed)"
fi

# =============================================================================
# Check 9: DEPTRY - Dependency Analysis
# =============================================================================
print_header "9️⃣  DEPTRY - Dependency Analysis"

if command -v deptry &> /dev/null; then
    DEPTRY_OUTPUT=$(deptry . 2>&1)
    DEPTRY_EXIT_CODE=$?

    if [ $DEPTRY_EXIT_CODE -eq 0 ]; then
        DEPTRY_ISSUES=0
        print_result "deptry" "✅ PASS" "(0 dependency issues)"
    else
        DEPTRY_ISSUES=$(echo "$DEPTRY_OUTPUT" | grep -E "^(Unused|Missing)" | wc -l)
        if [ "$DEPTRY_ISSUES" -gt 0 ]; then
            DEPTRY_STATUS="⚠️  WARN"
            print_result "deptry" "⚠️  WARN" "($DEPTRY_ISSUES dependency issues)"
            echo "$DEPTRY_OUTPUT"
        else
            print_result "deptry" "✅ PASS" "(0 dependency issues)"
        fi
    fi
else
    DEPTRY_STATUS="⚠️  SKIP"
    print_result "deptry" "⚠️  SKIP" "(not installed)"
fi

# =============================================================================
# Check 10: PIP-AUDIT - Dependency Security
# =============================================================================
print_header "1️⃣0️⃣  PIP-AUDIT - Dependency Security"

if [ -f "venv/bin/pip-audit" ]; then
    PIPAUDIT_OUTPUT=$(venv/bin/pip-audit 2>&1 || true)

    if echo "$PIPAUDIT_OUTPUT" | grep -q "No known vulnerabilities"; then
        PIPAUDIT_VULNS=0
        print_result "pip-audit" "✅ PASS" "(0 vulnerabilities)"
    elif echo "$PIPAUDIT_OUTPUT" | grep -qE "(CVE-|PYSEC-|GHSA-)"; then
        PIPAUDIT_VULNS=$(echo "$PIPAUDIT_OUTPUT" | grep -cE "(CVE-|PYSEC-|GHSA-)" || echo 0)
        PIPAUDIT_STATUS="⚠️  WARN"
        print_result "pip-audit" "⚠️  WARN" "($PIPAUDIT_VULNS vulnerabilities)"
        echo "$PIPAUDIT_OUTPUT" | grep -E "Name|CVE-|PYSEC-|GHSA-"
    else
        print_result "pip-audit" "✅ PASS" "(0 vulnerabilities)"
    fi
elif command -v pip-audit &> /dev/null; then
    PIPAUDIT_OUTPUT=$(pip-audit 2>&1 || true)

    if echo "$PIPAUDIT_OUTPUT" | grep -q "No known vulnerabilities"; then
        PIPAUDIT_VULNS=0
        print_result "pip-audit" "✅ PASS" "(0 vulnerabilities)"
    elif echo "$PIPAUDIT_OUTPUT" | grep -qE "(CVE-|PYSEC-|GHSA-)"; then
        PIPAUDIT_VULNS=$(echo "$PIPAUDIT_OUTPUT" | grep -cE "(CVE-|PYSEC-|GHSA-)" || echo 0)
        PIPAUDIT_STATUS="⚠️  WARN"
        print_result "pip-audit" "⚠️  WARN" "($PIPAUDIT_VULNS vulnerabilities)"
        echo "$PIPAUDIT_OUTPUT" | grep -E "Name|CVE-|PYSEC-|GHSA-"
    else
        print_result "pip-audit" "✅ PASS" "(0 vulnerabilities)"
    fi
else
    PIPAUDIT_STATUS="⚠️  SKIP"
    print_result "pip-audit" "⚠️  SKIP" "(not installed)"
fi

# =============================================================================
# Summary Report
# =============================================================================
echo -e "\n${BOLD}${BLUE}"
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                        ║"
echo "║                    📊 SUMMARY REPORT 📊                ║"
echo "║                                                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "\n${BOLD}Type Checking:${NC}"
echo -e "${BOLD}┌────────────────┬──────────────┬───────────────────┐${NC}"
echo -e "${BOLD}│ CHECK           │ STATUS       │ DETAILS           │${NC}"
echo -e "${BOLD}├────────────────┼──────────────┼───────────────────┤${NC}"
printf "│ %-15s │ %-12s │ %-17s │\n" "pyright" "$PYRIGHT_STATUS" "$PYRIGHT_ERRORS errors"
printf "│ %-15s │ %-12s │ %-17s │\n" "mypy" "$MYPY_STATUS" "$MYPY_ERRORS errors"
echo -e "${BOLD}└────────────────┴──────────────┴───────────────────┘${NC}"

echo -e "\n${BOLD}Static Analysis:${NC}"
echo -e "${BOLD}┌────────────────┬──────────────┬───────────────────┐${NC}"
echo -e "${BOLD}│ CHECK           │ STATUS       │ DETAILS           │${NC}"
echo -e "${BOLD}├────────────────┼──────────────┼───────────────────┤${NC}"
printf "│ %-15s │ %-12s │ %-17s │\n" "ruff" "$RUFF_STATUS" "$RUFF_ERRORS errors"
printf "│ %-15s │ %-12s │ %-17s │\n" "black" "$BLACK_STATUS" "$BLACK_ISSUES files"
echo -e "${BOLD}└────────────────┴──────────────┴───────────────────┘${NC}"

echo -e "\n${BOLD}Code Quality:${NC}"
echo -e "${BOLD}┌────────────────┬──────────────┬───────────────────┐${NC}"
echo -e "${BOLD}│ CHECK           │ STATUS       │ DETAILS           │${NC}"
echo -e "${BOLD}├────────────────┼──────────────┼───────────────────┤${NC}"
printf "│ %-15s │ %-12s │ %-17s │\n" "radon" "$RADON_STATUS" "info only"
printf "│ %-15s │ %-12s │ %-17s │\n" "vulture" "$VULTURE_STATUS" "$VULTURE_ITEMS items"
printf "│ %-15s │ %-12s │ %-17s │\n" "refurb" "$REFURB_STATUS" "$REFURB_ITEMS suggestions"
echo -e "${BOLD}└────────────────┴──────────────┴───────────────────┘${NC}"

echo -e "\n${BOLD}Testing & Coverage:${NC}"
echo -e "${BOLD}┌────────────────┬──────────────┬───────────────────┐${NC}"
echo -e "${BOLD}│ CHECK           │ STATUS       │ DETAILS           │${NC}"
echo -e "${BOLD}├────────────────┼──────────────┼───────────────────┤${NC}"
printf "│ %-15s │ %-12s │ %-17s │\n" "pytest" "$PYTEST_STATUS" "$PYTEST_PASSED tests"
printf "│ %-15s │ %-12s │ %-17s │\n" "coverage" "$COVERAGE_STATUS" "$COVERAGE_PCT%"
printf "│ %-15s │ %-12s │ %-17s │\n" "branch-cov" "$BRANCH_COVERAGE_STATUS" "$BRANCH_COVERAGE_PCT%"
echo -e "${BOLD}└────────────────┴──────────────┴───────────────────┘${NC}"

echo -e "\n${BOLD}Dependencies:${NC}"
echo -e "${BOLD}┌────────────────┬──────────────┬───────────────────┐${NC}"
echo -e "${BOLD}│ CHECK           │ STATUS       │ DETAILS           │${NC}"
echo -e "${BOLD}├────────────────┼──────────────┼───────────────────┤${NC}"
printf "│ %-15s │ %-12s │ %-17s │\n" "deptry" "$DEPTRY_STATUS" "$DEPTRY_ISSUES issues"
printf "│ %-15s │ %-12s │ %-17s │\n" "pip-audit" "$PIPAUDIT_STATUS" "$PIPAUDIT_VULNS vulns"
echo -e "${BOLD}└────────────────┴──────────────┴───────────────────┘${NC}"

# Overall status
FAILED=0
WARNINGS=0

# Type Checking (blocking)
if [[ "$PYRIGHT_STATUS" == *"FAIL"* ]]; then ((FAILED++)); fi
if [[ "$MYPY_STATUS" == *"FAIL"* ]]; then ((FAILED++)); fi

# Static Analysis (blocking)
if [[ "$RUFF_STATUS" == *"FAIL"* ]]; then ((FAILED++)); fi
if [[ "$BLACK_STATUS" == *"FAIL"* ]]; then ((FAILED++)); fi

# Code Quality (warnings)
if [[ "$VULTURE_STATUS" == *"WARN"* ]] || [[ "$VULTURE_STATUS" == *"SKIP"* ]]; then ((WARNINGS++)); fi
if [[ "$REFURB_STATUS" == *"WARN"* ]] || [[ "$REFURB_STATUS" == *"SKIP"* ]]; then ((WARNINGS++)); fi
if [[ "$RADON_STATUS" == *"WARN"* ]] || [[ "$RADON_STATUS" == *"SKIP"* ]]; then ((WARNINGS++)); fi

# Testing & Coverage
if [[ "$PYTEST_STATUS" == *"FAIL"* ]]; then ((FAILED++)); fi
if [[ "$COVERAGE_STATUS" == *"WARN"* ]] || [[ "$COVERAGE_STATUS" == *"SKIP"* ]]; then ((WARNINGS++)); fi
if [[ "$BRANCH_COVERAGE_STATUS" == *"WARN"* ]] || [[ "$BRANCH_COVERAGE_STATUS" == *"SKIP"* ]]; then ((WARNINGS++)); fi
if [[ "$DEPTRY_STATUS" == *"WARN"* ]] || [[ "$DEPTRY_STATUS" == *"SKIP"* ]]; then ((WARNINGS++)); fi
if [[ "$PIPAUDIT_STATUS" == *"WARN"* ]] || [[ "$PIPAUDIT_STATUS" == *"SKIP"* ]]; then ((WARNINGS++)); fi

# Skips are warnings
if [[ "$PYRIGHT_STATUS" == *"SKIP"* ]]; then ((WARNINGS++)); fi
if [[ "$MYPY_STATUS" == *"SKIP"* ]]; then ((WARNINGS++)); fi
if [[ "$RUFF_STATUS" == *"SKIP"* ]]; then ((WARNINGS++)); fi
if [[ "$BLACK_STATUS" == *"SKIP"* ]]; then ((WARNINGS++)); fi
if [[ "$PYTEST_STATUS" == *"SKIP"* ]]; then ((WARNINGS++)); fi

echo ""
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}${BOLD}❌ QUALITY CHECK FAILED${NC}"
    echo -e "${RED}   $FAILED check(s) failed, $WARNINGS warning(s)${NC}"
    echo ""
    echo -e "${YELLOW}Fix commands:${NC}"
    echo -e "  ${CYAN}ruff check src/ tests/ --fix${NC}  # Fix linting issues"
    echo -e "  ${CYAN}black src/ tests/${NC}             # Format code"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}${BOLD}⚠️  QUALITY CHECK PASSED WITH WARNINGS${NC}"
    echo -e "${YELLOW}   $WARNINGS warning(s) found${NC}"
    exit 0
else
    echo -e "${GREEN}${BOLD}✅ ALL QUALITY CHECKS PASSED${NC}"
    echo -e "${GREEN}   Your codebase is production-ready!${NC}"
    exit 0
fi
