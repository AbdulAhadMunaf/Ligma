from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserReportData:
    id: int
    name: str
    email: str
    phone_number: str
    language: str
    positions: str
    last_login: datetime
    is_active: bool
    role_id: int
    date_joined: datetime
    role_name: str

    def __post_init__(self):
        # Convert the positions list to a comma-separated string
        self.positions = ",".join(self.positions) if self.positions else ""
