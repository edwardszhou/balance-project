//
//  MotionService.swift
//  BalanceProject
//

import Foundation
import CoreMotion

class MotionService {
    var onUpdate: ((CMDeviceMotion, MotionTiming) -> Void)?
    
    // Monotonic to world time
    private var startTimeWorld: Date?
    private var startTimestamp: TimeInterval?
    
    // Sliding window average over dt for sample rate
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
        startTimeWorld = nil
        startTimestamp = nil
        lastTimestamp = nil
        lastTimestampDeltas.removeAll()
    }
    
    private func getTiming(_ timestamp: TimeInterval) -> MotionTiming {
        defer { lastTimestamp = timestamp }
        
        let worldTimestamp = monotonicToWorld(timestamp)
        guard let lastTimestamp else { return MotionTiming(worldTimestamp, dt: 0, hz: 0) }
        
        let dt = timestamp - lastTimestamp
        guard dt > 0 else { return MotionTiming(worldTimestamp, dt: 0, hz: 0) }
        
        lastTimestampDeltas.append(dt)
        if lastTimestampDeltas.count > maxDeltas {
            lastTimestampDeltas.removeFirst()
        }
        
        let hz = Double(lastTimestampDeltas.count) / lastTimestampDeltas.reduce(0, +)

        return MotionTiming(worldTimestamp, dt: dt, hz: hz)
    }
    
    private func monotonicToWorld(_ timestamp: TimeInterval) -> Date {
        guard let startTimeWorld, let startTimestamp else {
            startTimeWorld = Date()
            startTimestamp = timestamp
            return startTimeWorld!
        }
        return startTimeWorld.addingTimeInterval(timestamp - startTimestamp)
    }
}
