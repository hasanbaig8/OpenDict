import Cocoa
import SwiftUI

// Create the main app
@main
struct HelloWorldApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .windowStyle(.hiddenTitleBar)
        .windowResizability(.contentSize)
    }
}

// Content view
struct ContentView: View {
    var body: some View {
        VStack(spacing: 20) {
            Text("Hello World")
                .font(.largeTitle)
                .fontWeight(.bold)
                .foregroundColor(.primary)
            
            Text("Welcome to your first macOS app!")
                .font(.body)
                .foregroundColor(.secondary)
        }
        .frame(width: 300, height: 200)
        .padding()
    }
} 