from typing import Annotated

from pydantic import BaseModel, ConfigDict, FiniteFloat, StringConstraints

class ProposeRule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    threshold: FiniteFloat


class EvaluateRule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cards: list[Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]]


class PublishRule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evaluation: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
