import AVFoundation
import SwiftUI
import Foundation

class AudioRecorder: NSObject, ObservableObject {
    private var audioRecorder: AVAudioRecorder?
    private var audioPlayer: AVAudioPlayer?
    private var recordingTimer: Timer?
    
    @Published var isRecording = false
    @Published var isPlaying = false
    @Published var hasRecording = false
    @Published var isTranscribing = false
    @Published var transcribedText = ""
    @Published var isGlobalRecording = false
    
    var accessibilityManager: AccessibilityManager?
    private var recordingIndicatorManager: RecordingIndicatorManager?
    
    private var audioURL: URL {
        let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        return documentsPath.appendingPathComponent("recording.wav")
    }
    
    private var globalAudioURL: URL {
        let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        return documentsPath.appendingPathComponent("global_recording.wav")
    }
    
    override init() {
        super.init()
        checkForExistingRecording()
    }
    
    private func checkForExistingRecording() {
        hasRecording = FileManager.default.fileExists(atPath: audioURL.path)
    }
    
    func startRecording() {
        guard !isRecording && !isGlobalRecording else {
            print("Already recording")
            return
        }
        
        let settings = [
            AVFormatIDKey: Int(kAudioFormatLinearPCM),
            AVSampleRateKey: 16000,
            AVNumberOfChannelsKey: 1,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
        ]
        
        do {
            audioRecorder = try AVAudioRecorder(url: audioURL, settings: settings)
            audioRecorder?.delegate = self
            audioRecorder?.record()
            isRecording = true
            startRecordingTimer()
            print("Started recording to: \(audioURL.path)")
        } catch {
            print("Failed to start recording: \(error)")
        }
    }
    
    func stopRecording() {
        guard isRecording else { return }
        
        audioRecorder?.stop()
        audioRecorder = nil
        isRecording = false
        hasRecording = true
        stopRecordingTimer()
        print("Stopped recording")
    }
    
    func startPlaying() {
        guard !isPlaying else {
            print("Already playing")
            return
        }
        
        guard FileManager.default.fileExists(atPath: audioURL.path) else {
            print("Audio file does not exist at: \(audioURL.path)")
            return
        }
        
        do {
            audioPlayer = try AVAudioPlayer(contentsOf: audioURL)
            audioPlayer?.delegate = self
            audioPlayer?.prepareToPlay()
            
            if audioPlayer?.play() == true {
                isPlaying = true
                print("Started playing audio")
            } else {
                print("Failed to start playback")
            }
        } catch {
            print("Failed to play audio: \(error)")
        }
    }
    
    func stopPlaying() {
        guard isPlaying else { return }
        
        audioPlayer?.stop()
        audioPlayer = nil
        isPlaying = false
        print("Stopped playing audio")
    }
    
    func transcribeAudio() {
        guard !isTranscribing else {
            print("Already transcribing")
            return
        }
        
        guard FileManager.default.fileExists(atPath: audioURL.path) else {
            print("Audio file does not exist at: \(audioURL.path)")
            return
        }
        
        isTranscribing = true
        transcribedText = ""
        
        let task = Process()
        let bundle = Bundle.main
        let pythonPath = bundle.path(forResource: "venv/bin/python", ofType: nil) ?? "/Users/hasanbaig/Downloads/Code/opendict/venv/bin/python"
        let scriptPath = bundle.path(forResource: "transcribe", ofType: "py") ?? "/Users/hasanbaig/Downloads/Code/opendict/transcribe.py"
        
        // Verify paths exist
        guard FileManager.default.fileExists(atPath: pythonPath) else {
            print("Python interpreter not found at: \(pythonPath)")
            DispatchQueue.main.async {
                self.isTranscribing = false
                self.transcribedText = "Error: Python interpreter not found"
            }
            return
        }
        
        guard FileManager.default.fileExists(atPath: scriptPath) else {
            print("Transcription script not found at: \(scriptPath)")
            DispatchQueue.main.async {
                self.isTranscribing = false
                self.transcribedText = "Error: Transcription script not found"
            }
            return
        }
        
        task.launchPath = pythonPath
        task.arguments = [scriptPath, audioURL.path]
        
        let pipe = Pipe()
        task.standardOutput = pipe
        task.standardError = pipe
        
        task.terminationHandler = { process in
            DispatchQueue.main.async {
                self.isTranscribing = false
                if process.terminationStatus == 0 {
                    self.loadTranscribedText()
                } else {
                    print("Transcription process failed with status: \(process.terminationStatus)")
                    self.transcribedText = "Transcription failed"
                }
            }
        }
        
        print("Starting transcription with python: \(pythonPath)")
        print("Script: \(scriptPath)")
        print("Audio file: \(audioURL.path)")
        
        do {
            try task.run()
        } catch {
            print("Failed to run transcription: \(error)")
            DispatchQueue.main.async {
                self.isTranscribing = false
                self.transcribedText = "Failed to start transcription: \(error.localizedDescription)"
            }
        }
    }
    
