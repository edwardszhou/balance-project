//
//  SessionHistoryView.swift
//  BalanceProject
//

import SwiftUI
import SwiftData

struct SessionHistoryView: View {
    
    @Query(sort: \MotionSession.startDate, order: .reverse)
    var sessions: [MotionSession]
    
    @State private var viewModel = SessionHistoryViewModel()
    
    var body: some View {
        List {
            if sessions.isEmpty {
                ContentUnavailableView("No sessions recorded", systemImage: "clock")
            }
            
            ForEach(sessions) { session in
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        if let name = session.name {
                            Text(name)
                                .font(.headline)
                            Text(session.startDate.formatted(date: .abbreviated, time: .shortened))
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        } else {
                            Text(session.startDate.formatted(date: .abbreviated, time: .shortened))
                                .font(.headline)
                        }
                        Spacer()
                        Text("Airpods Samples: \(session.airpodsDatapoints.count)")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        Text("Phone Samples: \(session.phoneDatapoints.count)")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    .padding(.vertical, 4)
                    Spacer()
                    HStack(spacing: 8) {
                        if session.isUploaded {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundStyle(.green)
                        } else {
                            Button {
                                
                            } label: {
                                Image(systemName: "arrow.triangle.2.circlepath.circle")
                            }
                            .buttonStyle(.bordered)
                            .disabled(viewModel.sessionToExport != nil)
                        }
                        Button {
                            viewModel.sessionToExport = session
                        } label: {
                            Image(systemName: "square.and.arrow.up")
                        }
                        .buttonStyle(.bordered)
                        .disabled(viewModel.sessionToExport != nil)
                        .confirmationDialog(
                            "Select Export Format",
                            isPresented: Binding(
                                get: { viewModel.sessionToExport == session && viewModel.sessionToExport != nil },
                                set: { if !$0 { viewModel.sessionToExport = nil } }
                            ),
                            titleVisibility: .visible
                        ) {
                            Button("JSON") { viewModel.prepareExport(type: .json) }
                            Button("CSV") { viewModel.prepareExport(type: .csv) }
                            Button("Graph") { viewModel.prepareExport(type: .graph) }
                            Button("Cancel", role: .cancel) {}
                        }
                    }
                }
            }
        }
        .sheet(item: $viewModel.exportURL) { url in
            VStack(spacing: 20) {
                Text("File Ready")
                    .font(.headline)
                ShareLink("Save Session", item: url)
                    .controlSize(.large)
                    .buttonStyle(.borderedProminent)
            }
            .presentationDetents([.height(200)])
        }
        .navigationTitle("Session History")
    }
}

extension URL: @retroactive Identifiable {
    public var id: String { self.absoluteString }
}
