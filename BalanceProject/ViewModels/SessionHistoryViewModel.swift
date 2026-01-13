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
    
    func prepareExport(_ session: MotionSession) {
        isPreparingExport = true
        
        // Run on a background thread so the UI doesn't freeze
        DispatchQueue.global(qos: .userInitiated).async {
            if let url = self.exportService.exportToJSON(session) {
                DispatchQueue.main.async {
                    self.exportURL = url
                    self.isPreparingExport = false
                }
            }
        }
    }
}
