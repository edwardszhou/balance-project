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
    var currentData: MotionDatapoint?
    var isRecording: Bool = false
    
    private let motionService = AirpodMotionService()
    
    init() {
        motionService.onUpdate = { [weak self] data in
            guard let self else { return }
            
            let datapoint = MotionDatapoint(motion: data)
            
            self.currentData = datapoint
        }
    }
    
    func startSession() {
        guard !isRecording else { return }
        
        motionService.startTracking()
        isRecording = true
    }
    func endSession() {
        guard isRecording else { return }
        
        motionService.stopTracking()
        isRecording = false
    }
}
