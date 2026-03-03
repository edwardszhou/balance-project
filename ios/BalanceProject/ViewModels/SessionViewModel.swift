//
//  SessionViewModel.swift
//  BalanceProject
//

import Foundation
import CoreMotion
import Observation
import SwiftUI

@Observable
@MainActor
class SessionViewModel {
    @ObservationIgnored @AppStorage("userName") private var userName = ""
    
    var currentSession: MotionSession?
    
    var currentAirpodsData: MotionDatapoint?
    var currentAirpodsHz: TimeInterval = 0
    var currentPhoneData: MotionDatapoint?
    var currentPhoneHz: TimeInterval = 0
    
    var isRecording: Bool = false
    
    private let uploadService = SessionUploadService()
    
    private let airpodsMotion = AirpodsMotionService()
    private let phoneMotion = PhoneMotionService()
    
    init() {
        airpodsMotion.onUpdate = { [weak self] data, timing in
            guard let self, self.isRecording else { return }
            
            let datapoint = MotionDatapoint(data, timing: timing, source: .airpods)
            
            Task{ @MainActor in
                self.currentSession?.addDatapoint(datapoint)
                self.currentAirpodsData = datapoint
                self.currentAirpodsHz = timing.sampleRateHz
            }
        }
        
        phoneMotion.onUpdate = { [weak self] data, timing in
            guard let self, self.isRecording else { return }
            
            let datapoint = MotionDatapoint(data, timing: timing, source: .phone)
            
            Task{ @MainActor in
                self.currentSession?.addDatapoint(datapoint)
                self.currentPhoneData = datapoint
                self.currentPhoneHz = timing.sampleRateHz
            }
        }
    }
    
    func startSession() {
        guard !isRecording else { return }
        
        currentSession = MotionSession(userName: userName)
        airpodsMotion.startTracking()
        phoneMotion.startTracking()

        isRecording = true
    }
    func endSession() -> MotionSession? {
        guard isRecording, let session = currentSession else { return nil }
        
        airpodsMotion.stopTracking()
        phoneMotion.stopTracking()
        session.end()
        
        currentSession = nil
        currentAirpodsHz = 0
        currentPhoneHz = 0
        isRecording = false
        
        return session
    }
    
    func uploadSession(_ session: MotionSession) {
        Task.detached(priority: .userInitiated) { [weak self] in
            guard let self else { return }
            do {
                try await self.uploadService.uploadJSON(session)
                session.isUploaded = true
            } catch {
                print("Failed to upload session: \(error)")
            }
        }
    }
}
