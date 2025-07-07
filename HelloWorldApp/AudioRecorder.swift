import AVFoundation
import Foundation

class AudioRecorder: NSObject, ObservableObject {
    private var audioRecorder: AVAudioRecorder?
    private var recordingTimer: Timer?
    
    @Published var isGlobalRecording = false
    @Published var isTranscribing = false
    
    var accessibilityManager: AccessibilityManager?
    
    private var globalAudioURL: URL {
        let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        return documentsPath.appendingPathComponent("global_recording.wav")
    }
    
    func startGlobalRecording() {
        guard !isGlobalRecording else { return }
        
        let settings = [
            AVFormatIDKey: Int(kAudioFormatLinearPCM),
            AVSampleRateKey: 16000,
            AVNumberOfChannelsKey: 1,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
        ]
        
        do {
            audioRecorder = try AVAudioRecorder(url: globalAudioURL, settings: settings)
            audioRecorder?.record()
            isGlobalRecording = true
            startRecordingTimer()
        } catch {
            print("Failed to start recording: \(error)")
        }
    }
    
    func stopGlobalRecording() {
        guard isGlobalRecording else { return }
        
        audioRecorder?.stop()
        isGlobalRecording = false
        stopRecordingTimer()
        
        transcribeGlobalAudio()
    }
    
    private func transcribeGlobalAudio() {
        guard FileManager.default.fileExists(atPath: globalAudioURL.path) else {
            return
        }
        
        isTranscribing = true
        
        let task = Process()
        let bundle = Bundle.main
        let pythonPath = bundle.path(forResource: "venv/bin/python", ofType: nil) ?? "/Users/hasanbaig/Downloads/Code/opendict/venv/bin/python"
        let scriptPath = bundle.path(forResource: "transcribe", ofType: "py") ?? "/Users/hasanbaig/Downloads/Code/opendict/transcribe.py"
        
        task.launchPath = pythonPath
        task.arguments = [scriptPath, globalAudioURL.path]
        
        let pipe = Pipe()
        task.standardOutput = pipe
        task.standardError = pipe
        
        task.terminationHandler = { _ in
            DispatchQueue.main.async {
                self.isTranscribing = false
                self.loadGlobalTranscribedText()
            }
        }
        
        do {
            try task.run()
        } catch {
            print("Failed to run transcription: \(error)")
            DispatchQueue.main.async {
                self.isTranscribing = false
            }
        }
    }
    
    private func loadGlobalTranscribedText() {
        let outputURL = globalAudioURL.deletingLastPathComponent().appendingPathComponent("output_text.json")
        
        guard FileManager.default.fileExists(atPath: outputURL.path) else {
            return
        }
        
        do {
            let data = try Data(contentsOf: outputURL)
            if let json = try JSONSerialization.jsonObject(with: data, options: []) as? [String: Any],
               let text = json["text"] as? String {
                accessibilityManager?.insertTextAtCursor(text)
            }
        } catch {
            print("Failed to load transcribed text: \(error)")
        }
    }
    
    private func startRecordingTimer() {
        recordingTimer?.invalidate()
        recordingTimer = Timer.scheduledTimer(withTimeInterval: 60.0, repeats: false) { _ in
            DispatchQueue.main.async {
                if self.isGlobalRecording {
                    self.stopGlobalRecording()
                }
            }
        }
    }
    
    private func stopRecordingTimer() {
        recordingTimer?.invalidate()
        recordingTimer = nil
    }
    
}

