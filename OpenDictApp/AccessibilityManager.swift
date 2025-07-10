import Foundation
import ApplicationServices
import Cocoa
import Carbon
import UserNotifications

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
            let oldStatus = self.hasAccessibilityPermissions
            self.hasAccessibilityPermissions = newPermissionStatus

            // If permissions were just granted, show a notification
            if !oldStatus && newPermissionStatus {
                self.showPermissionGrantedNotification()
            }
        }
    }

    private func showPermissionGrantedNotification() {
        let content = UNMutableNotificationContent()
        content.title = "OpenDict Ready!"
        content.body = "Accessibility permissions granted. Ctrl+Space hotkey is now active."
        content.sound = UNNotificationSound.default

        let request = UNNotificationRequest(identifier: "permissions-granted", content: content, trigger: nil)

        UNUserNotificationCenter.current().add(request) { error in
            if let error = error {
                print("Failed to show notification: \(error)")
            }
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
        startAggressivePermissionChecking()
    }

    private func startAggressivePermissionChecking() {
        let checkInterval: TimeInterval = 0.5
        let maxChecks = 20 // Check for 10 seconds
        var checkCount = 0

        let aggressiveTimer = Timer.scheduledTimer(withTimeInterval: checkInterval, repeats: true) { timer in
            checkCount += 1
            self.checkAccessibilityPermissions()

            // Stop aggressive checking if permissions are granted or we've checked enough
            if self.hasAccessibilityPermissions || checkCount >= maxChecks {
                timer.invalidate()

                if self.hasAccessibilityPermissions {
                    print("Accessibility permissions granted! Hotkeys should now work.")
                }
            }
        }

        // Also invalidate the timer if it's not cleaned up
        DispatchQueue.main.asyncAfter(deadline: .now() + TimeInterval(maxChecks) * checkInterval + 1.0) {
            aggressiveTimer.invalidate()
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
