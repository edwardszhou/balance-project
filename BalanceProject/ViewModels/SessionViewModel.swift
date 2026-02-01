//
//  SessionViewModel.swift
//  BalanceProject
//

import Foundation
import CoreMotion
import Observation

@Observable
@MainActor
class SessionViewModel {
    var currentSession: MotionSession?
    
    var currentAirpodsData: MotionDatapoint?
    var currentAirpodsHz: TimeInterval = 0
    var currentPhoneData: MotionDatapoint?
    var currentPhoneHz: TimeInterval = 0
    
    var isRecording: Bool = false
    
    private let airpodsMotion = AirpodsMotionService()
    private let phoneMotion = PhoneMotionService()
    
    init() {
        airpodsMotion.onUpdate = { [weak self] data, hz in
            guard let self, self.isRecording else { return }
            
            let datapoint = MotionDatapoint(data, motionSource: .airpods)
            
            Task{ @MainActor in
                self.currentSession?.addDatapoint(datapoint)
                self.currentAirpodsData = datapoint
                self.currentAirpodsHz = hz
            }
        }
        
        phoneMotion.onUpdate = { [weak self] data, hz in
            guard let self, self.isRecording else { return }
            
            let datapoint = MotionDatapoint(data, motionSource: .phone)
            
            Task{ @MainActor in
                self.currentSession?.addDatapoint(datapoint)
                self.currentPhoneData = datapoint
                self.currentPhoneHz = hz
            }
        }
    }
    
    func startSession() {
        guard !isRecording else { return }
        
        currentSession = MotionSession()
        airpodsMotion.startTracking()
        phoneMotion.startTracking()

        isRecording = true
    }
    func endSession() -> MotionSession? {
        guard isRecording, var session = currentSession else { return nil }
        
        airpodsMotion.stopTracking()
        phoneMotion.stopTracking()
        session.end()
        
        currentSession = nil
        currentAirpodsHz = 0
        currentPhoneHz = 0
        isRecording = false
        
        return session
    }
}
