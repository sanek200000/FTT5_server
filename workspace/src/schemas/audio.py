from pydantic import BaseModel
from statistics import median, mean


class PauseStatisticDTO(BaseModel):
    minimum: float = 0.0
    maximum: float = 0.0

    median: float = 0.0
    average: float = 0.0

    p25: float = 0.0
    p75: float = 0.0


class PauseScaleDTO(BaseModel):
    scale: float = 1.0

    reference: PauseStatisticDTO
    generated: PauseStatisticDTO

    k25: float = 1.0
    k50: float = 1.0
    k75: float = 1.0


class SilenceRegionDTO(BaseModel):
    start: float
    end: float

    @property
    def duration(self) -> float:
        return self.end - self.start

    def format_log(self):
        return f"start: {self.start:.3f}\tend: {self.end:.3f}"


class ListRegionsDTO(BaseModel):
    regions: list[SilenceRegionDTO] = list()

    @property
    def length(self) -> int:
        return len(self.regions)

    @property
    def statistics(self) -> PauseStatisticDTO:
        pauses = [region.duration for region in self.regions]

        if not pauses:
            return PauseStatisticDTO()

        pauses.sort()

        def percentile(values: list[float], p: float) -> float:
            if len(values) == 1:
                return values[0]

            index = (len(values) - 1) * p
            lower = int(index)
            upper = min(lower + 1, len(values) - 1)

            if lower == upper:
                return values[lower]

            fraction = index - lower

            return values[lower] + (values[upper] - values[lower]) * fraction

        return PauseStatisticDTO(
            minimum=pauses[0],
            maximum=pauses[-1],
            average=mean(pauses),
            median=median(pauses),
            p25=percentile(pauses, 0.25),
            p75=percentile(pauses, 0.75),
        )

    def format_log(self):
        result = list()
        stats = self.statistics

        for i, region in enumerate(self.regions, start=1):
            result.append(
                f"{i:02d}. Silence: " f"{region.start:.3f}s -> " f"{region.end:.3f}s " f"({region.duration:.3f}s)\n"
            )
        return (
            "\n"
            "========================================================\n"
            "Regions\n"
            "--------------------------------------------------------\n"
            f'{"".join(result)}'
            "--------------------------------------------------------\n"
            "Statistics\n"
            "--------------------------------------------------------\n"
            f"min     : {stats.minimum:.3f}\n"
            f"p25     : {stats.p25:.3f}\n"
            f"median  : {stats.median:.3f}\n"
            f"mean    : {stats.average:.3f}\n"
            f"p75     : {stats.p75:.3f}\n"
            f"max     : {stats.maximum:.3f}\n"
            "========================================================"
            "\n"
        )


class PauseEditDTO(BaseModel):
    original: SilenceRegionDTO
    target_duration: float

    def format_log(self):
        return f"{self.original.format_log()}\target_duration: {self.target_duration:.3f}"


class PauseEditPlanDTO(BaseModel):
    scale: float = 1.0
    edits: list[PauseEditDTO] = list()

    @property
    def length(self) -> int:
        return len(self.edits)

    def format_log(self):
        edits_log = "\n".join(f"{i:02d}. {edit.format_log()}" for i, edit in enumerate(self.edits, start=1))
        return (
            "\n"
            "========================================================\n"
            "Pause edit plan\n"
            "--------------------------------------------------------\n"
            f"scale     : {self.scale:.3f}\n"
            f"edits:\n"
            f"{edits_log}"
            "\n"
            "========================================================"
            "\n"
        )
