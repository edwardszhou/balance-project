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

    init(_ motion: CMDeviceMotion) {
        id = UUID()
        timestamp = Date()

        pitch = motion.attitude.pitch
        roll = motion.attitude.roll
        yaw = motion.attitude.yaw

        rotationRateX = motion.rotationRate.x
        rotationRateY = motion.rotationRate.y
        rotationRateZ = motion.rotationRate.z

        accelerationX = motion.userAcceleration.x
        accelerationY = motion.userAcceleration.y
        accelerationZ = motion.userAcceleration.z
    }
}
