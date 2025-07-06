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
        let newPermissionStatus = AXIsProcessTrustedWithOptions(nil)
        
        DispatchQueue.main.async {
            self.hasAccessibilityPermissions = newPermissionStatus
        }
    }
    
    private func startPermissionMonitoring() {
        // Check permissions every 2 seconds to detect when they're granted
        permissionTimer = Timer.scheduledTimer(withTimeInterval: 2.0, repeats: true) { _ in
            self.checkAccessibilityPermissions()
        }
    }
    
    func requestAccessibilityPermissions() {
        let _ = AXIsProcessTrustedWithOptions([
            kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: true
        ] as CFDictionary)
        
        // Check again after a short delay in case permissions were granted immediately
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            self.checkAccessibilityPermissions()
        }
    }
    
    func insertTextAtCursor(_ text: String) {
        guard hasAccessibilityPermissions else {
            print("No accessibility permissions")
            return
        }
        
        // Try to get the focused UI element
        let systemWideElement = AXUIElementCreateSystemWide()
        var focusedElement: CFTypeRef?
        
        let result = AXUIElementCopyAttributeValue(
            systemWideElement,
            kAXFocusedUIElementAttribute as CFString,
            &focusedElement
        )
        
        if result == .success, let element = focusedElement {
            // Get current text value
            var currentValue: CFTypeRef?
            let getCurrentResult = AXUIElementCopyAttributeValue(
                element as! AXUIElement,
                kAXValueAttribute as CFString,
                &currentValue
            )
            
            var newText = text
            if getCurrentResult == .success, let currentText = currentValue as? String {
                // Append to existing text
                newText = currentText + text
            }
            
            // Set the combined text
            let cfText = newText as CFString
            AXUIElementSetAttributeValue(element as! AXUIElement, kAXValueAttribute as CFString, cfText)
        } else {
            // Fallback: use pasteboard and simulate Cmd+V
            insertTextViaPasteboard(text)
        }
    }
    
    private func insertTextViaPasteboard(_ text: String) {
        // Save current pasteboard contents
        let pasteboard = NSPasteboard.general
        let savedContents = pasteboard.pasteboardItems?.first?.data(forType: .string)
        
        // Set our text to pasteboard
        pasteboard.clearContents()
        pasteboard.setString(text, forType: .string)
        
        // Simulate Cmd+V
        let source = CGEventSource(stateID: .hidSystemState)
        
        // Press Cmd+V
        let cmdVDown = CGEvent(keyboardEventSource: source, virtualKey: CGKeyCode(kVK_ANSI_V), keyDown: true)
        cmdVDown?.flags = CGEventFlags.maskCommand
        
        let cmdVUp = CGEvent(keyboardEventSource: source, virtualKey: CGKeyCode(kVK_ANSI_V), keyDown: false)
        cmdVUp?.flags = CGEventFlags.maskCommand
        
        cmdVDown?.post(tap: CGEventTapLocation.cghidEventTap)
        cmdVUp?.post(tap: CGEventTapLocation.cghidEventTap)
        
        // Restore pasteboard after a short delay
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            if let savedContents = savedContents {
                pasteboard.clearContents()
                pasteboard.setData(savedContents, forType: .string)
            }
        }
    }
}