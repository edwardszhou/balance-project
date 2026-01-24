//
//  GraphDatapoint.swift
//  BalanceProject
//
//  Created by Edward Zhou on 1/23/26.
//

import Foundation

struct GraphDatapoint: Identifiable {
    let id = UUID()
    let time: TimeInterval
    let value: Double
    let label: String
}
