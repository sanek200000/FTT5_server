from pydantic import BaseModel


class SilenceRegionDTO(BaseModel):
    start: float
    end: float

    @property
    def duration(self) -> float:
        return self.end - self.start


class ListRegionsDTO(BaseModel):
    regions: list[SilenceRegionDTO] = list()

    @property
    def length(self) -> int:
        return len(self.regions)

    def format_log(self):
        result = list()

        for region in self.regions:
            result.append(f"Silence: " f"{region.start:.3f}s -> " f"{region.end:.3f}s " f"({region.duration:.3f}s)\n")
        return (
            "\n"
            "========================================================\n"
            "Regions\n"
            "--------------------------------------------------------\n"
            f'{"".join(result)}'
            "========================================================"
            "\n"
        )
