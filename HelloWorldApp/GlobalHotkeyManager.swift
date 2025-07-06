import Foundation
import Carbon
import ApplicationServices
import Cocoa

class GlobalHotkeyManager: ObservableObject {
    private var eventHotKeyRef: EventHotKeyRef?
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
        // Add both global and local monitors for comprehensive coverage
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
        // Check for Ctrl+Space
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
        
        // Start recording
        audioRecorder?.startGlobalRecording()
    }
    
    private func hotkeyReleased() {
        guard isHotkeyPressed else { return }
        isHotkeyPressed = false
        
        // Stop recording and transcribe
        audioRecorder?.stopGlobalRecording()
    }
    
    private func cleanup() {
        for monitor in monitors {
            NSEvent.removeMonitor(monitor)
        }
        monitors.removeAll()
    }
}