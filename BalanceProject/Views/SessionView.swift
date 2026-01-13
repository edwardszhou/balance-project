//
//  SessionView.swift
//  BalanceProject
//

import SwiftUI

struct SessionView: View {

    @State private var sessionViewModel = SessionViewModel()
    @State private var historyViewModel = SessionHistoryViewModel()
    
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
                    .font(.headline)
                    .foregroundStyle(sessionViewModel.isRecording ? .red : .secondary)
                
                if let currentData = sessionViewModel.currentData {
                    VStack(alignment: .leading, spacing: 8) {
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
                } else {
                    Text("No motion data.")
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
                            historyViewModel.addSession(session)
                        }
                    } label: {
                        Text("End Session")
                    }
                    .buttonStyle(.bordered)
                }
            }
            .padding(64)
        }
    }
}

#Preview {
    SessionView()
}
