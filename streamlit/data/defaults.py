from dataclasses import asdict, dataclass, field
import json

AXIS_OPTIONS = {
    "+X": (0, 1),
    "+Y": (1, 1),
    "+Z": (2, 1),
    "-X": (0, -1),
    "-Y": (1, -1),
    "-Z": (2, -1),
}


@dataclass
class OptiParams:
    lp_cutoff: float | None = 10.0
    lp_order: int = 4


@dataclass
class IMUParams:
    detrend_a: bool | None = True
    lp_cutoff: float | None = 10.0
    lp_order: int | None = 4
    hp_cutoff: float | None = 0.1
    hp_order: int | None = 4
    detrend_v: bool | None = True


@dataclass
class Params:
    opti: OptiParams = field(default_factory=OptiParams)
    imu: IMUParams | None = field(default_factory=IMUParams)
    trim: float = 1.5
    axes: list = field(default_factory=lambda: list(AXIS_OPTIONS)[:3])

    def to_json(self):
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, value: str):
        data = json.loads(value)
        return cls(
            opti=OptiParams(**data["opti"]),
            imu=IMUParams(**data["imu"]),
            trim=data["trim"],
            axes=data["axes"],
        )


DEFAULT_PARAMS = Params()
