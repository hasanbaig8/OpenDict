import Foundation
import ApplicationServices
import Cocoa
import Carbon

class AccessibilityManager: ObservableObject {
    @Published var hasAccessibilityPermissions = false
    private var permissionTimer: Timer?
    
    init() {
        checkAccessibilityPermissions()
        startPermissionMonitoring()
    }
    
    deinit {
        permissionTimer?.invalidate()
    }
    
    func checkAccessibilityPermissions() {
        let newPermissionStatus = AXIsProcessTrustedWithOptions([
            kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: false
        ] as CFDictionary)
        
        DispatchQueue.main.async {
            self.hasAccessibilityPermissions = newPermissionStatus
        }
    }
    
    private func startPermissionMonitoring() {
        permissionTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { _ in
            self.checkAccessibilityPermissions()
        }
    }
    
    func requestAccessibilityPermissions() {
        let _ = AXIsProcessTrustedWithOptions([
            kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: true
        ] as CFDictionary)
        
        // Check more frequently after requesting permissions
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            self.checkAccessibilityPermissions()
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
            self.checkAccessibilityPermissions()
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 5.0) {
            self.checkAccessibilityPermissions()
        }
    }
    
    func insertTextAtCursor(_ text: String) {
        print("insertTextAtCursor called with: '\(text)'")
        print("hasAccessibilityPermissions: \(hasAccessibilityPermissions)")
        
        guard hasAccessibilityPermissions else { 
            print("No accessibility permissions - cannot insert text")
            return 
        }
        
        print("Attempting to insert text via pasteboard...")
        let pasteboard = NSPasteboard.general
        let savedContents = pasteboard.pasteboardItems?.first?.data(forType: .string)
        
        pasteboard.clearContents()
        let success = pasteboard.setString(text, forType: .string)
        print("Pasteboard setString success: \(success)")
        
        let source = CGEventSource(stateID: .hidSystemState)
        
        let cmdVDown = CGEvent(keyboardEventSource: source, virtualKey: CGKeyCode(kVK_ANSI_V), keyDown: true)
        cmdVDown?.flags = CGEventFlags.maskCommand
        
        let cmdVUp = CGEvent(keyboardEventSource: source, virtualKey: CGKeyCode(kVK_ANSI_V), keyDown: false)
        cmdVUp?.flags = CGEventFlags.maskCommand
        
        print("Posting Cmd+V events...")
        cmdVDown?.post(tap: CGEventTapLocation.cghidEventTap)
        cmdVUp?.post(tap: CGEventTapLocation.cghidEventTap)
        print("Events posted")
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            if let savedContents = savedContents {
                pasteboard.clearContents()
                pasteboard.setData(savedContents, forType: .string)
                print("Restored pasteboard contents")
            }
        }
    }
}