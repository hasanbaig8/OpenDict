import AVFoundation
import Foundation

class AudioRecorder: NSObject, ObservableObject {
    private var audioRecorder: AVAudioRecorder?
    private var recordingTimer: Timer?
    private var transcriptionClient: SimpleTranscriptionClient?

    @Published var isGlobalRecording = false
    @Published var isTranscribing = false

    var accessibilityManager: AccessibilityManager?

    private var globalAudioURL: URL {
        let tempDir = FileManager.default.temporaryDirectory
        return tempDir.appendingPathComponent("opendict_recording.wav")
    }

    override init() {
        super.init()
        transcriptionClient = SimpleTranscriptionClient()
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

        transcriptionClient?.transcribeAudio(audioFilePath: globalAudioURL.path) { [weak self] result in
            DispatchQueue.main.async {
                self?.isTranscribing = false

                switch result {
                case .success(let text):
                    print("Transcription successful: '\(text)'")
                    print("Has accessibility permissions: \(self?.accessibilityManager?.hasAccessibilityPermissions ?? false)")

                    if let accessibilityManager = self?.accessibilityManager {
                        if accessibilityManager.hasAccessibilityPermissions {
                            print("Inserting text at cursor")
                            accessibilityManager.insertTextAtCursor(text)
                        } else {
                            print("No accessibility permissions - cannot insert text")
                        }
                    } else {
                        print("No accessibility manager")
                    }
                case .failure(let error):
                    print("Transcription failed: \(error)")
                }
            }
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

    func cancelTranscription() {
        guard isTranscribing else { return }

        // For now, we can't cancel the network request easily, so just reset state
        isTranscribing = false
    }

    func shutdown() {
        transcriptionClient?.shutdown()
    }

}
