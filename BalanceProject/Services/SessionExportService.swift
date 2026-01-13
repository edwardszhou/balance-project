//
//  SessionExportService.swift
//  BalanceProject
//

import Foundation

class SessionExportService {
    
    func exportToJSON(_ session: MotionSession) -> URL? {
        guard session.endDate != nil else {
            print("Session has not ended yet.")
            return nil
        }
        
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted]
        encoder.dateEncodingStrategy = .iso8601
        
        do {
            let data = try encoder.encode(session)
            let fileUrl = getFileUrl(session.id)
            try data.write(to: fileUrl, options: .atomic)
            
            return fileUrl
        } catch {
            print("Failed to encode session: \(error)")
            return nil
        }
    }
    
    private func getFileUrl(_ sessionID: UUID) -> URL {
        let directory = FileManager.default.temporaryDirectory
        let filename = "motion-session-\(sessionID.uuidString)"
        return directory
            .appending(path: filename)
            .appendingPathExtension("json")
    }
}
