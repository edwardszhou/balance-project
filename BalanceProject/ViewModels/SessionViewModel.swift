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
    var currentData: MotionDatapoint?
    var isRecording: Bool = false
    
    private let motionService = AirpodMotionService()
    
    init() {
        motionService.onUpdate = { [weak self] data in
            guard let self, self.isRecording else { return }
            
            let datapoint = MotionDatapoint(data)
            
            self.currentSession?.addDatapoint(datapoint)
            self.currentData = datapoint
        }
    }
    
    func startSession() {
        guard !isRecording else { return }
        
        currentSession = MotionSession()
        motionService.startTracking()

        isRecording = true
    }
    func endSession() -> MotionSession? {
        guard isRecording, var session = currentSession else { return nil }
        
        motionService.stopTracking()
        session.end()
        
        currentSession = nil
        isRecording = false
        
        return session
    }
}
