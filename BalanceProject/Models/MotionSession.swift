//
//  MotionSession.swift
//  BalanceProject
//

import Foundation
import CoreMotion
import UIKit

struct MotionSession: Codable, Identifiable {

    let id: UUID
    let user: String
    let startDate: Date
    
    var name: String?
    var endDate: Date?
    var airpodsDatapoints: [MotionDatapoint]
    var phoneDatapoints: [MotionDatapoint]

    init() {
        self.id = UUID()
        self.user = UIDevice.current.identifierForVendor?.uuidString ?? "unknown"
        self.startDate = Date()
        self.airpodsDatapoints = []
        self.phoneDatapoints = []
    }
    
    mutating func addDatapoint(_ datapoint: MotionDatapoint) {
        switch datapoint.source {
        case .airpods: airpodsDatapoints.append(datapoint)
        case .phone: phoneDatapoints.append(datapoint)
        }
    }
    
    mutating func end() {
        endDate = Date()
    }
}
