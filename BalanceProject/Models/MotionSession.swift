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
    var datapoints: [MotionDatapoint]

    init() {
        id = UUID()
        startDate = Date()
        datapoints = []
    }
    
    mutating func addDatapoint(_ datapoint: MotionDatapoint) {
        datapoints.append(datapoint)
    }
    
    mutating func end() {
        endDate = Date()
    }
}
