//
//  MotionSession.swift
//  BalanceProject
//

import Foundation
import CoreMotion

struct MotionSession: Codable, Identifiable {

    let id: UUID
    let startDate: Date
    
    var name: String?
    var endDate: Date?
    var airpodsDatapoints: [MotionDatapoint]
    var phoneDatapoints: [MotionDatapoint]

    init() {
        id = UUID()
        startDate = Date()
        airpodsDatapoints = []
        phoneDatapoints = []
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
