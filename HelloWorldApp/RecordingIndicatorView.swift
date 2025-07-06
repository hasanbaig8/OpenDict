import SwiftUI
import AppKit

class RecordingIndicatorManager: ObservableObject {
    private var indicatorWindow: NSWindow?
    
    func showRecordingIndicator() {
        guard indicatorWindow == nil else { return }
        
        DispatchQueue.main.async {
            guard let screen = NSScreen.main else { return }
            let screenFrame = screen.visibleFrame
            let windowSize = CGSize(width: 150, height: 40)
            let origin = CGPoint(
                x: screenFrame.maxX - windowSize.width - 20,
                y: screenFrame.maxY - windowSize.height - 20
            )
            
            let window = NSPanel(
                contentRect: NSRect(origin: origin, size: windowSize),
                styleMask: [.nonactivatingPanel],
                backing: .buffered,
                defer: false
            )
            
            window.isOpaque = false
            window.backgroundColor = NSColor.clear
            window.level = NSWindow.Level.floating
            window.hasShadow = false
            window.isMovable = false
            window.canHide = false
            window.ignoresMouseEvents = true
            window.collectionBehavior = [.canJoinAllSpaces, .stationary]
            
            let indicatorView = RecordingIndicatorView()
            let hostingView = NSHostingView(rootView: indicatorView)
            window.contentView = hostingView
            
            window.orderFront(nil)
            self.indicatorWindow = window
        }
    }
    
    func hideRecordingIndicator() {
        DispatchQueue.main.async {
            self.indicatorWindow?.orderOut(nil)
            self.indicatorWindow = nil
        }
    }
}

struct RecordingIndicatorView: View {
    @State private var isAnimating = false
    
    var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(Color.red)
                .frame(width: 6, height: 6)
                .scaleEffect(isAnimating ? 1.3 : 1.0)
                .animation(.easeInOut(duration: 0.8).repeatForever(autoreverses: true), value: isAnimating)
            
            Text("Recording...")
                .font(.system(size: 11, weight: .medium))
                .foregroundColor(.primary)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 6)
        .background(
            RoundedRectangle(cornerRadius: 6)
                .fill(.regularMaterial)
        )
        .onAppear {
            isAnimating = true
        }
    }
}