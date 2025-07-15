import SwiftUI
import AppKit
import Combine
import UserNotifications
import Foundation

@main
struct OpenDictApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    var body: some Scene {
        Settings {
            EmptyView()
        }
    }
}

class AppDelegate: NSObject, NSApplicationDelegate {
    private var statusItem: NSStatusItem!
    private var popover: NSPopover!
    private var menu: NSMenu!
    private var audioRecorder: AudioRecorder!
    private var accessibilityManager: AccessibilityManager!
    private var hotkeyManager: GlobalHotkeyManager!
    private var pythonServerProcess: Process?

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Start Python transcription server
        startPythonServer()

        // Create managers
        audioRecorder = AudioRecorder()
        accessibilityManager = AccessibilityManager()
        hotkeyManager = GlobalHotkeyManager()

        // Connect managers
        audioRecorder.accessibilityManager = accessibilityManager
        hotkeyManager.audioRecorder = audioRecorder
        hotkeyManager.setAccessibilityManager(accessibilityManager)

        // Create status item
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        updateStatusIcon()

        // Create menu
        createMenu()

        // Create popover
        popover = NSPopover()
        popover.contentSize = NSSize(width: 280, height: 220)
        popover.behavior = .transient
        popover.contentViewController = NSHostingController(
            rootView: MenuBarContentView()
                .environmentObject(audioRecorder)
                .environmentObject(accessibilityManager)
        )

        // Hide dock icon and prevent main window
        NSApp.setActivationPolicy(.accessory)

        // Observe recording state changes
        setupObservers()

