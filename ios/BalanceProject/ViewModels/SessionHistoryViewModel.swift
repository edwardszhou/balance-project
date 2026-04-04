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
    @MainActor var bulkExportURLs: [URL] = []
    @MainActor var sessionToUpload: MotionSession?
    
    private let exportService = SessionExportService()
    private let uploadService = SessionUploadService()
    
    enum SessionExportType {
        case graph
        case json
        case csv
    }
    
    func prepareExport(session: MotionSession, type: SessionExportType = .json) {
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
            
            await MainActor.run { self.exportURL = url }
        }
    }
    
    func prepareBulkExport(sessions: [MotionSession], type: SessionExportType = .json) {
        Task.detached(priority: .userInitiated) { [weak self] in
            guard let self else { return }
            
            let urls: [URL] = await withTaskGroup(of: URL?.self) { group in
                for session in sessions {
                    group.addTask {
                        switch type {
                        case .json: return await self.exportService.exportToJSON(session)
                        case .graph: return await self.exportService.exportGraph(session)
                        case .csv: return await self.exportService.exportToCSV(session)
                        }
                    }
                }
                var results: [URL] = []
                for await url in group {
                    if let url { results.append(url) }
                }
                return results
            }
            
            await MainActor.run { self.bulkExportURLs = urls }
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

