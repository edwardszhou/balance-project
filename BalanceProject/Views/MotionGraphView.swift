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
                data: orientationData
            )
            graphSection(
                title: "Rotation Rate (rad/s)",
                data: rotationData
            )
            graphSection(
                title: "Acceleration (m/s^2)",
                data: accelerationData
            )
        }
        .padding()
        .background(Color.white)
    }
    
    private func graphSection(
        title: String,
        data: [GraphDatapoint]
    ) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.headline)

            Chart(data) {
                LineMark(
                    x: .value("Time", $0.time),
                    y: .value("Value", $0.value)
                )
                .foregroundStyle(by: .value("Axis", $0.label))
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

    private var orientationData: [GraphDatapoint] {
        session.datapoints.flatMap { datapoint in
            let t = datapoint.sessionTime(since: session.startDate)
            return [
                GraphDatapoint(time: t, value: datapoint.pitch, label: "Pitch"),
                GraphDatapoint(time: t, value: datapoint.roll, label: "Roll"),
                GraphDatapoint(time: t, value: datapoint.yaw, label: "Yaw")
            ]
        }
    }

    private var rotationData: [GraphDatapoint] {
        session.datapoints.flatMap { datapoint in
            let t = datapoint.sessionTime(since: session.startDate)
            return [
                GraphDatapoint(time: t, value: datapoint.rotationRateX, label: "X"),
                GraphDatapoint(time: t, value: datapoint.rotationRateY, label: "Y"),
                GraphDatapoint(time: t, value: datapoint.rotationRateZ, label: "Z")
            ]
        }
    }

    private var accelerationData: [GraphDatapoint] {
        session.datapoints.flatMap { datapoint in
            let t = datapoint.sessionTime(since: session.startDate)
            return [
                GraphDatapoint(time: t, value: datapoint.accelerationX, label: "X"),
                GraphDatapoint(time: t, value: datapoint.accelerationY, label: "Y"),
                GraphDatapoint(time: t, value: datapoint.accelerationZ, label: "Z")
            ]
        }
    }
}

extension MotionDatapoint {
    func sessionTime(since sessionStart: Date) -> TimeInterval {
        timestamp.timeIntervalSince(sessionStart)
    }
}
