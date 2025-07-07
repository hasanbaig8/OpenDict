import SwiftUI
import AppKit
import Combine

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
    private var audioRecorder: AudioRecorder!
    private var accessibilityManager: AccessibilityManager!
    private var hotkeyManager: GlobalHotkeyManager!
    
    func applicationDidFinishLaunching(_ notification: Notification) {
        // Create managers
        audioRecorder = AudioRecorder()
        accessibilityManager = AccessibilityManager()
        hotkeyManager = GlobalHotkeyManager()
        
        // Connect managers
        audioRecorder.accessibilityManager = accessibilityManager
        hotkeyManager.audioRecorder = audioRecorder
        
        // Create status item
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        updateStatusIcon()
        if let button = statusItem.button {
            button.action = #selector(togglePopover)
            button.target = self
        }
        
        // Create popover
        popover = NSPopover()
        popover.contentSize = NSSize(width: 280, height: 120)
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
    
    private func setupObservers() {
        // Watch for recording state changes
        audioRecorder.objectWillChange.sink { [weak self] _ in
            DispatchQueue.main.async {
                self?.updateStatusIcon()
            }
        }.store(in: &cancellables)
    }
    
    private var cancellables = Set<AnyCancellable>()
    
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
    
    @objc func togglePopover() {
        if popover.isShown {
            popover.performClose(nil)
        } else {
            if let button = statusItem.button {
                popover.show(relativeTo: button.bounds, of: button, preferredEdge: .minY)
            }
        }
    }
} 