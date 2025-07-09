"""OpenDict Build and Distribution System.

Automated building, packaging, and distribution utilities.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from logging_config import get_logger


class BuildTarget(Enum):
    """Build target platforms."""

    MACOS = "macos"
    DEVELOPMENT = "development"
    RELEASE = "release"


class PackageFormat(Enum):
    """Package formats."""

    APP = "app"
    DMG = "dmg"
    ZIP = "zip"
    TAR_GZ = "tar.gz"


@dataclass
class BuildConfig:
    """Build configuration."""

    target: BuildTarget
    output_dir: str
    app_name: str
    version: str
    bundle_id: str
    sign_identity: Optional[str] = None
    notarize: bool = False
    include_python: bool = True
    include_venv: bool = True
    swift_build_config: str = "release"


class BuildError(Exception):
    """Build process error."""

    pass


class SwiftBuilder:
    """Swift application builder."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger()

    def build_swift_app(self, config: BuildConfig) -> str:
        """Build Swift application."""
        try:
            # Clean previous build
            if os.path.exists(".build"):
                shutil.rmtree(".build")

            # Build command
            cmd = [
                "swift",
                "build",
                "-c",
                config.swift_build_config,
                "--product",
                "OpenDict",
            ]

            self.logger.info(f"Building Swift app with command: {' '.join(cmd)}")

            # Run build
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")

            if result.returncode != 0:
                raise BuildError(f"Swift build failed: {result.stderr}")

            # Find executable
            executable_path = f".build/{config.swift_build_config}/OpenDict"
            if not os.path.exists(executable_path):
                raise BuildError(f"Executable not found: {executable_path}")

            self.logger.info(f"Swift build successful: {executable_path}")
            return executable_path

        except Exception as e:
            raise BuildError(f"Swift build failed: {str(e)}")


class PythonBundler:
    """Python environment bundler."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger()

    def create_python_bundle(self, output_dir: str, include_venv: bool = True) -> str:
        """Create Python bundle with dependencies."""
        try:
            bundle_dir = os.path.join(output_dir, "python")
            os.makedirs(bundle_dir, exist_ok=True)

            # Copy Python files
            python_files = [
                "transcribe_server.py",
                "transcribe.py",
                "config.py",
                "logging_config.py",
                "error_handling.py",
                "validation.py",
                "security.py",
                "monitoring.py",
            ]

            for file in python_files:
                if os.path.exists(file):
                    shutil.copy2(file, bundle_dir)
                    self.logger.info(f"Copied {file} to bundle")

            # Copy configuration
            if os.path.exists("config"):
                shutil.copytree("config", os.path.join(bundle_dir, "config"))
                self.logger.info("Copied config directory to bundle")

            # Handle virtual environment
            if include_venv and os.path.exists("venv"):
                venv_dest = os.path.join(bundle_dir, "venv")

                # Create minimal venv structure
                self._create_minimal_venv(venv_dest)
                self.logger.info("Created minimal Python environment")

            # Create requirements file
            self._create_bundle_requirements(bundle_dir)

            # Create startup script
            self._create_startup_script(bundle_dir)

            return bundle_dir

        except Exception as e:
            raise BuildError(f"Python bundle creation failed: {str(e)}")

    def _create_minimal_venv(self, venv_dest: str):
        """Create minimal virtual environment."""
        # Create directory structure
        os.makedirs(os.path.join(venv_dest, "bin"), exist_ok=True)
        os.makedirs(
            os.path.join(venv_dest, "lib", "python3.9", "site-packages"), exist_ok=True
        )

        # Copy essential packages
        source_site_packages = "venv/lib/python3.9/site-packages"
        dest_site_packages = os.path.join(
            venv_dest, "lib", "python3.9", "site-packages"
        )

        if os.path.exists(source_site_packages):
            # Copy only essential packages
            essential_packages = [
                "nemo_toolkit",
                "torch",
                "torchaudio",
                "librosa",
                "soundfile",
                "omegaconf",
                "hydra",
                "numpy",
                "scipy",
            ]

            for package in essential_packages:
                source_pkg = os.path.join(source_site_packages, package)
                if os.path.exists(source_pkg):
                    dest_pkg = os.path.join(dest_site_packages, package)
                    if os.path.isdir(source_pkg):
                        shutil.copytree(source_pkg, dest_pkg)
                    else:
                        shutil.copy2(source_pkg, dest_pkg)

        # Create Python executable symlink
        python_exe = os.path.join(venv_dest, "bin", "python")
        if not os.path.exists(python_exe):
            os.symlink(sys.executable, python_exe)

    def _create_bundle_requirements(self, bundle_dir: str):
        """Create requirements file for bundle."""
        requirements = [
            "nemo-toolkit[asr]>=1.23.0",
            "torch>=2.0.0",
            "torchaudio>=2.0.0",
            "librosa>=0.10.0",
            "soundfile>=0.12.0",
            "omegaconf>=2.3.0",
            "hydra-core>=1.3.0",
            "psutil>=5.9.0",
        ]

        requirements_path = os.path.join(bundle_dir, "requirements.txt")
        with open(requirements_path, "w") as f:
            f.write("\n".join(requirements))

    def _create_startup_script(self, bundle_dir: str):
        """Create startup script for Python server."""
        startup_script = """#!/bin/bash
