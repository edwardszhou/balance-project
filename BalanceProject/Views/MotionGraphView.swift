//
//  MotionGraphView.swift
//  BalanceProject
//

import SwiftUI

struct MotionGraphView: View {

    let session: MotionSession

    var body: some View {
        VStack(spacing: 24) {
            graphSection(
                title: "Orientation",
                legend: [
                    ("Pitch", .red),
                    ("Roll", .green),
                    ("Yaw", .blue)
                ],
                series: [
                    session.datapoints.map { $0.pitch },
                    session.datapoints.map { $0.roll },
                    session.datapoints.map { $0.yaw }
                ],
                colors: [.red, .green, .blue]
            )

            graphSection(
                title: "Rotation Rate",
                legend: [
                    ("X", .red),
                    ("Y", .green),
                    ("Z", .blue)
                ],
                series: [
                    session.datapoints.map { $0.rotationRateX },
                    session.datapoints.map { $0.rotationRateY },
                    session.datapoints.map { $0.rotationRateZ }
                ],
                colors: [.red, .green, .blue]
            )

            graphSection(
                title: "Acceleration",
                legend: [
                    ("X", .red),
                    ("Y", .green),
                    ("Z", .blue)
                ],
                series: [
                    session.datapoints.map { $0.accelerationX },
                    session.datapoints.map { $0.accelerationY },
                    session.datapoints.map { $0.accelerationZ }
                ],
                colors: [.red, .green, .blue]
            )
        }
        .padding()
        .background(Color.white)
    }


    private func graphSection(
        title: String,
        legend: [(String, Color)],
        series: [[Double]],
        colors: [Color]
    ) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.headline)

            HStack(spacing: 16) {
                ForEach(legend, id: \.0) { label, color in
                    HStack(spacing: 6) {
                        Rectangle()
                            .fill(color)
                            .frame(width: 12, height: 12)

                        Text(label)
                            .font(.caption)
                    }
                }
            }

            GeometryReader { geo in
                ZStack {
                    ForEach(series.indices, id: \.self) { index in
                        Path { path in
                            plot(
                                values: series[index],
                                in: geo.size,
                                path: &path
                            )
                        }
                        .stroke(colors[index], lineWidth: 2)
                    }
                }
            }
            .frame(height: 200)
        }
    }


    private func plot(
        values: [Double],
        in size: CGSize,
        path: inout Path
    ) {
        guard values.count > 1 else { return }

        let minVal = values.min() ?? 0
        let maxVal = values.max() ?? 1
        let range = max(maxVal - minVal, 0.0001)

        for (index, value) in values.enumerated() {
            let x = size.width * CGFloat(index) / CGFloat(values.count - 1)
            let y = size.height * (1 - CGFloat((value - minVal) / range))

            index == 0
                ? path.move(to: CGPoint(x: x, y: y))
                : path.addLine(to: CGPoint(x: x, y: y))
        }
    }
}
