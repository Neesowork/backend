from pydantic import BaseModel, conlist
from typing import Annotated, Literal, Annotated
from annotated_types import Len

class Vacancy(BaseModel):
    id: str

    name: str | None
    area: str | None
    type: str | None
    employer: str | None
    responsibility: str | None
    schedule: str | None
    experience: str | None
    employment: str | None
    requirement: str | None
    currency: str | None

    average_salary: int | None

class Resume(BaseModel):
    id: str

    gender: str | None
    birthday: str | None
    search_status: str | None
    address: str | None
    position: str | None
    about: str | None
    currency: str | None
    preferred_commute_time: str | None
    moving_status: str | None
    citizenship: str | None

    specializations: list[str] | None
    languages: list[str] | None
    schedule: list[str] | None
    skills: list[str] | None
    employment: list[str] | None

    education: list[Annotated[list[str], Len(min_length=2, max_length=2)]] | None

    age: int | None
    salary: int | None
