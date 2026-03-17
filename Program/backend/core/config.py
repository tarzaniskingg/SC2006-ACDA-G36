import os
from dataclasses import dataclass


@dataclass
class Settings:
    google_maps_key: str = os.getenv("GOOGLE_MAPS_KEY", "")
    lta_account_key: str = os.getenv("LTA_ACCOUNT_KEY", "")
    # TTLs (seconds)
    ttl_bus_arrival: int = int(os.getenv("TTL_BUS_ARRIVAL", "30"))
    ttl_pcd: int = int(os.getenv("TTL_PCD", "600"))
    ttl_est_travel: int = int(os.getenv("TTL_EST_TRAVEL", "300"))
    ttl_speed_bands: int = int(os.getenv("TTL_SPEED_BANDS", "300"))
    ttl_taxi: int = int(os.getenv("TTL_TAXI", "60"))
    ttl_carpark: int = int(os.getenv("TTL_CARPARK", "300"))


def get_settings() -> Settings:
    return Settings()