# OpenDict Python Server Startup Script

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Set Python path
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Use bundled Python if available, otherwise system Python
if [ -f "$SCRIPT_DIR/venv/bin/python" ]; then
    PYTHON_EXE="$SCRIPT_DIR/venv/bin/python"
else
    PYTHON_EXE="python3"
fi

# Check if dependencies are installed
if ! $PYTHON_EXE -c "import nemo.collections.asr" 2>/dev/null; then
    echo "Installing Python dependencies..."
    $PYTHON_EXE -m pip install -r "$SCRIPT_DIR/requirements.txt"
fi

# Start transcription server
exec $PYTHON_EXE "$SCRIPT_DIR/transcribe_server.py" "$@"
"""

        script_path = os.path.join(bundle_dir, "start_server.sh")
        with open(script_path, "w") as f:
            f.write(startup_script)

        # Make executable
        os.chmod(script_path, 0o755)


class AppBundler:
    """macOS app bundle creator."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger()

    def create_app_bundle(
        self, config: BuildConfig, swift_executable: str, python_bundle: str
    ) -> str:
        """Create macOS app bundle."""
        try:
            app_path = os.path.join(config.output_dir, f"{config.app_name}.app")

            # Remove existing bundle
            if os.path.exists(app_path):
                shutil.rmtree(app_path)

            # Create bundle structure
            contents_dir = os.path.join(app_path, "Contents")
            macos_dir = os.path.join(contents_dir, "MacOS")
            resources_dir = os.path.join(contents_dir, "Resources")

            os.makedirs(macos_dir, exist_ok=True)
            os.makedirs(resources_dir, exist_ok=True)

            # Copy executable
            executable_dest = os.path.join(macos_dir, config.app_name)
            shutil.copy2(swift_executable, executable_dest)
            os.chmod(executable_dest, 0o755)

            # Copy Python bundle
            python_dest = os.path.join(resources_dir, "python")
            shutil.copytree(python_bundle, python_dest)

            # Copy icon
            if os.path.exists("OpenDict.icns"):
                shutil.copy2("OpenDict.icns", resources_dir)

            # Create Info.plist
            self._create_info_plist(contents_dir, config)

            # Create PkgInfo
            self._create_pkginfo(contents_dir)

            # Create launcher script
            self._create_launcher_script(macos_dir, config)

            self.logger.info(f"App bundle created: {app_path}")
            return app_path

        except Exception as e:
            raise BuildError(f"App bundle creation failed: {str(e)}")

    def _create_info_plist(self, contents_dir: str, config: BuildConfig):
        """Create Info.plist file."""
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>{config.app_name}</string>
    <key>CFBundleIdentifier</key>
    <string>{config.bundle_id}</string>
    <key>CFBundleName</key>
    <string>{config.app_name}</string>
    <key>CFBundleDisplayName</key>
    <string>{config.app_name}</string>
    <key>CFBundleVersion</key>
    <string>{config.version}</string>
    <key>CFBundleShortVersionString</key>
    <string>{config.version}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>LSMinimumSystemVersion</key>
    <string>13.0</string>
    <key>LSUIElement</key>
    <true/>
    <key>NSMicrophoneUsageDescription</key>
    <string>OpenDict needs microphone access to record audio for transcription.</string>
    <key>NSAppleEventsUsageDescription</key>
    <string>OpenDict needs Apple Events access to insert transcribed text.</string>
    <key>CFBundleIconFile</key>
    <string>OpenDict</string>
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.productivity</string>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2024 OpenDict. All rights reserved.</string>
</dict>
</plist>"""

        plist_path = os.path.join(contents_dir, "Info.plist")
        with open(plist_path, "w") as f:
            f.write(plist_content)

    def _create_pkginfo(self, contents_dir: str):
        """Create PkgInfo file."""
        pkginfo_path = os.path.join(contents_dir, "PkgInfo")
        with open(pkginfo_path, "w") as f:
            f.write("APPL????")

    def _create_launcher_script(self, macos_dir: str, config: BuildConfig):
        """Create launcher script."""
        launcher_content = f"""#!/bin/bash
