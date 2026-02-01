//
//  MotionService.swift
//  BalanceProject
//

import Foundation
import CoreMotion

class MotionService {
    var onUpdate: ((CMDeviceMotion, Double) -> Void)?
    
    private var lastTimestamp: TimeInterval?
    private var lastTimestampDeltas: [TimeInterval] = []
    private let maxDeltas = 20
    
    func handleUpdate(_ motion: CMDeviceMotion) {
        let hz = getHertz(motion.timestamp)
        onUpdate?(motion, hz)
    }
    
    func reset() {
        lastTimestamp = nil
        lastTimestampDeltas.removeAll()
    }
    
    private func getHertz(_ timestamp: TimeInterval) -> Double {
        defer { lastTimestamp = timestamp }
        
        guard let lastTimestamp else { return 0 }
        let delta = timestamp - lastTimestamp
        guard delta > 0 else { return 0 }
        
        lastTimestampDeltas.append(delta)
        if lastTimestampDeltas.count > maxDeltas {
            lastTimestampDeltas.removeFirst()
        }
        
        let avgDelta = lastTimestampDeltas.reduce(0, +) / Double(lastTimestampDeltas.count)

        return 1.0 / avgDelta
        
        
    }
}
