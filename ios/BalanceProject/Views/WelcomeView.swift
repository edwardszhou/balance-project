//
//  WelcomeView.swift
//  BalanceProject
//

import SwiftUI

struct OnboardingView: View {
    
    @AppStorage("userName") private var userName = ""
    @State private var tempName = ""
    
    var body: some View {
        VStack(spacing: 24) {
            
            LinearGradient(
                colors: [.blue, .teal],
                startPoint: .leading,
                endPoint: .trailing
            ).mask(
                Text("Welcome to TrueBalance")
                    .font(.system(size: 36, weight: .bold))
            ).frame(maxHeight: 200)
            
            Text("Please enter your name:")
                .font(.headline)
            
            TextField("Name", text: $tempName)
                .multilineTextAlignment(TextAlignment.center)
                .padding()
                .background(
                    Capsule()
                        .fill(Color.gray.opacity(0.2))
                )
                .padding(.horizontal, 64)
            
            Button {
                guard !tempName.trimmingCharacters(in: .whitespaces).isEmpty else {
                    return
                }
                userName = tempName
            } label: {
                Text("Continue")
            }
            .buttonStyle(.borderedProminent)
        }
        .padding()
    }
}