    private func loadTranscribedText() {
        let outputURL = audioURL.deletingLastPathComponent().appendingPathComponent("output_text.json")
        
        guard FileManager.default.fileExists(atPath: outputURL.path) else {
            print("Output file does not exist")
            return
        }
        
        do {
            let data = try Data(contentsOf: outputURL)
            if let json = try JSONSerialization.jsonObject(with: data, options: []) as? [String: Any],
               let text = json["text"] as? String {
                transcribedText = text
            }
        } catch {
            print("Failed to load transcribed text: \(error)")
        }
    }
    
    // MARK: - Global Recording Methods
    
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
            showRecordingIndicator()
            print("Started global recording")
        } catch {
            print("Failed to start global recording: \(error)")
        }
    }
    
    func stopGlobalRecording() {
        guard isGlobalRecording else { return }
        
        audioRecorder?.stop()
        isGlobalRecording = false
        stopRecordingTimer()
        hideRecordingIndicator()
        print("Stopped global recording")
        
        // Transcribe and insert text
        transcribeGlobalAudio()
    }
    
    private func transcribeGlobalAudio() {
        guard FileManager.default.fileExists(atPath: globalAudioURL.path) else {
            print("Global audio file does not exist")
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
            print("Failed to run global transcription: \(error)")
            DispatchQueue.main.async {
                self.isTranscribing = false
            }
        }
    }
    
    private func loadGlobalTranscribedText() {
        let outputURL = globalAudioURL.deletingLastPathComponent().appendingPathComponent("output_text.json")
        
        guard FileManager.default.fileExists(atPath: outputURL.path) else {
            print("Global output file does not exist")
            return
        }
        
        do {
            let data = try Data(contentsOf: outputURL)
            if let json = try JSONSerialization.jsonObject(with: data, options: []) as? [String: Any],
               let text = json["text"] as? String {
                
                // Insert text at cursor position
                accessibilityManager?.insertTextAtCursor(text)
                
                // Also update the transcribed text for the UI
                transcribedText = text
            }
        } catch {
            print("Failed to load global transcribed text: \(error)")
        }
    }
    
    // MARK: - Timer Methods
    
    private func startRecordingTimer() {
        recordingTimer?.invalidate()
        recordingTimer = Timer.scheduledTimer(withTimeInterval: 60.0, repeats: false) { _ in
            DispatchQueue.main.async {
                if self.isRecording {
                    self.stopRecording()
                    print("Recording stopped automatically after 1 minute")
                }
                if self.isGlobalRecording {
                    self.stopGlobalRecording()
                    print("Global recording stopped automatically after 1 minute")
                }
            }
        }
    }
    
    private func stopRecordingTimer() {
        recordingTimer?.invalidate()
        recordingTimer = nil
    }
    
    private func showRecordingIndicator() {
        if recordingIndicatorManager == nil {
            recordingIndicatorManager = RecordingIndicatorManager()
        }
        recordingIndicatorManager?.showRecordingIndicator()
    }
    
    private func hideRecordingIndicator() {
        recordingIndicatorManager?.hideRecordingIndicator()
        recordingIndicatorManager = nil
    }
}

extension AudioRecorder: AVAudioPlayerDelegate {
    func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        isPlaying = false
    }
}

extension AudioRecorder: AVAudioRecorderDelegate {
    func audioRecorderDidFinishRecording(_ recorder: AVAudioRecorder, successfully flag: Bool) {
        if flag {
            hasRecording = true
            print("Recording finished successfully")
        } else {
            print("Recording failed")
        }
        isRecording = false
    }
    
    func audioRecorderEncodeErrorDidOccur(_ recorder: AVAudioRecorder, error: Error?) {
        print("Recording encode error: \(error?.localizedDescription ?? "Unknown error")")
        isRecording = false
    }
}