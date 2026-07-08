from pydantic import BaseModel

class SilenceRegion(BaseModel):
    start: float
    end: float

    @property
    def duration(self) -> float:
        return self.end - self.start
