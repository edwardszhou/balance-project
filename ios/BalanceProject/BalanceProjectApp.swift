//
//  BalanceProjectApp.swift
//  BalanceProject
//

import SwiftUI
import SwiftData

@main
struct BalanceProjectApp: App {
    @AppStorage("userName") private var userName = ""
    
    var body: some Scene {
        WindowGroup {
            ZStack {
                if userName.count > 0 {
                    SessionView()
                        .transition(.move(edge: .trailing))
                        .modelContainer(for: MotionSession.self)
                } else {
                    OnboardingView()
                        .transition(.move(edge: .leading))
                }
            }
            .animation(.easeInOut(duration: 0.35), value: userName.count > 0)
        }
    }
}