        // Request notification permissions (after other setup)
        // requestNotificationPermissions() // Disabled for development
    }

    private func startPythonServer() {
        pythonServerProcess = Process()

        // Find the project directory by looking for key files
        let projectDir = findProjectDirectory()

        // Find Python interpreter
        let pythonPath = findPythonInterpreter(projectDir: projectDir)

        // Find the transcribe_server.py script
        let scriptPath = findTranscribeScript(projectDir: projectDir)

        guard let validPythonPath = pythonPath, let validScriptPath = scriptPath else {
            print("Failed to locate Python interpreter or transcribe_server.py script")
            print("Python path: \(pythonPath ?? "nil")")
            print("Script path: \(scriptPath ?? "nil")")
            print("Project directory: \(projectDir)")
            print("Current directory: \(FileManager.default.currentDirectoryPath)")
            print("Bundle path: \(Bundle.main.bundlePath)")
            return
        }

        print("Starting Python server...")
        print("Project directory: \(projectDir)")
        print("Python path: \(validPythonPath)")
        print("Script path: \(validScriptPath)")

        pythonServerProcess?.launchPath = validPythonPath
        pythonServerProcess?.arguments = [validScriptPath]
        pythonServerProcess?.currentDirectoryPath = projectDir

        // Set up environment variables
        var environment = ProcessInfo.processInfo.environment
        let venvBinPath = "\(projectDir)/venv/bin"
        if let existingPath = environment["PATH"] {
            environment["PATH"] = "\(venvBinPath):\(existingPath)"
        } else {
            environment["PATH"] = "\(venvBinPath):/usr/local/bin:/usr/bin:/bin"
        }
        pythonServerProcess?.environment = environment

        // Redirect output to capture logs
        let outputPipe = Pipe()
        let errorPipe = Pipe()
        pythonServerProcess?.standardOutput = outputPipe
        pythonServerProcess?.standardError = errorPipe

        // Read output asynchronously
        outputPipe.fileHandleForReading.readabilityHandler = { handle in
            let data = handle.availableData
            if !data.isEmpty {
                let output = String(data: data, encoding: .utf8) ?? ""
                print("Python server output: \(output)")
            }
        }

        errorPipe.fileHandleForReading.readabilityHandler = { handle in
            let data = handle.availableData
            if !data.isEmpty {
                let error = String(data: data, encoding: .utf8) ?? ""
                print("Python server error: \(error)")
            }
        }

        // Add termination handler to monitor server crashes
        pythonServerProcess?.terminationHandler = { [weak self] process in
            print("Python server terminated with status: \(process.terminationStatus)")
            if process.terminationStatus != 0 && process.terminationStatus != 15 { // Don't restart if killed intentionally
                DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
                    print("Attempting to restart crashed Python server...")
                    self?.startPythonServer()
                }
            }
        }

        do {
            try pythonServerProcess?.run()
            print("Python transcription server started successfully")

            // Wait for the server to be ready by checking if port is available
            waitForServerReady()
        } catch {
            print("Failed to start Python server: \(error)")
        }
    }

    private func findProjectDirectory() -> String {
        let fileManager = FileManager.default
        let currentDir = fileManager.currentDirectoryPath

        // Check if we're already in the project directory
        if fileManager.fileExists(atPath: "\(currentDir)/transcribe_server.py") &&
           fileManager.fileExists(atPath: "\(currentDir)/venv/bin/python") {
            return currentDir
        }

        // Try to find the project directory relative to the bundle
        let bundlePath = Bundle.main.bundlePath
        let bundleDir = URL(fileURLWithPath: bundlePath).deletingLastPathComponent().path

        // Check bundle parent directory
        if fileManager.fileExists(atPath: "\(bundleDir)/transcribe_server.py") &&
           fileManager.fileExists(atPath: "\(bundleDir)/venv/bin/python") {
            return bundleDir
        }

        // Check common development paths
        let possiblePaths = [
            currentDir,
            bundleDir,
            "\(NSHomeDirectory())/Downloads/Code/opendict",
            "\(NSHomeDirectory())/Development/opendict",
            "\(NSHomeDirectory())/Projects/opendict"
        ]

        for path in possiblePaths {
            if fileManager.fileExists(atPath: "\(path)/transcribe_server.py") &&
               fileManager.fileExists(atPath: "\(path)/venv/bin/python") {
                return path
            }
        }

        // Fall back to current directory
        return currentDir
    }

    private func findPythonInterpreter(projectDir: String) -> String? {
        let fileManager = FileManager.default

        // Priority order: project venv, current dir venv, system python
        let possiblePaths = [
            "\(projectDir)/venv/bin/python",
            "\(FileManager.default.currentDirectoryPath)/venv/bin/python",
            "/usr/bin/python3",
            "/usr/local/bin/python3"
        ]

        for path in possiblePaths {
            if fileManager.fileExists(atPath: path) {
                return path
            }
        }

        return nil
    }

    private func findTranscribeScript(projectDir: String) -> String? {
        let fileManager = FileManager.default

        // Priority order: project dir, current dir, bundle resources
        let possiblePaths = [
            "\(projectDir)/transcribe_server.py",
            "\(FileManager.default.currentDirectoryPath)/transcribe_server.py",
            Bundle.main.path(forResource: "transcribe_server", ofType: "py")
        ].compactMap { $0 }

        for path in possiblePaths {
            if fileManager.fileExists(atPath: path) {
                return path
            }
        }

        return nil
    }

    private func waitForServerReady() {
        // Check if server is ready by trying to connect to port 8765
        DispatchQueue.global(qos: .utility).async {
            var attempts = 0
            let maxAttempts = 30 // 30 seconds timeout

            while attempts < maxAttempts {
                let sock = Darwin.socket(AF_INET, SOCK_STREAM, 0)
                var addr = sockaddr_in()
                addr.sin_family = sa_family_t(AF_INET)
                addr.sin_port = UInt16(8765).bigEndian
                addr.sin_addr.s_addr = inet_addr("127.0.0.1")

                let result = withUnsafePointer(to: &addr) { pointer in
                    pointer.withMemoryRebound(to: sockaddr.self, capacity: 1) { sockaddrPointer in
                        Darwin.connect(sock, sockaddrPointer, socklen_t(MemoryLayout<sockaddr_in>.size))
                    }
                }

                Darwin.close(sock)

                if result == 0 {
                    print("Python server is ready!")
                    return
                }

                attempts += 1
                Thread.sleep(forTimeInterval: 1.0)
            }

            print("Warning: Python server may not be ready after \(maxAttempts) seconds")
        }
    }

    private func setupObservers() {
        // Watch for recording state changes
        audioRecorder.objectWillChange.sink { [weak self] _ in
            DispatchQueue.main.async {
                self?.updateStatusIcon()
                self?.updateMenu()
                self?.handlePopoverVisibility()
            }
        }.store(in: &cancellables)

        // Watch for accessibility permission changes
        accessibilityManager.objectWillChange.sink { [weak self] _ in
            DispatchQueue.main.async {
                self?.updateMenu()
            }
        }.store(in: &cancellables)
    }

    private var cancellables = Set<AnyCancellable>()

    private func requestNotificationPermissions() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound]) { granted, error in
            if let error = error {
                print("Failed to request notification permissions: \(error)")
            } else if granted {
                print("Notification permissions granted")
            }
        }
    }

    private func updateStatusIcon() {
        guard let button = statusItem.button else { return }

        if audioRecorder.isGlobalRecording {
            button.image = NSImage(systemSymbolName: "record.circle.fill", accessibilityDescription: "Recording")
            button.imagePosition = .imageOnly
        } else if audioRecorder.isTranscribing {
            button.image = NSImage(systemSymbolName: "doc.text.fill", accessibilityDescription: "Transcribing")
            button.imagePosition = .imageOnly
        } else {
            button.image = NSImage(systemSymbolName: "mic", accessibilityDescription: "OpenDict")
            button.imagePosition = .imageOnly
        }
    }

    private func updateMenu() {
        createMenu()
    }

    private func createMenu() {
        menu = NSMenu()

        // Status information
        let statusItem = NSMenuItem(title: getStatusText(), action: nil, keyEquivalent: "")
        statusItem.isEnabled = false
        menu.addItem(statusItem)

        menu.addItem(NSMenuItem.separator())

        // Accessibility permission item (if needed)
        if !accessibilityManager.hasAccessibilityPermissions {
            let accessibilityItem = NSMenuItem(title: "Grant Accessibility Permission", action: #selector(requestAccessibilityPermissions), keyEquivalent: "")
            accessibilityItem.target = self
            menu.addItem(accessibilityItem)
            menu.addItem(NSMenuItem.separator())
        }

        // Restart item
        let restartItem = NSMenuItem(title: "Restart OpenDict", action: #selector(restartApp), keyEquivalent: "")
        restartItem.target = self
        menu.addItem(restartItem)

        // Quit item
        let quitItem = NSMenuItem(title: "Quit OpenDict", action: #selector(quitApp), keyEquivalent: "q")
        quitItem.target = self
        menu.addItem(quitItem)

        // Set click action for status item
        self.statusItem.button?.target = self
        self.statusItem.button?.action = #selector(statusItemClicked)
    }

    private func getStatusText() -> String {
        if audioRecorder.isGlobalRecording {
            return "● Recording..."
        } else if audioRecorder.isTranscribing {
            return "● Transcribing..."
        } else if !accessibilityManager.hasAccessibilityPermissions {
            return "⚠️ Accessibility permission needed"
        } else {
            return "Hold Ctrl+Space to record"
        }
    }

    @objc func requestAccessibilityPermissions() {
        accessibilityManager.requestAccessibilityPermissions()
    }

    @objc func restartApp() {
        let url = URL(fileURLWithPath: Bundle.main.resourcePath!)
        let path = url.deletingLastPathComponent().deletingLastPathComponent().absoluteString
        let task = Process()
        task.launchPath = "/usr/bin/open"
        task.arguments = [path]
        task.launch()
        NSApplication.shared.terminate(nil)
    }

    @objc func quitApp() {
        // Shutdown audio recorder and transcription client
        audioRecorder?.shutdown()

        // Terminate Python server process
        pythonServerProcess?.terminate()
        pythonServerProcess = nil

        NSApplication.shared.terminate(nil)
    }

    func applicationWillTerminate(_ notification: Notification) {
        // Ensure cleanup on app termination
        audioRecorder?.shutdown()
        pythonServerProcess?.terminate()
    }

    @objc func statusItemClicked() {
        if let event = NSApp.currentEvent {
            if event.type == .rightMouseUp {
                // Right click shows menu
                self.statusItem.menu = menu
                self.statusItem.button?.performClick(nil)
                self.statusItem.menu = nil
            } else {
                // Left click shows popover
                togglePopover()
            }
        } else {
            togglePopover()
        }
    }

    @objc func togglePopover() {
        if popover.isShown {
            popover.performClose(nil)
        } else {
            if let button = statusItem.button {
                popover.show(relativeTo: button.bounds, of: button, preferredEdge: .minY)
            }
        }
    }

    private func handlePopoverVisibility() {
        let shouldShow = audioRecorder.isGlobalRecording || audioRecorder.isTranscribing

        if shouldShow && !popover.isShown {
            // Show popover when recording or transcribing starts
            if let button = statusItem.button {
                popover.show(relativeTo: button.bounds, of: button, preferredEdge: .minY)
            }
        } else if !shouldShow && popover.isShown {
            // Hide popover when both recording and transcribing are done
            popover.performClose(nil)
        }
    }
}
