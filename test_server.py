#!/usr/bin/env python3
import socket
import json

def test_server():
    try:
        # Connect to the server
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 8765))
        print("Connected to server")
        
        # Create a test request
        request = {
            "action": "transcribe",
            "audio_file": "/tmp/test.wav"  # This file doesn't need to exist for connection test
        }
        
        # Send request
        request_data = json.dumps(request).encode('utf-8')
        client_socket.send(request_data)
        print(f"Sent request: {request}")
        
        # Receive response
        response_data = client_socket.recv(4096)
        response = json.loads(response_data.decode('utf-8'))
        print(f"Received response: {response}")
        
        client_socket.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_server()