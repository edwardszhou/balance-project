//
//  AirpodMotionService.swift
//  BalanceProject
//

import Foundation
import CoreMotion

class AirpodMotionService {
    private let motionManager = CMHeadphoneMotionManager()
    private let motionQueue: OperationQueue = {
        let queue = OperationQueue()
        queue.qualityOfService = .userInteractive
        return queue
    }()

    var onUpdate: ((CMDeviceMotion, Double) -> Void)?
    
    private var lastTimestamp: TimeInterval?
    private var lastTimestampDeltas: [TimeInterval] = []
    private let maxDeltas = 20
    
    func startTracking() {
        guard motionManager.isDeviceMotionAvailable else {
            print("Headphone Motion is not available on this device.")
            return
        }
        
        lastTimestamp = nil
        lastTimestampDeltas.removeAll()
        
        motionManager.startDeviceMotionUpdates(to: motionQueue) { [weak self] motion, error in
            guard let self, let motion, error == nil else { return }
            
            let hz = getHertz(motion.timestamp)
            self.onUpdate?(motion, hz)
        }
    }
    
    func stopTracking() {
        motionManager.stopDeviceMotionUpdates()
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
