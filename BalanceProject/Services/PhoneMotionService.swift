//
//  PhoneMotionService.swift
//  BalanceProject
//

import Foundation
import CoreMotion

class PhoneMotionService: MotionService {
    private let motionManager = CMMotionManager()
    
    func startTracking() {
        guard motionManager.isDeviceMotionAvailable else {
            print("Phone Motion is not available on this device.")
            return
        }
        motionManager.deviceMotionUpdateInterval = 1.0 / 100.0
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

