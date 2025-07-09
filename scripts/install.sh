#!/bin/bash

# OpenDict Installation Script
# Installs OpenDict from a distribution package

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
Usage: $0 [OPTIONS] [PACKAGE_FILE]

Install OpenDict from a package file.

OPTIONS:
    -d, --dest DIRECTORY        Installation directory (default: /Applications)
    -f, --force                 Force installation (overwrite existing)
    -u, --uninstall             Uninstall OpenDict
    -h, --help                  Show this help message

PACKAGE_FILE:
    Path to OpenDict package file (.dmg, .zip, or .app directory)
    If not specified, will look for package files in current directory

Examples:
    $0                          # Install from package in current directory
    $0 OpenDict.dmg             # Install from DMG file
    $0 OpenDict.zip             # Install from ZIP file
    $0 --uninstall              # Uninstall OpenDict
    $0 --force OpenDict.app     # Force install from app directory
EOF
}

# Default values
DEST_DIR="/Applications"
FORCE=false
UNINSTALL=false
PACKAGE_FILE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--dest)
            DEST_DIR="$2"
            shift 2
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -u|--uninstall)
            UNINSTALL=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        -*)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
        *)
            PACKAGE_FILE="$1"
            shift
            ;;
    esac
done

# Check if running on macOS
check_macos() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log_error "This installer is designed for macOS only."
        exit 1
    fi
}

# Check permissions
check_permissions() {
    if [[ ! -w "$DEST_DIR" ]]; then
        log_error "No write permission to $DEST_DIR"
        log_info "Please run with sudo or choose a different destination directory"
        exit 1
    fi
}

# Find package file
find_package() {
    if [[ -n "$PACKAGE_FILE" ]]; then
        if [[ ! -e "$PACKAGE_FILE" ]]; then
            log_error "Package file not found: $PACKAGE_FILE"
            exit 1
        fi
        return
    fi

    # Look for package files in current directory
    log_info "Looking for package files in current directory..."

    # Check for .dmg files
    if ls *.dmg 1> /dev/null 2>&1; then
        PACKAGE_FILE=$(ls *.dmg | head -n 1)
        log_info "Found DMG file: $PACKAGE_FILE"
        return
    fi

    # Check for .zip files
    if ls *.zip 1> /dev/null 2>&1; then
        PACKAGE_FILE=$(ls *.zip | head -n 1)
        log_info "Found ZIP file: $PACKAGE_FILE"
        return
    fi

    # Check for .app directories
    if ls *.app 1> /dev/null 2>&1; then
        PACKAGE_FILE=$(ls -d *.app | head -n 1)
        log_info "Found app directory: $PACKAGE_FILE"
        return
    fi

    log_error "No package file found. Please specify a package file."
    exit 1
}

# Install from DMG
install_dmg() {
    local dmg_file="$1"
    local mount_point="/tmp/opendict_install"

    log_info "Installing from DMG: $dmg_file"

    # Mount DMG
    log_info "Mounting DMG..."
    hdiutil attach "$dmg_file" -mountpoint "$mount_point" -quiet

    # Find .app bundle
    local app_path="$mount_point/OpenDict.app"
    if [[ ! -d "$app_path" ]]; then
        app_path=$(find "$mount_point" -name "*.app" -type d | head -n 1)
        if [[ -z "$app_path" ]]; then
            log_error "No .app bundle found in DMG"
            hdiutil detach "$mount_point" -quiet
            exit 1
        fi
    fi

    # Install app
    install_app "$app_path"

    # Unmount DMG
    log_info "Unmounting DMG..."
    hdiutil detach "$mount_point" -quiet
}

# Install from ZIP
install_zip() {
    local zip_file="$1"
    local temp_dir="/tmp/opendict_install"

    log_info "Installing from ZIP: $zip_file"

    # Extract ZIP
    log_info "Extracting ZIP..."
    rm -rf "$temp_dir"
    mkdir -p "$temp_dir"
    unzip -q "$zip_file" -d "$temp_dir"

    # Find .app bundle
    local app_path=$(find "$temp_dir" -name "*.app" -type d | head -n 1)
    if [[ -z "$app_path" ]]; then
        log_error "No .app bundle found in ZIP"
        rm -rf "$temp_dir"
        exit 1
    fi

    # Install app
    install_app "$app_path"

    # Clean up
    rm -rf "$temp_dir"
}

# Install app bundle
install_app() {
    local app_path="$1"
    local dest_path="$DEST_DIR/OpenDict.app"

    log_info "Installing app bundle: $app_path"

    # Check if app already exists
    if [[ -d "$dest_path" ]]; then
        if [[ "$FORCE" == false ]]; then
            log_warning "OpenDict already exists at $dest_path"
            read -p "Overwrite? [y/N] " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "Installation cancelled"
                exit 0
            fi
        fi

        log_info "Removing existing installation..."
        rm -rf "$dest_path"
    fi

    # Copy app bundle
    log_info "Copying app bundle to $dest_path"
    cp -R "$app_path" "$dest_path"

    # Set permissions
    chmod -R 755 "$dest_path"

    log_success "OpenDict installed successfully!"
}

# Uninstall OpenDict
uninstall_opendict() {
    local app_path="$DEST_DIR/OpenDict.app"

    log_info "Uninstalling OpenDict..."

    if [[ ! -d "$app_path" ]]; then
        log_warning "OpenDict not found at $app_path"
        return
    fi

    # Confirm uninstall
    read -p "Are you sure you want to uninstall OpenDict? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Uninstall cancelled"
        exit 0
    fi

    # Remove app bundle
    rm -rf "$app_path"

    # Remove user data (optional)
    read -p "Remove user data and cache? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$HOME/.opendict_cache"
        rm -rf "$HOME/Library/Preferences/com.opendict.app.plist"
        rm -rf "$HOME/Library/Application Support/OpenDict"
        log_info "User data removed"
    fi

    log_success "OpenDict uninstalled successfully!"
}

# Main installation function
install_opendict() {
    log_info "OpenDict Installation"
    log_info "Destination: $DEST_DIR"
    log_info "Force: $FORCE"
    echo

    check_macos
    check_permissions

    if [[ "$UNINSTALL" == true ]]; then
        uninstall_opendict
        return
    fi

    find_package

    # Determine file type and install
    case "$PACKAGE_FILE" in
        *.dmg)
            install_dmg "$PACKAGE_FILE"
            ;;
        *.zip)
            install_zip "$PACKAGE_FILE"
            ;;
        *.app)
            install_app "$PACKAGE_FILE"
            ;;
        *)
            log_error "Unsupported package format: $PACKAGE_FILE"
            log_info "Supported formats: .dmg, .zip, .app"
            exit 1
            ;;
    esac

    log_success "Installation completed!"
    log_info "You can now launch OpenDict from Applications or using Spotlight"
    log_info "Note: You may need to grant microphone and accessibility permissions"
}

# Run main function
install_opendict "$@"
