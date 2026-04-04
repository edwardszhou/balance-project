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
    @State private var selectedSessions: Set<UUID> = []
    @Environment(\.editMode) private var editMode
    
    var body: some View {
        List(selection: $selectedSessions) {
            if sessions.isEmpty {
                ContentUnavailableView("No sessions recorded", systemImage: "clock")
            }
            
            ForEach(sessions) { session in
                SessionRowView(
                    session: session,
                    isEditing: editMode?.wrappedValue == .active,
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
                .tag(session.id)
                .selectionDisabled(editMode?.wrappedValue != .active)
            }
        }
        .navigationTitle("Session History")
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                EditButton()
            }
            ToolbarItemGroup(placement: .bottomBar) {
                if editMode?.wrappedValue == .active && selectedSessions.count > 0 {
                    Spacer()
                    Menu("Export \(selectedSessions.count) sessions ") {
                        Button("Graph") {
                            let sessionsToExport = sessions.filter { selectedSessions.contains($0.id) }
                            viewModel.prepareBulkExport(sessions: sessionsToExport, type: .graph)
                        }
                        Button("CSV") {
                            let sessionsToExport = sessions.filter { selectedSessions.contains($0.id) }
                            viewModel.prepareBulkExport(sessions: sessionsToExport, type: .csv)
                        }
                        Button("JSON") {
                            let sessionsToExport = sessions.filter { selectedSessions.contains($0.id) }
                            viewModel.prepareBulkExport(sessions: sessionsToExport, type: .json)
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
        .sheet(isPresented: Binding(
            get: { !viewModel.bulkExportURLs.isEmpty },
            set: { if !$0 { viewModel.bulkExportURLs = [] } }
        )) {
            VStack(spacing: 20) {
                Text("Files Ready")
                    .font(.headline)
                ShareLink("Save \(viewModel.bulkExportURLs.count) Sessions", items: viewModel.bulkExportURLs)
                    .controlSize(.large)
                    .buttonStyle(.borderedProminent)
            }
            .presentationDetents([.height(200)])
        }
    }
}

struct SessionRowView: View {
    let session: MotionSession
    var isEditing: Bool
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
            .selectionDisabled(true)
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
                SessionExportButton(session: session, viewModel: viewModel, isEditing: isEditing)
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
    var isEditing: Bool
    
    @State private var isExporting = false
    
    var body: some View {
        Button {
            isExporting = true
        } label: {
            Image(systemName: "square.and.arrow.up")
        }
        .buttonStyle(.bordered)
        .buttonBorderShape(.circle)
        .disabled(isEditing)
        .confirmationDialog(
            "Select Export Format",
            isPresented: $isExporting
        ) {
            Button("JSON") { viewModel.prepareExport(session: session, type: .json) }
            Button("CSV") { viewModel.prepareExport(session: session, type: .csv) }
            Button("Graph") { viewModel.prepareExport(session: session, type: .graph) }
            Button("Cancel", role: .cancel) {}
        }
    }
}

extension URL: @retroactive Identifiable {
    public var id: String { self.absoluteString }
}
