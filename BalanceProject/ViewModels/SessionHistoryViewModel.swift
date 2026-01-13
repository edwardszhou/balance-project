//
//  SessionHistoryViewModel.swift
//  BalanceProject
//

import Foundation
import Observation

@Observable
class SessionHistoryViewModel {
    var sessions: [MotionSession] = []
    
    func addSession (_ session: MotionSession) {
        sessions.insert(session, at: 0)
    }
}
