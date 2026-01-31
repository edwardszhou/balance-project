//
//  SessionView.swift
//  BalanceProject
//

import SwiftUI

struct SessionView: View {

    @State private var sessionViewModel = SessionViewModel()
    @State private var historyViewModel = SessionHistoryViewModel()
    
    @State private var showNamePrompt = false
    @State private var pendingSession: MotionSession?
    @State private var sessionName = ""
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 24) {
                Text("Balance Project")
                    .font(.system(size: 36, weight: .bold))
                    .foregroundColor(.primary)
                Image(systemName: "airpodspro")
                    .font(.system(size: 50))
                    .foregroundColor(.blue)
            }
            .padding(64)
            .toolbar {
                NavigationLink("History") {
                    SessionHistoryView(viewModel: historyViewModel)
                }
            }
            Spacer()
            VStack(spacing: 24) {
                Text(sessionViewModel.isRecording ? "Recording…" : "Idle")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundStyle(sessionViewModel.isRecording ? .red : .secondary)
                
                if let currentData = sessionViewModel.currentData {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Sample Rate (Hz): \(sessionViewModel.currentHz, specifier: "%.1f")")
                        Spacer().frame(maxHeight: 32)
                        Text("Pitch: \(currentData.pitch, specifier: "%.3f")")
                        Text("Roll: \(currentData.roll, specifier: "%.3f")")
                        Text("Yaw: \(currentData.yaw, specifier: "%.3f")")
                        Spacer().frame(maxHeight: 32)
                        Text("Rotation Rate X: \(currentData.rotationRateX, specifier: "%.3f")")
                        Text("Rotation Rate Y: \(currentData.rotationRateY, specifier: "%.3f")")
                        Text("Rotation Rate Z: \(currentData.rotationRateZ, specifier: "%.3f")")
                        Spacer().frame(maxHeight: 32)
                        Text("Acceleration X: \(currentData.accelerationX, specifier: "%.3f")")
                        Text("Acceleration Y: \(currentData.accelerationY, specifier: "%.3f")")
                        Text("Acceleration Z: \(currentData.accelerationZ, specifier: "%.3f")")
                    }
                }
            }
            Spacer()
            HStack(spacing: 24) {
                if !sessionViewModel.isRecording {
                    Button {
                        sessionViewModel.startSession()
                    } label: {
                        Text("Start Session")
                    }
                    .buttonStyle(.borderedProminent)
                } else {
                    Button(role: .cancel) {
                        if let session = sessionViewModel.endSession() {
                            pendingSession = session
                            showNamePrompt = true
                        }
                    } label: {
                        Text("End Session")
                    }
                    .buttonStyle(.bordered)
                }
            }
            .padding(64)
        }
        .alert("Name Session", isPresented: $showNamePrompt) {
            TextField("Name", text: $sessionName)
            Button("Save") {
                var session = pendingSession!
                session.name = sessionName
                historyViewModel.addSession(session)
                
                sessionName = ""
                pendingSession = nil
            }
        }
    }
}

#Preview {
    SessionView()
}
