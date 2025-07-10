import Foundation
import Cocoa
import Carbon
import Combine

class GlobalHotkeyManager: ObservableObject {
    @Published var isHotkeyPressed = false
    private var monitors: [Any] = []
    private var isSetup = false

    weak var audioRecorder: AudioRecorder?
    weak var accessibilityManager: AccessibilityManager?

    init() {
        setupGlobalHotkey()
    }

    deinit {
        cleanup()
    }

    func setAccessibilityManager(_ manager: AccessibilityManager) {
        self.accessibilityManager = manager

        // Listen for permission changes
        manager.objectWillChange.sink { [weak self] _ in
            DispatchQueue.main.async {
                self?.handlePermissionChange()
            }
        }.store(in: &cancellables)
    }

    private var cancellables = Set<AnyCancellable>()

    private func handlePermissionChange() {
        guard let accessibilityManager = accessibilityManager else { return }

        if accessibilityManager.hasAccessibilityPermissions && !isSetup {
            // Permissions were just granted, setup hotkeys
            setupGlobalHotkey()
        } else if !accessibilityManager.hasAccessibilityPermissions && isSetup {
            // Permissions were revoked, cleanup
            cleanup()
        }
    }

    private func setupGlobalHotkey() {
        // Clean up existing monitors first
        cleanup()

        if let globalMonitor = NSEvent.addGlobalMonitorForEvents(matching: [.keyDown, .keyUp], handler: { event in
            self.handleHotkeyEvent(event)
        }) {
            monitors.append(globalMonitor)
        }

        if let localMonitor = NSEvent.addLocalMonitorForEvents(matching: [.keyDown, .keyUp], handler: { event in
            self.handleHotkeyEvent(event)
            return event
        }) {
            monitors.append(localMonitor)
        }

        isSetup = !monitors.isEmpty
        print("Global hotkey setup completed. Monitors active: \(isSetup)")
    }

    private func handleHotkeyEvent(_ event: NSEvent) {
        if event.keyCode == kVK_Space && event.modifierFlags.contains(.control) {
            DispatchQueue.main.async {
                if event.type == .keyDown {
                    self.hotkeyPressed()
                } else if event.type == .keyUp {
                    self.hotkeyReleased()
                }
            }
        } else if event.keyCode == kVK_Escape && event.type == .keyDown {
            DispatchQueue.main.async {
                self.escapePressed()
            }
        }
    }

    private func hotkeyPressed() {
        guard !isHotkeyPressed else { return }
        isHotkeyPressed = true
        audioRecorder?.startGlobalRecording()
    }

    private func hotkeyReleased() {
        guard isHotkeyPressed else { return }
        isHotkeyPressed = false
        audioRecorder?.stopGlobalRecording()
    }

    private func escapePressed() {
        audioRecorder?.cancelTranscription()
    }

    private func cleanup() {
        for monitor in monitors {
            NSEvent.removeMonitor(monitor)
        }
        monitors.removeAll()
        isSetup = false
        print("Global hotkey monitors cleaned up")
    }
}
