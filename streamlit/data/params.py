from dataclasses import asdict, dataclass, field, fields
import json

AXIS_OPTIONS = {
    # Axis label: (Axis index, multiplier)
    "+X": (0, 1),
    "+Y": (1, 1),
    "+Z": (2, 1),
    "-X": (0, -1),
    "-Y": (1, -1),
    "-Z": (2, -1),
}


@dataclass
class FilterParams:
    cutoff: float | None = field(
        default=None,
        metadata={
            "label": "Cutoff",
        },
    )
    order: int | None = field(
        default=None,
        metadata={
            "label": "Order",
        },
    )
    active: bool = True


@dataclass
class OptiFilters:
    lowpass: FilterParams = field(
        default_factory=lambda: FilterParams(cutoff=10.0, order=4),
        metadata={"label": "Low-pass filter"},
    )

    @classmethod
    def field_labels(cls):
        return {f.name: f.metadata["label"] for f in fields(cls)}

    @classmethod
    def label_fields(cls):
        return {f.metadata["label"]: f.name for f in fields(cls)}

    def active_labels(self):
        return [
            f.metadata["label"] for f in fields(self) if getattr(self, f.name).active
        ]


@dataclass
class IMUFilters:
    detrend_a: FilterParams = field(
        default_factory=FilterParams,
        metadata={"label": "Detrend (acc.)"},
    )
    lowpass: FilterParams = field(
        default_factory=lambda: FilterParams(cutoff=10.0, order=4),
        metadata={"label": "Low-pass filter"},
    )
    highpass: FilterParams = field(
        default_factory=lambda: FilterParams(cutoff=0.1, order=4),
        metadata={"label": "High-pass filter"},
    )
    detrend_v: FilterParams = field(
        default_factory=FilterParams,
        metadata={"label": "Detrend (vel.)"},
    )

    @classmethod
    def field_labels(cls):
        return {f.name: f.metadata["label"] for f in fields(cls)}

    @classmethod
    def label_fields(cls):
        return {f.metadata["label"]: f.name for f in fields(cls)}

    def active_labels(self):
        return [
            f.metadata["label"] for f in fields(self) if getattr(self, f.name).active
        ]


@dataclass
class Params:
    opti: OptiFilters = field(default_factory=OptiFilters)
    imu: IMUFilters = field(default_factory=IMUFilters)
    trim: float = 1.5
    axes: list = field(default_factory=lambda: list(AXIS_OPTIONS)[:3])

    def to_json(self):
        return json.dumps(asdict(self))

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_json(cls, value: str):
        data = json.loads(value)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict):
        try:
            return cls(
                opti=OptiFilters(lowpass=FilterParams(**data["opti"]["lowpass"])),
                imu=IMUFilters(
                    detrend_a=FilterParams(**data["imu"]["detrend_a"]),
                    lowpass=FilterParams(**data["imu"]["lowpass"]),
                    highpass=FilterParams(**data["imu"]["highpass"]),
                    detrend_v=FilterParams(**data["imu"]["detrend_v"]),
                ),
                trim=data["trim"],
                axes=data["axes"],
            )
        except KeyError:
            return Params()