# OpenDict Launcher Script

# Get bundle directory
BUNDLE_DIR="$(dirname "$0")/.."
RESOURCES_DIR="$BUNDLE_DIR/Resources"

# Set environment variables
export OPENDICT_BUNDLE_MODE=1
export OPENDICT_RESOURCES_DIR="$RESOURCES_DIR"

# Start Python server in background
"$RESOURCES_DIR/python/start_server.sh" &
PYTHON_PID=$!

# Start Swift app
"$BUNDLE_DIR/MacOS/{config.app_name}" "$@"

# Clean up Python server
kill $PYTHON_PID 2>/dev/null || true
"""

        launcher_path = os.path.join(macos_dir, f"{config.app_name}_launcher")
        with open(launcher_path, "w") as f:
            f.write(launcher_content)

        os.chmod(launcher_path, 0o755)


class PackageCreator:
    """Package creator for different formats."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger()

    def create_dmg(
        self, app_path: str, output_dir: str, app_name: str, version: str
    ) -> str:
        """Create DMG package."""
        try:
            dmg_path = os.path.join(output_dir, f"{app_name}-{version}.dmg")

            # Remove existing DMG
            if os.path.exists(dmg_path):
                os.remove(dmg_path)

            # Create temporary directory for DMG contents
            with tempfile.TemporaryDirectory() as temp_dir:
                # Copy app to temp directory
                temp_app_path = os.path.join(temp_dir, f"{app_name}.app")
                shutil.copytree(app_path, temp_app_path)

                # Create Applications symlink
                apps_link = os.path.join(temp_dir, "Applications")
                os.symlink("/Applications", apps_link)

                # Create README
                readme_path = os.path.join(temp_dir, "README.txt")
                with open(readme_path, "w") as f:
                    f.write(
                        f"""OpenDict {version}

Installation Instructions:
1. Drag OpenDict.app to the Applications folder
2. Launch OpenDict from Applications
3. Grant microphone and accessibility permissions when prompted

For more information, visit: https://github.com/opendict/opendict

Copyright © 2024 OpenDict. All rights reserved.
"""
                    )

                # Create DMG
                cmd = [
                    "hdiutil",
                    "create",
                    "-volname",
                    f"{app_name}",
                    "-srcfolder",
                    temp_dir,
                    "-ov",
                    "-format",
                    "UDZO",
                    dmg_path,
                ]

                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise BuildError(f"DMG creation failed: {result.stderr}")

            self.logger.info(f"DMG created: {dmg_path}")
            return dmg_path

        except Exception as e:
            raise BuildError(f"DMG creation failed: {str(e)}")

    def create_zip(
        self, app_path: str, output_dir: str, app_name: str, version: str
    ) -> str:
        """Create ZIP package."""
        try:
            zip_path = os.path.join(output_dir, f"{app_name}-{version}.zip")

            # Remove existing ZIP
            if os.path.exists(zip_path):
                os.remove(zip_path)

            # Create ZIP
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, _dirs, files in os.walk(app_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, os.path.dirname(app_path))
                        zipf.write(file_path, arcname)

            self.logger.info(f"ZIP created: {zip_path}")
            return zip_path

        except Exception as e:
            raise BuildError(f"ZIP creation failed: {str(e)}")


