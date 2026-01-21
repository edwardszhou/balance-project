//
//  SessionHistoryViewModel.swift
//  BalanceProject
//

import Foundation
import Observation

@Observable
class SessionHistoryViewModel {
    var sessions: [MotionSession] = []
    var exportURL: URL?
    var isPreparingExport = false
    
    private let exportService = SessionExportService()
    
    func addSession (_ session: MotionSession) {
        sessions.insert(session, at: 0)
    }
    
    enum SessionExportType {
        case graph
        case json
    }
    
    func prepareExport(_ session: MotionSession, type: SessionExportType = .json) {
        isPreparingExport = true
        
        // Run on a background thread so the UI doesn't freeze
        DispatchQueue.global(qos: .userInitiated).async {
            let url: URL?
            switch type {
            case .json:
                url = self.exportService.exportToJSON(session)
            case .graph:
                url = self.exportService.exportGraph(session)
            }

            DispatchQueue.main.async {
                self.exportURL = url
                self.isPreparingExport = false
            }
        }
    }
}
