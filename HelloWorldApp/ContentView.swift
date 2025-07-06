import SwiftUI

struct ContentView: View {
    @EnvironmentObject var audioRecorder: AudioRecorder
    @EnvironmentObject var accessibilityManager: AccessibilityManager
    @EnvironmentObject var hotkeyManager: GlobalHotkeyManager
    
    var body: some View {
        VStack(spacing: 20) {
            Text("OpenDict")
                .font(.largeTitle)
                .fontWeight(.bold)
                .foregroundColor(.primary)
            
            Text("Global Hotkey: Ctrl+Space")
                .font(.caption)
                .foregroundColor(.secondary)
            
            if !accessibilityManager.hasAccessibilityPermissions {
                VStack(spacing: 10) {
                    Text("⚠️ Accessibility permissions required")
                        .font(.headline)
                        .foregroundColor(.orange)
                    
                    Text("To use the global hotkey feature, please grant accessibility permissions.")
                        .font(.caption)
                        .multilineTextAlignment(.center)
                        .foregroundColor(.secondary)
                    
                    Button("Grant Permissions") {
                        accessibilityManager.requestAccessibilityPermissions()
                    }
                    .buttonStyle(.borderedProminent)
                }
                .padding()
                .background(Color.orange.opacity(0.1))
                .cornerRadius(8)
            }
            
            if hotkeyManager.isHotkeyPressed {
                VStack {
                    Text("🎤 Recording...")
                        .font(.headline)
                        .foregroundColor(.red)
                    Text("Release Ctrl+Space to transcribe")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding()
                .background(Color.red.opacity(0.1))
                .cornerRadius(8)
            }
            
            HStack(spacing: 15) {
                Button(action: {
                    if audioRecorder.isRecording {
                        audioRecorder.stopRecording()
                    } else {
                        audioRecorder.startRecording()
                    }
                }) {
                    HStack {
                        Image(systemName: audioRecorder.isRecording ? "stop.circle.fill" : "mic.circle.fill")
                        Text(audioRecorder.isRecording ? "Stop" : "Record")
                    }
                }
                .font(.title2)
                .buttonStyle(.borderedProminent)
                .foregroundColor(audioRecorder.isRecording ? .red : .blue)
                
                Button(action: {
                    if audioRecorder.isPlaying {
                        audioRecorder.stopPlaying()
                    } else {
                        audioRecorder.startPlaying()
                    }
                }) {
                    HStack {
                        Image(systemName: audioRecorder.isPlaying ? "stop.circle.fill" : "play.circle.fill")
                        Text(audioRecorder.isPlaying ? "Stop" : "Play")
                    }
                }
                .font(.title2)
                .buttonStyle(.bordered)
                .disabled(!audioRecorder.hasRecording || audioRecorder.isRecording)
                
                Button(action: {
                    audioRecorder.transcribeAudio()
                }) {
                    HStack {
                        Image(systemName: audioRecorder.isTranscribing ? "waveform.circle" : "text.bubble")
                        Text(audioRecorder.isTranscribing ? "Transcribing..." : "Transcribe")
                    }
                }
                .font(.title2)
                .buttonStyle(.bordered)
                .disabled(!audioRecorder.hasRecording || audioRecorder.isRecording || audioRecorder.isTranscribing)
            }
            
            if audioRecorder.isRecording {
                Text("Recording...")
                    .font(.caption)
                    .foregroundColor(.red)
            } else if audioRecorder.isPlaying {
                Text("Playing...")
                    .font(.caption)
                    .foregroundColor(.blue)
            } else if audioRecorder.isTranscribing {
                Text("Transcribing audio...")
                    .font(.caption)
                    .foregroundColor(.orange)
            } else if audioRecorder.hasRecording {
                Text("Recording ready to play")
                    .font(.caption)
                    .foregroundColor(.green)
            }
            
            if !audioRecorder.transcribedText.isEmpty {
                ScrollView {
                    Text("Transcribed Text:")
                        .font(.headline)
                        .padding(.top)
                    
                    Text(audioRecorder.transcribedText)
                        .font(.body)
                        .padding()
                        .background(Color.gray.opacity(0.1))
                        .cornerRadius(8)
                        .textSelection(.enabled)
                }
                .frame(maxHeight: 150)
            }
        }
        .frame(width: 500, height: 400)
        .padding()
    }
}

#Preview {
    ContentView()
        .environmentObject(AudioRecorder())
        .environmentObject(AccessibilityManager())
        .environmentObject(GlobalHotkeyManager())
} 