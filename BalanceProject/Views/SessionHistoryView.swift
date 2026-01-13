//
//  SessionHistoryView.swift
//  BalanceProject
//

import SwiftUI

struct SessionHistoryView: View {
    
    let viewModel: SessionHistoryViewModel
    
    var body: some View {
        List {
            if viewModel.sessions.isEmpty {
                Text("No sessions recorded")
                    .foregroundStyle(.secondary)
            }

            ForEach(viewModel.sessions) { session in
                VStack(alignment: .leading, spacing: 4) {
                    Text("Session")
                        .font(.headline)

                    Text("Samples: \(session.datapoints.count)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                .padding(.vertical, 4)
            }
        }
        .navigationTitle("Session History")
    }
}
