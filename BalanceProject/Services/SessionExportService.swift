//
//  SessionExportService.swift
//  BalanceProject
//

import SwiftUI

class SessionExportService {
    
    func exportGraph(_ session: MotionSession) -> URL? {
        guard session.endDate != nil else {
            print("Session has not ended yet.")
            return nil
        }
        
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
    func exportToCSV(_ session: MotionSession) -> URL? {
        guard session.endDate != nil else {
            print("Session has not ended yet.")
            return nil
        }
        
        var csv = csvHeader() + "\n"
        for datapoint in session.datapoints {
            csv.append(csvRow(from: datapoint))
            csv.append("\n")
        }

        let fileURL = getFileUrl(session.id, fileType: "csv")

        do {
            try csv.write(to: fileURL, atomically: true, encoding: .utf8)
            return fileURL
        } catch {
            print("Failed to export session as csv: \(error)")
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
    
    private func csvHeader() -> String {
        [
            "id",
            "timestamp",
            "pitch",
            "roll",
            "yaw",
            "rotation_x",
            "rotation_y",
            "rotation_z",
            "accel_x",
            "accel_y",
            "accel_z"
        ].joined(separator: ",")
    }

    private func csvRow(from datapoint: MotionDatapoint) -> String {
        [
            datapoint.id.uuidString,
            ISO8601DateFormatter().string(from: datapoint.timestamp),
            String(format: "%.6f", datapoint.pitch),
            String(format: "%.6f", datapoint.roll),
            String(format: "%.6f", datapoint.yaw),
            String(format: "%.6f", datapoint.rotationRateX),
            String(format: "%.6f", datapoint.rotationRateY),
            String(format: "%.6f", datapoint.rotationRateZ),
            String(format: "%.6f", datapoint.accelerationX),
            String(format: "%.6f", datapoint.accelerationY),
            String(format: "%.6f", datapoint.accelerationZ)
        ].joined(separator: ",")
    }

}
