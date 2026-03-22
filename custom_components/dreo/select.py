"""Support Select entities for some Dreo devices."""
# Suppress warnings about DataClass constructors
# pylint: disable=E1123

# Suppress warnings about unused function arguments
# pylint: disable=W0613

from __future__ import annotations

from dataclasses import dataclass
import logging

from .haimports import *  # pylint: disable=W0401,W0614
from .dreobasedevice import DreoBaseDeviceHA
from .pydreo import PyDreo
from .pydreo.pydreobasedevice import PyDreoBaseDevice
from .pydreo.constant import DreoDeviceType

from .const import DOMAIN, PYDREO_MANAGER

_LOGGER = logging.getLogger(__name__)


@dataclass
class DreoSelectEntityDescription(SelectEntityDescription):
    """Describe Dreo Select entity."""

    attr_name: str | None = None


# Humidifier mist level exposed as a friendly 3-option select.
# Internally, the PyDreo humidifier maps this to the device's foglevel.
MIST_LEVEL_OPTIONS = ["Bassa", "Media", "Alta"]

# Humidifier ambient light level (rgblevel) exposed as 4-option select.
AMBIENT_LIGHT_LEVEL_OPTIONS = ["Spento", "Bassa", "Media", "Alta"]

SELECTS: tuple[DreoSelectEntityDescription, ...] = (
    DreoSelectEntityDescription(
        key="Mist Level",
        translation_key="mist_level",
        attr_name="mist_level",
        icon="mdi:weather-windy",
    ),
    DreoSelectEntityDescription(
        key="Ambient Light Level",
        translation_key="ambient_light_level",
        attr_name="ambient_light_level",
        icon="mdi:led-strip-variant",
    ),
)


def get_entries(pydreo_devices: list[PyDreoBaseDevice]) -> list["DreoSelectHA"]:
    """Create Select entities for supported devices."""
    entities: list[DreoSelectHA] = []

    for device in pydreo_devices:
        for sel in SELECTS:
            # Only humidifiers, and only if the feature is supported.
            if device.type != DreoDeviceType.HUMIDIFIER:
                continue
            if not device.is_feature_supported(sel.attr_name):
                continue

            entities.append(DreoSelectHA(device, sel))

    return entities


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dreo Select platform."""
    _LOGGER.info("Starting Dreo Select Platform")

    pydreo_manager: PyDreo = hass.data[DOMAIN][PYDREO_MANAGER]
    async_add_entities(get_entries(pydreo_manager.devices))


class DreoSelectHA(DreoBaseDeviceHA, SelectEntity):
    """Representation of a Select describing a read-write property of a Dreo device."""

    def __init__(self, device: PyDreoBaseDevice, description: DreoSelectEntityDescription) -> None:
        super().__init__(device)
        self.device = device
        self.entity_description = description

        self._attr_name = super().name + " " + description.key
        self._attr_unique_id = f"{super().unique_id}-{description.key}"

        # Options depend on which select we are exposing
        if description.attr_name == "mist_level":
            self._attr_options = MIST_LEVEL_OPTIONS
        elif description.attr_name == "ambient_light_level":
            self._attr_options = AMBIENT_LIGHT_LEVEL_OPTIONS
        else:
            self._attr_options = []

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        attr = self.entity_description.attr_name

        if attr == "mist_level":
            try:
                level = int(getattr(self.device, attr))
            except (TypeError, ValueError):
                return None
            if 1 <= level <= 3:
                return MIST_LEVEL_OPTIONS[level - 1]
            return None

        if attr == "ambient_light_level":
            lvl = getattr(self.device, attr)
            if not isinstance(lvl, str):
                return None
            lvl_norm = lvl.strip().lower()
            map_to_it = {"off": "Spento", "spento": "Spento", "low": "Bassa", "bassa": "Bassa", "medium": "Media", "media": "Media", "high": "Alta", "alta": "Alta"}
            opt = map_to_it.get(lvl_norm)
            return opt if opt in AMBIENT_LIGHT_LEVEL_OPTIONS else None

        return None

    def select_option(self, option: str) -> None:
        """Set a new option."""
        attr = self.entity_description.attr_name

        if attr == "mist_level":
            if option not in MIST_LEVEL_OPTIONS:
                return
            level = MIST_LEVEL_OPTIONS.index(option) + 1
            setattr(self.device, attr, level)
            return

        if attr == "ambient_light_level":
            if option not in AMBIENT_LIGHT_LEVEL_OPTIONS:
                return
            setattr(self.device, attr, option)
            return

