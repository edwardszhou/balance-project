//
//  MotionGraphView.swift
//  BalanceProject
//

import SwiftUI
import Charts

struct MotionGraphView: View {

    let session: MotionSession

    var body: some View {
        VStack(spacing: 24) {
            graphSection(
                title: "Orientation (rad)",
                airpodsData: orientationData(from: session.airpodsDatapoints, source: .airpods),
                phoneData: orientationData(from: session.phoneDatapoints, source: .phone)
            )
            graphSection(
                title: "Rotation Rate (rad/s)",
                airpodsData: rotationData(from: session.airpodsDatapoints, source: .airpods),
                phoneData: rotationData(from: session.phoneDatapoints, source: .phone)
            )
            graphSection(
                title: "Acceleration (m/s^2)",
                airpodsData: accelerationData(from: session.airpodsDatapoints, source: .airpods),
                phoneData: accelerationData(from: session.phoneDatapoints, source: .phone)
            )
        }
        .padding()
        .background(Color.white)
    }
    
    private func graphSection(
        title: String,
        airpodsData: [GraphDatapoint],
        phoneData: [GraphDatapoint]
    ) -> some View {
        let combinedData = airpodsData + phoneData
        
        return VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.headline)

            Chart(combinedData) { datapoint in
                LineMark(
                    x: .value("Time", datapoint.time),
                    y: .value("Value", datapoint.value)
                )
                .foregroundStyle(by: .value("Axis", datapoint.label))
                .lineStyle(by: .value("Source", datapoint.source.rawValue))
            }
            .chartXAxis {
                AxisMarks(values: .stride(by: 0.5))
            }
            .chartYAxis {
                AxisMarks(
                    position: .leading,
                    values: .automatic(desiredCount: 8)
                )
            }
            .chartXAxisLabel("Time (s)")
            .chartYAxisLabel(title)
            .frame(height: 220)
        }
    }

    private func orientationData(from datapoints: [MotionDatapoint], source: MotionSource) -> [GraphDatapoint] {
        datapoints.flatMap { datapoint in
            let t = datapoint.sessionTime(since: session.startDate)
            return [
                GraphDatapoint(time: t, value: datapoint.pitch, label: "Pitch", source: source),
                GraphDatapoint(time: t, value: datapoint.roll, label: "Roll", source: source),
                GraphDatapoint(time: t, value: datapoint.yaw, label: "Yaw", source: source)
            ]
        }
    }

    private func rotationData(from datapoints: [MotionDatapoint], source: MotionSource) -> [GraphDatapoint] {
        datapoints.flatMap { datapoint in
            let t = datapoint.sessionTime(since: session.startDate)
            return [
                GraphDatapoint(time: t, value: datapoint.rotationRateX, label: "X", source: source),
                GraphDatapoint(time: t, value: datapoint.rotationRateY, label: "Y", source: source),
                GraphDatapoint(time: t, value: datapoint.rotationRateZ, label: "Z", source: source)
            ]
        }
    }

    private func accelerationData(from datapoints: [MotionDatapoint], source: MotionSource) -> [GraphDatapoint] {
        datapoints.flatMap { datapoint in
            let t = datapoint.sessionTime(since: session.startDate)
            return [
                GraphDatapoint(time: t, value: datapoint.accelerationX, label: "X", source: source),
                GraphDatapoint(time: t, value: datapoint.accelerationY, label: "Y", source: source),
                GraphDatapoint(time: t, value: datapoint.accelerationZ, label: "Z", source: source)
            ]
        }
    }
}

extension MotionDatapoint {
    func sessionTime(since sessionStart: Date) -> TimeInterval {
        timestamp.timeIntervalSince(sessionStart)
    }
}
