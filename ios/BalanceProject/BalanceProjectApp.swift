//
//  BalanceProjectApp.swift
//  BalanceProject
//

import SwiftUI
import SwiftData

@main
struct BalanceProjectApp: App {    
    var body: some Scene {
        WindowGroup {
            SessionView()
                .modelContainer(for: MotionSession.self)
        }
    }
}
