import SwiftUI
import AppKit

@main
struct OpenDictApp: App {
    @StateObject private var audioRecorder: AudioRecorder
    @StateObject private var accessibilityManager: AccessibilityManager
    @StateObject private var hotkeyManager: GlobalHotkeyManager
    private let windowDelegate = WindowDelegate()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(audioRecorder)
                .environmentObject(accessibilityManager)
                .environmentObject(hotkeyManager)
                .onAppear {
                    setupWindowControls()
                }
        }
        .windowResizability(.contentSize)
    }
    
    init() {
        // Create the managers
        let audioRecorder = AudioRecorder()
        let accessibilityManager = AccessibilityManager()
        let hotkeyManager = GlobalHotkeyManager()
        
        // Set up StateObjects first
        _audioRecorder = StateObject(wrappedValue: audioRecorder)
        _accessibilityManager = StateObject(wrappedValue: accessibilityManager)
        _hotkeyManager = StateObject(wrappedValue: hotkeyManager)
        
        // Then connect the managers
        audioRecorder.accessibilityManager = accessibilityManager
        hotkeyManager.audioRecorder = audioRecorder
    }
    
    func setupWindowControls() {
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            for window in NSApplication.shared.windows {
                // Set up as a normal application window
                window.level = .normal
                window.hidesOnDeactivate = false
                window.canHide = true
                window.isMovable = true
                
                // Ensure window delegate is set
                window.delegate = self.windowDelegate
                
                // Force show standard window buttons
                window.standardWindowButton(.closeButton)?.isHidden = false
                window.standardWindowButton(.miniaturizeButton)?.isHidden = false
                window.standardWindowButton(.zoomButton)?.isHidden = false
                
                // Enable the buttons explicitly
                window.standardWindowButton(.closeButton)?.isEnabled = true
                window.standardWindowButton(.miniaturizeButton)?.isEnabled = true
                window.standardWindowButton(.zoomButton)?.isEnabled = true
                
                // Ensure proper window style
                window.titlebarAppearsTransparent = false
                window.titleVisibility = .visible
                
                break // Only set up the first window
            }
        }
    }
}

class WindowDelegate: NSObject, NSWindowDelegate {
    func windowShouldClose(_ sender: NSWindow) -> Bool {
        NSApplication.shared.terminate(nil)
        return true
    }
    
    func windowWillMiniaturize(_ notification: Notification) {
        // Allow miniaturization
    }
} 