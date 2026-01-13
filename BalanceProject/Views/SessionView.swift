//
//  SessionView.swift
//  BalanceProject
//

import SwiftUI

struct SessionView: View {

    @State private var viewModel = SessionViewModel()
    
    var body: some View {
        VStack(spacing: 24) {
            Text(viewModel.isRecording ? "Recording…" : "Idle")
                .font(.headline)
                .foregroundStyle(viewModel.isRecording ? .red : .secondary)
            
            if let currentData = viewModel.currentData {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Pitch: \(currentData.pitch, specifier: "%.3f")")
                    Text("Roll: \(currentData.roll, specifier: "%.3f")")
                    Text("Yaw: \(currentData.yaw, specifier: "%.3f")")
                }
            } else {
                Text("No motion data.")
            }
        }
        HStack(spacing: 24) {
            if !viewModel.isRecording {
                Button {
                    viewModel.startSession()
                } label: {
                    Text("Start Session")
                }
                .buttonStyle(.borderedProminent)
            } else {
                Button(role: .cancel) {
                    viewModel.endSession()
                } label: {
                    Text("End Session")
                }
                .buttonStyle(.bordered)
            }
        }
        .padding()
    }
}

#Preview {
    SessionView()
}
