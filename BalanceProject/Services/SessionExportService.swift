//
//  SessionExportService.swift
//  BalanceProject
//

import SwiftUI

class SessionExportService {
    
    func exportGraph(_ session: MotionSession) -> URL? {
        let view = MotionGraphView(session: session)
            .frame(width: 1200, height: 900)

        let renderer = ImageRenderer(content: view)
        renderer.scale = 2

        let fileUrl = getFileUrl(session.id, fileType: "png")
        
        guard let image = renderer.uiImage,
              let data = image.pngData() else {
            print("Failed to export graph.")
            return nil;
        }

        do {
            try data.write(to: fileUrl, options: .atomic)
            return fileUrl
        } catch {
            print("Failed to export graph: \(error)")
            return nil
        }

    }
    
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
            let fileUrl = getFileUrl(session.id, fileType: "json")
            try data.write(to: fileUrl, options: .atomic)
            
            return fileUrl
        } catch {
            print("Failed to encode session: \(error)")
            return nil
        }
    }
    
    private func getFileUrl(_ sessionID: UUID, fileType: String) -> URL {
        let directory = FileManager.default.temporaryDirectory
        let filename = "motion-session-\(sessionID.uuidString)"
        return directory
            .appending(path: filename)
            .appendingPathExtension(fileType)
    }
}
