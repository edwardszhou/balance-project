//
//  SessionHistoryView.swift
//  BalanceProject
//

import SwiftUI

struct SessionHistoryView: View {
    
    @Bindable var viewModel: SessionHistoryViewModel
    
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
                    Button {
                        viewModel.prepareExport(session)
                    } label: {
                        if viewModel.isPreparingExport {
                            ProgressView()
                        } else {
                            Image(systemName: "square.and.arrow.up")
                        }
                    }
                    .buttonStyle(.bordered)
                    .disabled(viewModel.isPreparingExport)
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
