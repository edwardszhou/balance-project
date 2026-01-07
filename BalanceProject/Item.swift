//
//  Item.swift
//  BalanceProject
//
//  Created by Edward Zhou.
//

import Foundation
import SwiftData

@Model
final class Item {
    var timestamp: Date
    
    init(timestamp: Date) {
        self.timestamp = timestamp
    }
}
