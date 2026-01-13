//
//  MotionDatapoint.swift
//  BalanceProject
//

import Foundation
import CoreMotion

struct MotionDatapoint: Codable, Identifiable {

    let id: UUID
    let timestamp: Date

    let pitch: Double
    let roll: Double
    let yaw: Double

    let rotationRateX: Double
    let rotationRateY: Double
    let rotationRateZ: Double

    let accelerationX: Double
    let accelerationY: Double
    let accelerationZ: Double

    init(motion: CMDeviceMotion) {
        self.id = UUID()
        self.timestamp = Date()

        self.pitch = motion.attitude.pitch
        self.roll = motion.attitude.roll
        self.yaw = motion.attitude.yaw

        self.rotationRateX = motion.rotationRate.x
        self.rotationRateY = motion.rotationRate.y
        self.rotationRateZ = motion.rotationRate.z

        self.accelerationX = motion.userAcceleration.x
        self.accelerationY = motion.userAcceleration.y
        self.accelerationZ = motion.userAcceleration.z
    }
}
