import SwiftUI
import AppKit
import Combine
import UserNotifications

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
        // Request notification permissions
        requestNotificationPermissions()

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
    }

    private func startPythonServer() {
        pythonServerProcess = Process()
        let bundle = Bundle.main
        let pythonPath = bundle.path(forResource: "venv/bin/python", ofType: nil) ?? "/Users/hasanbaig/Downloads/Code/opendict/venv/bin/python"
        let scriptPath = bundle.path(forResource: "transcribe_server", ofType: "py") ?? "/Users/hasanbaig/Downloads/Code/opendict/transcribe_server.py"

        pythonServerProcess?.launchPath = pythonPath
        pythonServerProcess?.arguments = [scriptPath]

        // Redirect output to avoid blocking
        let pipe = Pipe()
        pythonServerProcess?.standardOutput = pipe
        pythonServerProcess?.standardError = pipe

        do {
            try pythonServerProcess?.run()
            print("Python transcription server started")

            // Give the Python server time to start up
            DispatchQueue.global(qos: .utility).asyncAfter(deadline: .now() + 2.0) {
                print("Python server should be ready now")
            }
        } catch {
            print("Failed to start Python server: \(error)")
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
