//
//  MotionSession.swift
//  BalanceProject
//

import Foundation
import CoreMotion
import SwiftData
import UIKit

@Model
class MotionSession {

    @Attribute(.unique) var id: UUID = UUID()
    var userId: String = UIDevice.current.identifierForVendor?.uuidString ?? "unknown"
    var userName: String = "unknown"
    var startDate: Date = Date()
    
    var name: String?
    var endDate: Date?
    var isUploaded: Bool = false
    var airpodsDatapoints: [MotionDatapoint] = []
    var phoneDatapoints: [MotionDatapoint] = []

    init(userName: String) {
        self.userName = userName
    }
    
    func addDatapoint(_ datapoint: MotionDatapoint) {
        switch datapoint.source {
        case .airpods: airpodsDatapoints.append(datapoint)
        case .phone: phoneDatapoints.append(datapoint)
        }
    }
    
    func end() {
        endDate = Date()
    }
    
    func exportDTO() -> MotionSessionDTO {
        guard let endDate, let name else { fatalError("Session not yet ended") }
        
        return MotionSessionDTO(
            id: id,
            name: name,
            userId: userId,
            userName: userName,
            startDate: startDate,
            endDate: endDate,
            airpodsDatapoints: airpodsDatapoints,
            phoneDatapoints: phoneDatapoints
        )
    }
}

struct MotionSessionDTO: Codable {
    let id: UUID
    let name: String
    let userId: String
    let userName: String
    let startDate: Date
    let endDate: Date
    let airpodsDatapoints: [MotionDatapoint]
    let phoneDatapoints: [MotionDatapoint]
}
