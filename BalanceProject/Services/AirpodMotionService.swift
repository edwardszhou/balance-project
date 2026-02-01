//
//  AirpodMotionService.swift
//  BalanceProject
//

import Foundation
import CoreMotion

class AirpodMotionService: MotionService {
    private let motionManager = CMHeadphoneMotionManager()
    
    func startTracking() {
        guard motionManager.isDeviceMotionAvailable else {
            print("Headphone Motion is not available on this device.")
            return
        }

        motionManager.startDeviceMotionUpdates(to: motionQueue) { [weak self] motion, error in
            guard let self, let motion, error == nil else { return }
            self.handleUpdate(motion)
        }
    }
    
    func stopTracking() {
        motionManager.stopDeviceMotionUpdates()
        motionQueue.addOperation { [weak self] in
            self?.reset()
        }
    }
}
