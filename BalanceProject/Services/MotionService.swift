//
//  MotionService.swift
//  BalanceProject
//

import Foundation
import CoreMotion

class MotionService {
    var onUpdate: ((CMDeviceMotion, MotionTiming) -> Void)?
    
    private var lastTimestamp: TimeInterval?
    private var lastTimestampDeltas: [TimeInterval] = []
    private let maxDeltas = 10
    
    let motionQueue: OperationQueue = {
        let queue = OperationQueue()
        queue.qualityOfService = .userInteractive
        queue.maxConcurrentOperationCount = 1
        return queue
    }()
    
    func handleUpdate(_ motion: CMDeviceMotion) {
        let timing = getTiming(motion.timestamp)
        onUpdate?(motion, timing)
    }
    
    func reset() {
        lastTimestamp = nil
        lastTimestampDeltas.removeAll()
    }
    
    private func getTiming(_ timestamp: TimeInterval) -> MotionTiming {
        defer { lastTimestamp = timestamp }
        
        let now = Date()
        guard let lastTimestamp else { return MotionTiming(now, dt: 0, hz: 0) }
        let delta = timestamp - lastTimestamp
        guard delta > 0 else { return MotionTiming(now, dt: 0, hz: 0) }
        
        lastTimestampDeltas.append(delta)
        if lastTimestampDeltas.count > maxDeltas {
            lastTimestampDeltas.removeFirst()
        }
        
        let avgDelta = lastTimestampDeltas.reduce(0, +) / Double(lastTimestampDeltas.count)

        return MotionTiming(now, dt: delta, hz: 1.0 / avgDelta)
        
        
    }
}
