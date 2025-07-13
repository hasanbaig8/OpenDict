import Foundation
import Network

class TranscriptionClient: ObservableObject {
    private var connection: NWConnection?
    private let port: UInt16 = 8765
    private let host = "localhost"

    init() {
        setupConnection()
    }

    private func setupConnection() {
        let nwEndpoint = NWEndpoint.hostPort(host: NWEndpoint.Host(host), port: NWEndpoint.Port(integerLiteral: port))
        connection = NWConnection(to: nwEndpoint, using: .tcp)

        connection?.stateUpdateHandler = { [weak self] state in
            switch state {
            case .ready:
                print("TranscriptionClient: Connection ready")
            case .failed(let error):
                print("TranscriptionClient: Connection failed: \(error)")
                self?.reconnect()
            case .cancelled:
                print("TranscriptionClient: Connection cancelled")
            default:
                break
            }
        }

        connection?.start(queue: .global(qos: .utility))
    }

    private func reconnect() {
        DispatchQueue.global(qos: .utility).asyncAfter(deadline: .now() + 1.0) {
            self.setupConnection()
        }
    }

    func transcribeAudio(audioFilePath: String, completion: @escaping (Result<String, Error>) -> Void) {
        // Ensure connection is ready, retry if needed
        waitForConnection { [weak self] success in
            if !success {
                completion(.failure(TranscriptionError.connectionNotReady))
                return
            }

            guard let self = self, let connection = self.connection else {
                completion(.failure(TranscriptionError.connectionNotReady))
                return
            }

            let request: [String: Any] = [
                "action": "transcribe",
                "audio_file": audioFilePath
            ]

            do {
                let requestData = try JSONSerialization.data(withJSONObject: request)
                print("Sending transcription request for: \(audioFilePath)")

                connection.send(content: requestData, completion: .contentProcessed { error in
                    if let error = error {
                        print("Send error: \(error)")
                        completion(.failure(error))
                        return
                    }

                    print("Request sent, waiting for response...")
                    // Receive response
                    connection.receive(minimumIncompleteLength: 1, maximumLength: 4096) { data, _, isComplete, error in
                        if let error = error {
                            print("Receive error: \(error)")
                            completion(.failure(error))
                            return
                        }

                        guard let data = data else {
                            print("No data received")
                            completion(.failure(TranscriptionError.noResponse))
                            return
                        }

                        print("Received \(data.count) bytes")

                        do {
                            let response = try JSONSerialization.jsonObject(with: data) as? [String: Any]
                            print("Response: \(response ?? [:])")

                            if let status = response?["status"] as? String {
                                if status == "success", let text = response?["text"] as? String {
                                    completion(.success(text))
                                } else if status == "error", let errorMsg = response?["error"] as? String {
                                    completion(.failure(TranscriptionError.serverError(errorMsg)))
                                } else {
                                    completion(.failure(TranscriptionError.unknownResponse))
                                }
                            } else {
                                completion(.failure(TranscriptionError.invalidResponse))
                            }
                        } catch {
                            print("JSON parsing error: \(error)")
                            completion(.failure(error))
                        }
                    }
                })
            } catch {
                completion(.failure(error))
            }
        }
    }

    private func waitForConnection(completion: @escaping (Bool) -> Void) {
        if connection?.state == .ready {
            completion(true)
            return
        }

        // Wait up to 5 seconds for connection
        var attempts = 0
        let maxAttempts = 50

        func checkConnection() {
            if connection?.state == .ready {
                completion(true)
            } else if attempts < maxAttempts {
                attempts += 1
                DispatchQueue.global(qos: .utility).asyncAfter(deadline: .now() + 0.1) {
                    checkConnection()
                }
            } else {
                completion(false)
            }
        }

        checkConnection()
    }

    func shutdown() {
        guard let connection = connection else { return }

        let request: [String: Any] = [
            "action": "shutdown"
        ]

        do {
            let requestData = try JSONSerialization.data(withJSONObject: request)
            connection.send(content: requestData, completion: .contentProcessed { _ in
                self.connection?.cancel()
            })
        } catch {
            connection.cancel()
        }
    }

    deinit {
        connection?.cancel()
    }
}

enum TranscriptionError: Error, LocalizedError {
    case connectionNotReady
    case noResponse
    case serverError(String)
    case unknownResponse
    case invalidResponse

    var errorDescription: String? {
        switch self {
        case .connectionNotReady:
            return "Connection to transcription server not ready"
        case .noResponse:
            return "No response from transcription server"
        case .serverError(let message):
            return "Server error: \(message)"
        case .unknownResponse:
            return "Unknown response from server"
        case .invalidResponse:
            return "Invalid response format"
        }
    }
}
