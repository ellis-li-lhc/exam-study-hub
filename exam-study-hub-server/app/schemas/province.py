from pydantic import BaseModel, ConfigDict


class ProvinceRead(BaseModel):
    id: int
    code: str       # 如 "henan"
    name: str       # 如 "河南"
    note: str | None = None
    model_config = ConfigDict(from_attributes=True)
