//
//  MotionDatapoint.swift
//  BalanceProject
//

import Foundation
import CoreMotion

struct MotionDatapoint: Codable, Identifiable {
    let id: UUID
    let source: MotionSource
    let timing: MotionTiming

    let anglePitch: Double
    let angleRoll: Double
    let angleYaw: Double

    let rotationRateX: Double
    let rotationRateY: Double
    let rotationRateZ: Double

    let accelerationX: Double
    let accelerationY: Double
    let accelerationZ: Double

    init(_ motion: CMDeviceMotion, timing: MotionTiming, source: MotionSource) {
        self.id = UUID()
        self.source = source
        self.timing = timing

        self.anglePitch = motion.attitude.pitch
        self.angleRoll = motion.attitude.roll
        self.angleYaw = motion.attitude.yaw

        self.rotationRateX = motion.rotationRate.x
        self.rotationRateY = motion.rotationRate.y
        self.rotationRateZ = motion.rotationRate.z

        self.accelerationX = motion.userAcceleration.x
        self.accelerationY = motion.userAcceleration.y
        self.accelerationZ = motion.userAcceleration.z
    }
}

enum MotionSource : String, Codable {
    case phone
    case airpods
}

struct MotionTiming: Codable {
    let timestamp: Date
    let timestampEpoch: Int64
    let deltaTime: TimeInterval
    let sampleRateHz: Double
    
    init(_ timestamp: Date, dt: TimeInterval, hz: Double) {
        self.timestamp = timestamp
        self.timestampEpoch = Int64(timestamp.timeIntervalSince1970 * 1000)
        self.deltaTime = dt
        self.sampleRateHz = hz
    }
}
