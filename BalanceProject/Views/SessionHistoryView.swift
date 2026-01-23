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
                        Text(session.startDate.formatted(date: .abbreviated, time: .shortened))
                            .font(.headline)
                        
                        Text("Samples: \(session.datapoints.count)")
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
                                if viewModel.isPreparingExport {
                                    ProgressView()
                                } else {
                                    Image(systemName: systemImage)
                                }
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
    
    struct ExportButton: View {

        let systemImage: String
        let isLoading: Bool
        let action: () -> Void

        var body: some View {
            Button(action: action) {
                if isLoading {
                    ProgressView()
                } else {
                    Image(systemName: systemImage)
                }
            }
            .buttonStyle(.bordered)
            .disabled(isLoading)
        }
    }
}

extension URL: @retroactive Identifiable {
    public var id: String { self.absoluteString }
}
