//
//  SessionUploadService.swift
//  BalanceProject
//
//  Created by Edward Zhou on 2/28/26.
//

import Foundation

class SessionUploadService {
    
    func uploadJSON(_ session: MotionSession) async throws {
        guard let url = URL(string: "http://64.227.6.233:3000/app-sessions") else {
            throw URLError(.badURL)
        }
        
        let data = try encodeSessionJSON(session)
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = data
    
        let (_, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              200..<300 ~= httpResponse.statusCode else {
            print((response as! HTTPURLResponse).statusCode)
            print(response)
            throw URLError(.badServerResponse)
        }
    }
    
}
