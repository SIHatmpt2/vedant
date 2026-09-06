"""Terrain intelligence abstraction; raster providers can replace metadata values later."""
from typing import Any


class TerrainService:
    """Normalize elevation, slope, drainage density and flow accumulation to risk signals."""
    def __init__(self, provider: Any = None) -> None:
        self.provider = provider

    def elevation(self, latitude: float, longitude: float, metadata: dict[str, Any] | None = None) -> float | None:
        """Return elevation metres from a configured provider or normalized zone metadata."""
        if self.provider:
            return self.provider.elevation(latitude, longitude)
        value = (metadata or {}).get("elevation")
        return float(value) if value is not None else None

    def slope(self, latitude: float, longitude: float, metadata: dict[str, Any] | None = None) -> float | None:
        """Return slope in degrees from a provider or metadata."""
        if self.provider:
            return self.provider.slope(latitude, longitude)
        value = (metadata or {}).get("slope")
        return float(value) if value is not None else None

    def drainage(self, latitude: float, longitude: float, metadata: dict[str, Any] | None = None) -> float | None:
        """Return normalized drainage density/flow-accumulation susceptibility (0--100)."""
        if self.provider:
            value = self.provider.drainage(latitude, longitude)
        else:
            source = metadata or {}
            value = source.get("drainage_density", source.get("flow_accumulation"))
        return max(0.0, min(100.0, float(value))) if value is not None else None

    def score(self, latitude: float, longitude: float, metadata: dict[str, Any] | None = None) -> dict[str, float | None]:
        """Combine low-elevation, low-slope and drainage risks without raster assumptions."""
        elevation, slope, drainage = self.elevation(latitude, longitude, metadata), self.slope(latitude, longitude, metadata), self.drainage(latitude, longitude, metadata)
        parts = []
        if elevation is not None:
            parts.append(max(0.0, min(100.0, 100 - elevation / 20)))
        if slope is not None:
            parts.append(max(0.0, min(100.0, 100 - slope * 4)))
        if drainage is not None:
            parts.append(drainage)
        return {"terrain_score": round(sum(parts) / len(parts), 2) if parts else None, "elevation": elevation, "slope": slope, "drainage": drainage}
