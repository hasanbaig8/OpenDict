# Hello World macOS App

A simple macOS application built with SwiftUI that displays a "Hello World" window.

## Requirements

- macOS 13.0 or later
- Xcode 15.0 or later (or Swift 5.9+ command line tools)

## Building and Running

### Option 1: Using Swift Package Manager (Recommended)

1. Open Terminal and navigate to this directory
2. Build the app:
   ```bash
   swift build
   ```
3. Run the app:
   ```bash
   swift run
   ```

### Option 2: Using Xcode

1. Open the project in Xcode by double-clicking `Package.swift`
2. Select the "HelloWorldApp" target
3. Click the Run button (▶️) or press Cmd+R

## Features

- Clean, modern SwiftUI interface
- Properly sized window (300x200 pixels)
- Hidden title bar for a cleaner look
- Content-sized window that doesn't resize

## Project Structure

- `HelloWorldApp.swift` - Main app entry point
- `ContentView.swift` - Main view displaying "Hello World"
- `Info.plist` - App configuration and metadata
- `Package.swift` - Swift Package Manager configuration 