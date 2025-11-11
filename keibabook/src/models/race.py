from dataclasses import dataclass, asdict
from typing import List, Dict, Any

@dataclass
class Horse:
    number: int
    name: str
    sex_age: str
    weight: str
    jockey: str
    trainer: str
    stable: str
    blood: Dict[str, Any]

@dataclass
class Race:
    race_id: str
    venue: str
    date: str
    horses: List[Horse]
    results: Dict[str, Any]
    payouts: Dict[str, Any]

    def to_dict(self):
        return asdict(self)
