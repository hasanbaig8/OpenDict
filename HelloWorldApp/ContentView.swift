import SwiftUI

struct MenuBarContentView: View {
    @EnvironmentObject var audioRecorder: AudioRecorder
    @EnvironmentObject var accessibilityManager: AccessibilityManager
    
    var body: some View {
        VStack(spacing: 12) {
            HStack {
                Image(systemName: "mic.fill")
                    .foregroundColor(.blue)
                Text("OpenDict")
                    .font(.headline)
                    .fontWeight(.semibold)
            }
            
            if audioRecorder.isGlobalRecording {
                HStack {
                    Circle()
                        .fill(Color.red)
                        .frame(width: 8, height: 8)
                    Text("Recording...")
                        .foregroundColor(.red)
                        .font(.system(size: 14, weight: .medium))
                }
            } else if audioRecorder.isTranscribing {
                HStack {
                    Circle()
                        .fill(Color.orange)
                        .frame(width: 8, height: 8)
                    Text("Transcribing...")
                        .foregroundColor(.orange)
                        .font(.system(size: 14, weight: .medium))
                }
            } else {
                Text("Hold Ctrl+Space to record")
                    .font(.system(size: 13))
                    .foregroundColor(.secondary)
            }
            
            if !accessibilityManager.hasAccessibilityPermissions {
                Divider()
                
                VStack(spacing: 6) {
                    Text("Accessibility permission needed")
                        .font(.caption)
                        .foregroundColor(.orange)
                    
                    Button("Grant Permission") {
                        accessibilityManager.requestAccessibilityPermissions()
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.small)
                }
            }
            
            Divider()
            
            HStack(spacing: 12) {
                Button("Restart") {
                    restartApp()
                }
                .buttonStyle(.bordered)
                .controlSize(.small)
                
                Button("Quit") {
                    NSApplication.shared.terminate(nil)
                }
                .buttonStyle(.bordered)
                .controlSize(.small)
            }
        }
        .padding(16)
        .frame(width: 280)
    }
    
    private func restartApp() {
        let url = URL(fileURLWithPath: Bundle.main.resourcePath!)
        let path = url.deletingLastPathComponent().deletingLastPathComponent().absoluteString
        let task = Process()
        task.launchPath = "/usr/bin/open"
        task.arguments = [path]
        task.launch()
        NSApplication.shared.terminate(nil)
    }
} 