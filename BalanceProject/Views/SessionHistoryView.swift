//
//  SessionHistoryView.swift
//  BalanceProject
//

import SwiftUI

struct SessionHistoryView: View {
    
    @Bindable var viewModel: SessionHistoryViewModel
    
    private let exportActions: [(SessionHistoryViewModel.SessionExportType, String)] = [
        (.json, "square.and.arrow.up"),
        (.csv, "tablecells"),
        (.graph, "chart.xyaxis.line"),
    ]
    
    var body: some View {
        List {
            if viewModel.sessions.isEmpty {
                ContentUnavailableView("No sessions recorded", systemImage: "clock")
            }

            ForEach(viewModel.sessions) { session in
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
                        
                        Text("Samples: \(session.airpodsDatapoints.count)")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    .padding(.vertical, 4)
                    Spacer()
                    HStack(spacing: 8) {
                        ForEach(exportActions, id: \.0) { type, systemImage in
                            Button {
                                viewModel.prepareExport(session, type: type)
                            } label: {
                                Image(systemName: systemImage)
                            }
                            .buttonStyle(.bordered)
                            .disabled(viewModel.isPreparingExport)
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
