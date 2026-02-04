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
                airpodsData: orientationData(from: session.airpodsDatapoints),
                phoneData: orientationData(from: session.phoneDatapoints)
            )
            graphSection(
                title: "Rotation Rate (rad/s)",
                airpodsData: rotationData(from: session.airpodsDatapoints),
                phoneData: rotationData(from: session.phoneDatapoints)
            )
            graphSection(
                title: "Acceleration (m/s^2)",
                airpodsData: accelerationData(from: session.airpodsDatapoints),
                phoneData: accelerationData(from: session.phoneDatapoints)
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
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.headline)

            Chart {
                ForEach(airpodsData) { datapoint in
                    LineMark(
                        x: .value("Time", datapoint.time),
                        y: .value("Value", datapoint.value)
                    )
                    .foregroundStyle(by: .value("Axis", datapoint.label))
                    .lineStyle(by: .value("Source", MotionSource.airpods.rawValue.capitalized))
                }
                ForEach(phoneData) { datapoint in
                    LineMark(
                        x: .value("Time", datapoint.time),
                        y: .value("Value", datapoint.value)
                    )
                    .foregroundStyle(by: .value("Axis", datapoint.label))
                    .lineStyle(by: .value("Source", MotionSource.phone.rawValue.capitalized))
                }
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

    private func orientationData(from datapoints: [MotionDatapoint]) -> [GraphDatapoint] {
        datapoints.flatMap { datapoint in
            let t = datapoint.sessionTime(since: session.startDate)
            return [
                GraphDatapoint(time: t, value: datapoint.pitch, label: "Pitch"),
                GraphDatapoint(time: t, value: datapoint.roll, label: "Roll"),
                GraphDatapoint(time: t, value: datapoint.yaw, label: "Yaw")
            ]
        }
    }

    private func rotationData(from datapoints: [MotionDatapoint]) -> [GraphDatapoint] {
        datapoints.flatMap { datapoint in
            let t = datapoint.sessionTime(since: session.startDate)
            return [
                GraphDatapoint(time: t, value: datapoint.rotationRateX, label: "X"),
                GraphDatapoint(time: t, value: datapoint.rotationRateY, label: "Y"),
                GraphDatapoint(time: t, value: datapoint.rotationRateZ, label: "Z")
            ]
        }
    }

    private func accelerationData(from datapoints: [MotionDatapoint]) -> [GraphDatapoint] {
        datapoints.flatMap { datapoint in
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
        timing.timestamp.timeIntervalSince(sessionStart)
    }
}
