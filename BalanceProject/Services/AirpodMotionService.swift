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

    var onUpdate: ((CMDeviceMotion) -> Void)?
    
    func startTracking() {
        guard motionManager.isDeviceMotionAvailable else {
            print("Headphone Motion is not available on this device.")
            return
        }
        
        motionManager.startDeviceMotionUpdates(to: motionQueue) { [weak self] motion, error in
            guard let self, let motion, error == nil else { return }
            
            self.onUpdate?(motion)
        }
    }
    
    func stopTracking() {
        motionManager.stopDeviceMotionUpdates()
    }
}
