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
    @MainActor var isPreparingExport = false
    @MainActor var isUploading = false
    
    private let exportService = SessionExportService()
    private let uploadService = SessionUploadService()
    
    enum SessionExportType {
        case graph
        case json
        case csv
    }
    
    func prepareExport(_ session: MotionSession, type: SessionExportType = .json) {
        isPreparingExport = true
        
        Task.detached(priority: .userInitiated) { [weak self] in
            guard let self else { return }
            
            let url: URL?
            switch type {
            case .json:
                url = await self.exportService.exportToJSON(session)
            case .graph:
                url = await self.exportService.exportGraph(session)
            case .csv:
                url = await self.exportService.exportToCSV(session)
            }
            
            await MainActor.run {
                self.exportURL = url
                self.isPreparingExport = false
            }
        }
    }
}

