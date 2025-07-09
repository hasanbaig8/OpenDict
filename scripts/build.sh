#!/bin/bash

# OpenDict Build Script
# Builds OpenDict for distribution

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TARGET="release"
OUTPUT_DIR="dist"
APP_NAME="OpenDict"
VERSION="1.0.0"
BUNDLE_ID="com.opendict.app"
FORMATS=("app" "dmg")
INCLUDE_PYTHON=true
INCLUDE_VENV=true
CLEAN=false

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Build OpenDict for distribution.

OPTIONS:
    -t, --target TARGET         Build target: development, release (default: release)
    -o, --output-dir DIR        Output directory (default: dist)
    -n, --app-name NAME         Application name (default: OpenDict)
    -v, --version VERSION       Version string (default: 1.0.0)
    -b, --bundle-id ID          Bundle identifier (default: com.opendict.app)
    -f, --format FORMAT         Package format: app, dmg, zip (can be specified multiple times)
    --no-python                 Don't include Python bundle
    --no-venv                   Don't include virtual environment
    -c, --clean                 Clean build directory before building
    -h, --help                  Show this help message

Examples:
    $0                          # Build release with default settings
    $0 -t development           # Build development version
    $0 -f dmg -f zip            # Build DMG and ZIP packages
    $0 --clean                  # Clean build and rebuild
    $0 --no-python              # Build without Python bundle
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--target)
            TARGET="$2"
            shift 2
            ;;
        -o|--output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -n|--app-name)
            APP_NAME="$2"
            shift 2
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -b|--bundle-id)
            BUNDLE_ID="$2"
            shift 2
            ;;
        -f|--format)
            FORMATS+=("$2")
            shift 2
            ;;
        --no-python)
            INCLUDE_PYTHON=false
            shift
            ;;
        --no-venv)
            INCLUDE_VENV=false
            shift
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate target
if [[ "$TARGET" != "development" && "$TARGET" != "release" ]]; then
    log_error "Invalid target: $TARGET. Must be 'development' or 'release'"
    exit 1
fi

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."

    # Check Swift
    if ! command -v swift &> /dev/null; then
        log_error "Swift not found. Please install Xcode or Swift toolchain."
        exit 1
    fi

    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 not found. Please install Python 3.8 or later."
        exit 1
    fi

    # Check virtual environment
    if [[ "$INCLUDE_PYTHON" == true && ! -d "venv" ]]; then
        log_warning "Virtual environment not found. Run 'make setup' first."
        # Try to create it
        log_info "Creating virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    fi

    # Check for hdiutil on macOS (for DMG creation)
    if [[ " ${FORMATS[*]} " =~ " dmg " ]]; then
        if ! command -v hdiutil &> /dev/null; then
            log_error "hdiutil not found. DMG creation requires macOS."
            exit 1
        fi
    fi

    log_success "Dependencies check passed"
}

# Clean build directory
clean_build() {
    if [[ "$CLEAN" == true ]]; then
        log_info "Cleaning build directory..."
        rm -rf "$OUTPUT_DIR"
        rm -rf ".build"
        log_success "Build directory cleaned"
    fi
}

# Build distribution
build_distribution() {
    log_info "Starting build process..."

    # Prepare Python arguments
    PYTHON_ARGS=(
        "--target" "$TARGET"
        "--output-dir" "$OUTPUT_DIR"
        "--app-name" "$APP_NAME"
        "--version" "$VERSION"
        "--bundle-id" "$BUNDLE_ID"
    )

    # Add formats
    for format in "${FORMATS[@]}"; do
        PYTHON_ARGS+=("--format" "$format")
    done

    # Add Python options
    if [[ "$INCLUDE_PYTHON" == false ]]; then
        PYTHON_ARGS+=("--no-python")
    fi

    if [[ "$INCLUDE_VENV" == false ]]; then
        PYTHON_ARGS+=("--no-venv")
    fi

    # Run Python build script
    log_info "Running build script with arguments: ${PYTHON_ARGS[*]}"
    python3 build.py "${PYTHON_ARGS[@]}"

    log_success "Build completed successfully!"
}

# Show build results
show_results() {
    log_info "Build results:"

    if [[ -d "$OUTPUT_DIR" ]]; then
        find "$OUTPUT_DIR" -type f -name "*.app" -o -name "*.dmg" -o -name "*.zip" | while read -r file; do
            size=$(du -h "$file" | cut -f1)
            log_success "  $file ($size)"
        done
    fi
}

# Main execution
main() {
    log_info "OpenDict Build System"
    log_info "Target: $TARGET"
    log_info "Output Directory: $OUTPUT_DIR"
    log_info "App Name: $APP_NAME"
    log_info "Version: $VERSION"
    log_info "Bundle ID: $BUNDLE_ID"
    log_info "Formats: ${FORMATS[*]}"
    log_info "Include Python: $INCLUDE_PYTHON"
    log_info "Include Venv: $INCLUDE_VENV"
    log_info "Clean: $CLEAN"
    echo

    check_dependencies
    clean_build
    build_distribution
    show_results

    log_success "Build process completed!"
}

# Run main function
main "$@"
