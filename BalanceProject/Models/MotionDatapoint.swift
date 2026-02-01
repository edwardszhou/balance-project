//
//  MotionDatapoint.swift
//  BalanceProject
//

import Foundation
import CoreMotion

enum MotionSource : String, Codable {
    case phone
    case airpods
}

struct MotionDatapoint: Codable, Identifiable {

    let source: MotionSource
    let id: UUID
    let timestamp: Date
    let epochMilliseconds: Int64


    let pitch: Double
    let roll: Double
    let yaw: Double

    let rotationRateX: Double
    let rotationRateY: Double
    let rotationRateZ: Double

    let accelerationX: Double
    let accelerationY: Double
    let accelerationZ: Double

    init(_ motion: CMDeviceMotion, motionSource: MotionSource) {
        id = UUID()
        source = motionSource
        timestamp = Date()
        epochMilliseconds = Int64(timestamp.timeIntervalSince1970 * 1000)

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
