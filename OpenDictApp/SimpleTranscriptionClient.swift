import Foundation

class SimpleTranscriptionClient: ObservableObject {
    private let host = "127.0.0.1"
    private let port: UInt16 = 8765

    func transcribeAudio(audioFilePath: String, completion: @escaping (Result<String, Error>) -> Void) {
        DispatchQueue.global(qos: .utility).async {
            do {
                print("Connecting to transcription server...")

                // Create socket
                let socket = socket(AF_INET, SOCK_STREAM, 0)
                guard socket != -1 else {
                    throw SimpleTranscriptionError.connectionFailed("Failed to create socket")
                }

                // Set up server address
                var serverAddr = sockaddr_in()
                serverAddr.sin_family = sa_family_t(AF_INET)
                serverAddr.sin_port = self.port.bigEndian
                inet_pton(AF_INET, self.host, &serverAddr.sin_addr)

                // Connect
                let connectResult = withUnsafePointer(to: &serverAddr) {
                    $0.withMemoryRebound(to: sockaddr.self, capacity: 1) {
                        connect(socket, $0, socklen_t(MemoryLayout<sockaddr_in>.size))
                    }
                }

                guard connectResult != -1 else {
                    close(socket)
                    throw SimpleTranscriptionError.connectionFailed("Failed to connect to server")
                }

                print("Connected successfully, sending request...")

                // Create request
                let request: [String: Any] = [
                    "action": "transcribe",
                    "audio_file": audioFilePath
                ]

                let requestData = try JSONSerialization.data(withJSONObject: request)
                print("Sending: \(String(data: requestData, encoding: .utf8) ?? "nil")")

                // Send request
                let sendResult = requestData.withUnsafeBytes { bytes in
                    send(socket, bytes.bindMemory(to: UInt8.self).baseAddress, requestData.count, 0)
                }

                guard sendResult != -1 else {
                    close(socket)
                    throw SimpleTranscriptionError.connectionFailed("Failed to send request")
                }

                print("Request sent, waiting for response...")

                // Receive response
                var buffer = [UInt8](repeating: 0, count: 4096)
                let bytesReceived = recv(socket, &buffer, buffer.count, 0)

                close(socket)

                guard bytesReceived > 0 else {
                    throw SimpleTranscriptionError.noResponse
                }

                print("Received \(bytesReceived) bytes")

                let responseData = Data(buffer[0..<bytesReceived])
                let response = try JSONSerialization.jsonObject(with: responseData) as? [String: Any]

                print("Response: \(response ?? [:])")

                if let status = response?["status"] as? String {
                    if status == "success", let text = response?["text"] as? String {
                        DispatchQueue.main.async {
                            completion(.success(text))
                        }
                    } else if status == "error", let errorMsg = response?["error"] as? String {
                        DispatchQueue.main.async {
                            completion(.failure(SimpleTranscriptionError.serverError(errorMsg)))
                        }
                    } else {
                        DispatchQueue.main.async {
                            completion(.failure(SimpleTranscriptionError.unknownResponse))
                        }
                    }
                } else {
                    DispatchQueue.main.async {
                        completion(.failure(SimpleTranscriptionError.invalidResponse))
                    }
                }

            } catch {
                print("Transcription error: \(error)")
                DispatchQueue.main.async {
                    completion(.failure(error))
                }
            }
        }
    }

    func shutdown() {
        DispatchQueue.global(qos: .utility).async {
            do {
                let socket = Foundation.socket(AF_INET, SOCK_STREAM, 0)
                guard socket != -1 else { return }

                var serverAddr = sockaddr_in()
                serverAddr.sin_family = sa_family_t(AF_INET)
                serverAddr.sin_port = self.port.bigEndian
                inet_pton(AF_INET, self.host, &serverAddr.sin_addr)

                let connectResult = withUnsafePointer(to: &serverAddr) {
                    $0.withMemoryRebound(to: sockaddr.self, capacity: 1) {
                        connect(socket, $0, socklen_t(MemoryLayout<sockaddr_in>.size))
                    }
                }

                if connectResult != -1 {
                    let request: [String: Any] = ["action": "shutdown"]
                    let requestData = try JSONSerialization.data(withJSONObject: request)

                    requestData.withUnsafeBytes { bytes in
                        send(socket, bytes.bindMemory(to: UInt8.self).baseAddress, requestData.count, 0)
                    }
                }

                close(socket)
            } catch {
                print("Shutdown error: \(error)")
            }
        }
    }
}

enum SimpleTranscriptionError: Error, LocalizedError {
    case connectionFailed(String)
    case noResponse
    case serverError(String)
    case unknownResponse
    case invalidResponse

    var errorDescription: String? {
        switch self {
        case .connectionFailed(let message):
            return "Connection failed: \(message)"
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
