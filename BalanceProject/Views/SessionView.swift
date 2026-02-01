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
            VStack {
                Text("Balance Project")
                    .font(.system(size: 36, weight: .bold))
                    .foregroundColor(.primary)
            }
            .padding(24)
            .toolbar {
                NavigationLink("History") {
                    SessionHistoryView(viewModel: historyViewModel)
                }
            }
            Spacer()
            TabView {
                MotionDataView(
                    title: "Airpods Motion",
                    imageSystemName: "airpodspro",
                    isRecording: sessionViewModel.isRecording,
                    data: sessionViewModel.currentAirpodsData,
                    sampleRate: sessionViewModel.currentAirpodsHz
                )
                MotionDataView(
                    title: "iPhone Motion",
                    imageSystemName: "iphone.motion",
                    isRecording: sessionViewModel.isRecording,
                    data: sessionViewModel.currentPhoneData,
                    sampleRate: sessionViewModel.currentPhoneHz
                )
            }
            .tabViewStyle(.page)
            .frame(maxHeight: .infinity)
            Spacer()
            HStack{
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
            .padding(24)
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

struct MotionDataView: View {
    let title: String
    let imageSystemName: String
    let isRecording: Bool
    let data: MotionDatapoint?
    let sampleRate: Double
    
    var body: some View {
        VStack(spacing: 8) {
            Text(title)
                .font(.headline)
            Image(systemName: imageSystemName)
                .font(.system(size: 24))
                .foregroundColor(.blue)
            Text(isRecording ? "Recording" : "Not recording")
                .font(.system(size: 18, weight: .semibold))
                .foregroundStyle(isRecording ? .red : .secondary)
            Spacer()
            VStack(alignment: .leading) {
                if let data {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Sample Rate (Hz): \(sampleRate, specifier: "%.1f")")
                        Spacer().frame(maxHeight: 16)
                        Text("Pitch: \(data.pitch, specifier: "%.3f")")
                        Text("Roll: \(data.roll, specifier: "%.3f")")
                        Text("Yaw: \(data.yaw, specifier: "%.3f")")
                        Spacer().frame(maxHeight: 16)
                        Text("Rotation Rate X: \(data.rotationRateX, specifier: "%.3f")")
                        Text("Rotation Rate Y: \(data.rotationRateY, specifier: "%.3f")")
                        Text("Rotation Rate Z: \(data.rotationRateZ, specifier: "%.3f")")
                        Spacer().frame(maxHeight: 16)
                        Text("Acceleration X: \(data.accelerationX, specifier: "%.3f")")
                        Text("Acceleration Y: \(data.accelerationY, specifier: "%.3f")")
                        Text("Acceleration Z: \(data.accelerationZ, specifier: "%.3f")")
                    }
                } else {
                    Text("No data yet.")
                        .foregroundStyle(.secondary)
                }
            }
            .frame(height: 360, alignment: .center)
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 24)
                .fill(Color(UIColor.systemGray6))
                .frame(width: 300))
        .padding(.horizontal)
    }
}

#Preview {
    SessionView()
}
