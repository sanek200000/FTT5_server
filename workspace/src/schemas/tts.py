from pydantic import BaseModel


class TTSRequstDTO(BaseModel):
    ref_text: str
    gen_text: str