class DistributionBuilder:
    """Main distribution builder."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger()
        self.swift_builder = SwiftBuilder(logger)
        self.python_bundler = PythonBundler(logger)
        self.app_bundler = AppBundler(logger)
        self.package_creator = PackageCreator(logger)

    def build_distribution(
        self, config: BuildConfig, package_formats: List[PackageFormat]
    ) -> Dict[str, str]:
        """Build complete distribution."""
        try:
            # Create output directory
            os.makedirs(config.output_dir, exist_ok=True)

            results = {}

            # Build Swift application
            self.logger.info("Building Swift application...")
            swift_executable = self.swift_builder.build_swift_app(config)
            results["swift_executable"] = swift_executable

            # Create Python bundle
            if config.include_python:
                self.logger.info("Creating Python bundle...")
                python_bundle = self.python_bundler.create_python_bundle(
                    config.output_dir, config.include_venv
                )
                results["python_bundle"] = python_bundle

            # Create app bundle
            self.logger.info("Creating app bundle...")
            app_path = self.app_bundler.create_app_bundle(
                config,
                swift_executable,
                python_bundle if config.include_python else None,
            )
            results["app_bundle"] = app_path

            # Create packages
            for format in package_formats:
                self.logger.info(f"Creating {format.value} package...")

                if format == PackageFormat.DMG:
                    package_path = self.package_creator.create_dmg(
                        app_path, config.output_dir, config.app_name, config.version
                    )
                    results["dmg"] = package_path

                elif format == PackageFormat.ZIP:
                    package_path = self.package_creator.create_zip(
                        app_path, config.output_dir, config.app_name, config.version
                    )
                    results["zip"] = package_path

            self.logger.info("Distribution build completed successfully")
            return results

        except Exception as e:
            raise BuildError(f"Distribution build failed: {str(e)}")


def create_build_config(
    target: BuildTarget = BuildTarget.RELEASE,
    output_dir: str = "dist",
    app_name: str = "OpenDict",
    version: str = "1.0.0",
    bundle_id: str = "com.opendict.app",
) -> BuildConfig:
    """Create build configuration."""
    return BuildConfig(
        target=target,
        output_dir=output_dir,
        app_name=app_name,
        version=version,
        bundle_id=bundle_id,
    )


def main():
    """Main build script."""
    parser = argparse.ArgumentParser(description="OpenDict Build System")
    parser.add_argument(
        "--target", choices=["development", "release"], default="release"
    )
    parser.add_argument("--output-dir", default="dist")
    parser.add_argument("--app-name", default="OpenDict")
    parser.add_argument("--version", default="1.0.0")
    parser.add_argument("--bundle-id", default="com.opendict.app")
    parser.add_argument(
        "--format", choices=["app", "dmg", "zip"], action="append", default=[]
    )
    parser.add_argument(
        "--no-python", action="store_true", help="Don't include Python bundle"
    )
    parser.add_argument(
        "--no-venv", action="store_true", help="Don't include virtual environment"
    )

    args = parser.parse_args()

    # Default formats
    if not args.format:
        args.format = ["app", "dmg"]

    # Create build config
    config = BuildConfig(
        target=(
            BuildTarget.DEVELOPMENT
            if args.target == "development"
            else BuildTarget.RELEASE
        ),
        output_dir=args.output_dir,
        app_name=args.app_name,
        version=args.version,
        bundle_id=args.bundle_id,
        include_python=not args.no_python,
        include_venv=not args.no_venv,
        swift_build_config="debug" if args.target == "development" else "release",
    )

    # Create package formats
    package_formats = []
    for fmt in args.format:
        if fmt == "dmg":
            package_formats.append(PackageFormat.DMG)
        elif fmt == "zip":
            package_formats.append(PackageFormat.ZIP)

    # Build distribution
    try:
        builder = DistributionBuilder()
        results = builder.build_distribution(config, package_formats)

        print("Build completed successfully!")
        print("\nResults:")
        for key, value in results.items():
            print(f"  {key}: {value}")

    except BuildError as e:
        print(f"Build failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
