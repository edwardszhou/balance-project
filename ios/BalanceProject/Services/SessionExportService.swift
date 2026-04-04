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

        let fileUrl = getFileUrl(session, fileType: "png")
        
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
        
        do {
            let data = try encodeSessionJSON(session)
            let fileUrl = getFileUrl(session, fileType: "json")
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
        for datapoint in session.airpodsDatapoints {
            csv.append(csvRow(from: datapoint))
            csv.append("\n")
        }
        for datapoint in session.phoneDatapoints {
            csv.append(csvRow(from: datapoint))
            csv.append("\n")
        }

        let fileURL = getFileUrl(session, fileType: "csv")

        do {
            try csv.write(to: fileURL, atomically: true, encoding: .utf8)
            return fileURL
        } catch {
            print("Failed to export session as csv: \(error)")
            return nil
        }
    }

    
    private func getFileUrl(_ session: MotionSession, fileType: String) -> URL {
        let directory = FileManager.default.urls(
            for: .documentDirectory,
            in: .userDomainMask
        )[0]
        
        let filename: String
        if let name = session.name, !name.isEmpty {
            filename = sanitizeFileName(name)
        } else {
            filename = "motion-session"
        }
        return directory
            .appendingPathComponent(filename)
            .appendingPathExtension(fileType)
    }
    
    private func sanitizeFileName(_ name: String) -> String {
        var newName = name
        let allowed = CharacterSet.alphanumerics.union(CharacterSet(charactersIn: "-_"))
        newName = newName.unicodeScalars
            .map { allowed.contains($0) ? Character($0) : "-" }
            .map { String($0) }
            .joined()
        
        while newName.contains("--") {
            newName = newName.replacingOccurrences(of: "--", with: "-")
        }
        newName = newName.trimmingCharacters(in: CharacterSet(charactersIn: "-"))
        return newName.isEmpty ? "motion-session" : newName
    }
    
    private func csvHeader() -> String {
        [
            "source",
            "timestamp",
            "timestampEpoch",
            "deltaTime",
            "hz",
            "angle_pitch",
            "angle_roll",
            "angle_yaw",
            "rotation_rate_x",
            "rotation_rate_y",
            "rotation_rate_z",
            "accel_x",
            "accel_y",
            "accel_z"
        ].joined(separator: ",")
    }

    private func csvRow(from datapoint: MotionDatapoint) -> String {
        let isoTimestamp = datapoint.timing.timestamp.formatted(.iso8601
            .year()
            .month()
            .day()
            .timeZone(separator: .omitted)
            .time(includingFractionalSeconds: true)
            .timeSeparator(.colon)
        )
        let toString = FloatingPointFormatStyle<Double>
            .number
            .precision(.fractionLength(6))
        
        return [
            datapoint.source.rawValue,
            isoTimestamp,
            String(datapoint.timing.timestampEpoch),
            datapoint.timing.deltaTime.formatted(toString),
            datapoint.timing.sampleRateHz.formatted(toString),
            datapoint.anglePitch.formatted(toString),
            datapoint.angleRoll.formatted(toString),
            datapoint.angleYaw.formatted(toString),
            datapoint.rotationRateX.formatted(toString),
            datapoint.rotationRateY.formatted(toString),
            datapoint.rotationRateZ.formatted(toString),
            datapoint.accelerationX.formatted(toString),
            datapoint.accelerationY.formatted(toString),
            datapoint.accelerationZ.formatted(toString),
        ].joined(separator: ",")
    }

}

func encodeSessionJSON(_ session: MotionSession) throws -> Data {
    let sessionDTO = session.exportDTO()
    
    let encoder = JSONEncoder()
    let formatter = DateFormatter()
    formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSZ"
    formatter.calendar = Calendar(identifier: .iso8601)
    formatter.locale = Locale(identifier: "en_US_POSIX")
    formatter.timeZone = TimeZone(secondsFromGMT: 0)

    encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
    encoder.dateEncodingStrategy = .formatted(formatter)
    return try encoder.encode(sessionDTO)
}
