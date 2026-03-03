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
    @State private var expandedSessions: Set<UUID> = []
    
    var body: some View {
        List {
            if sessions.isEmpty {
                ContentUnavailableView("No sessions recorded", systemImage: "clock")
            }
            
            ForEach(sessions) { session in
                SessionRowView(
                    session: session,
                    isExpanded: Binding(
                        get: { expandedSessions.contains(session.id) },
                        set: { newValue in
                            withAnimation(.easeInOut) {
                                if newValue {
                                    expandedSessions.insert(session.id)
                                } else {
                                    expandedSessions.remove(session.id)
                                }
                            }
                        }
                    ),
                    viewModel: viewModel
                )
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

struct SessionRowView: View {
    let session: MotionSession
    
    @Binding var isExpanded: Bool
    var viewModel: SessionHistoryViewModel
    
    var body: some View {
        DisclosureGroup(
            isExpanded: $isExpanded
        ) {
            VStack(alignment: .leading, spacing: 2) {
                Text("AirPods Samples: \(session.airpodsDatapoints.count)")
                Text("Phone Samples: \(session.phoneDatapoints.count)")
                Text("Duration: \(formatDuration(session.startDate, session.endDate))")
            }
            .font(.caption)
            .foregroundStyle(.secondary)
            .padding(.leading, -16)
        } label: {
            HStack {
                VStack(alignment: .leading) {
                    HStack {
                        Text(session.name ?? "Untitled")
                            .font(.headline)
                        if session.isUploaded {
                            Image(systemName: "checkmark.circle")
                                .resizable()
                                .frame(width: 14, height: 14)
                                .foregroundStyle(.green)
                        } else {
                            Button {
                                viewModel.uploadSession(session)
                            } label: {
                                Image(systemName: "exclamationmark.circle")
                                    .resizable()
                                    .frame(width: 14, height: 14)
                                    .foregroundStyle(.red)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                    Text(session.isUploaded ? "Uploaded" : viewModel.sessionToUpload == session ? "Retrying upload..." : "Failed to upload")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text(session.startDate.formatted(date: .abbreviated, time: .shortened))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                SessionExportButton(session: session, viewModel: viewModel)
            }
            .padding(.vertical, 4)
        }
        .listRowSeparator(isExpanded ? .hidden : .visible)
    }
    
    private func formatDuration(_ start: Date, _ end: Date?) -> String {
        guard let end = end else { return "Unknown" }
        let interval = Int(end.timeIntervalSince(start))
        let minutes = interval / 60
        let seconds = interval % 60
        return "\(minutes)m \(seconds)s"
    }
}

struct SessionExportButton: View {
    let session: MotionSession
    var viewModel: SessionHistoryViewModel
    
    var body: some View {
        Button {
            viewModel.sessionToExport = session
        } label: {
            Image(systemName: "square.and.arrow.up")
        }
        .buttonStyle(.bordered)
        .buttonBorderShape(.circle)
        .disabled(viewModel.sessionToExport != nil)
        .confirmationDialog(
            "Select Export Format",
            isPresented: Binding(
                get: { viewModel.sessionToExport == session },
                set: { if !$0 { viewModel.sessionToExport = nil } }
            )
        ) {
            Button("JSON") { viewModel.prepareExport(type: .json) }
            Button("CSV") { viewModel.prepareExport(type: .csv) }
            Button("Graph") { viewModel.prepareExport(type: .graph) }
            Button("Cancel", role: .cancel) {}
        }
    }
}

extension URL: @retroactive Identifiable {
    public var id: String { self.absoluteString }
}
