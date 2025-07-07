import Foundation
import Cocoa
import Carbon

class GlobalHotkeyManager: ObservableObject {
    @Published var isHotkeyPressed = false
    private var monitors: [Any] = []
    
    weak var audioRecorder: AudioRecorder?
    
    init() {
        setupGlobalHotkey()
    }
    
    deinit {
        cleanup()
    }
    
    private func setupGlobalHotkey() {
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
    
    private func cleanup() {
        for monitor in monitors {
            NSEvent.removeMonitor(monitor)
        }
        monitors.removeAll()
    }
}