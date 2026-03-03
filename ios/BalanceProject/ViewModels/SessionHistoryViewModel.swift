//
//  SessionHistoryViewModel.swift
//  BalanceProject
//

import Foundation
import Observation

@Observable
class SessionHistoryViewModel {
    @MainActor var sessions: [MotionSession] = []
    @MainActor var exportURL: URL?
    @MainActor var sessionToExport: MotionSession?
    @MainActor var sessionToUpload: MotionSession?
    
    private let exportService = SessionExportService()
    private let uploadService = SessionUploadService()
    
    enum SessionExportType {
        case graph
        case json
        case csv
    }
    
    func prepareExport(type: SessionExportType = .json) {
        guard let sessionToExport else { return }
        
        Task.detached(priority: .userInitiated) { [weak self] in
            guard let self else { return }
            
            let url: URL?
            switch type {
            case .json:
                url = await self.exportService.exportToJSON(sessionToExport)
            case .graph:
                url = await self.exportService.exportGraph(sessionToExport)
            case .csv:
                url = await self.exportService.exportToCSV(sessionToExport)
            }
            
            await MainActor.run {
                self.exportURL = url
                self.sessionToExport = nil
            }
        }
    }
    
    func uploadSession(_ session: MotionSession) {
        self.sessionToUpload = session
        Task.detached(priority: .userInitiated) { [weak self] in
            guard let self else { return }
            do {
                try await self.uploadService.uploadJSON(session)
                session.isUploaded = true
            } catch {
                print("Failed to upload session: \(error)")
            }
            await MainActor.run { self.sessionToUpload = nil }
        }
    }
}

