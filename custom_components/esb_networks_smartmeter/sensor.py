"""Support for ESB Smart Meter sensors."""

import logging
from abc import abstractmethod
from datetime import datetime, timedelta, timezone

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import ESBDataUpdateCoordinator
from .models import ESBData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the ESB Smart Meter sensor based on a config entry."""
    # Get coordinator from hass.data
    coordinator: ESBDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    mprn = coordinator.mprn

    # Create all sensors using the coordinator
    sensors = [
        TodaySensor(coordinator=coordinator, mprn=mprn),
        Last24HoursSensor(coordinator=coordinator, mprn=mprn),
        ThisWeekSensor(coordinator=coordinator, mprn=mprn),
        Last7DaysSensor(coordinator=coordinator, mprn=mprn),
        ThisMonthSensor(coordinator=coordinator, mprn=mprn),
        Last30DaysSensor(coordinator=coordinator, mprn=mprn),
        # Current interval sensors (most recent 30-min reading)
        CurrentImportSensor(coordinator=coordinator, mprn=mprn),
        CurrentExportSensor(coordinator=coordinator, mprn=mprn),
        # Grid export sensors (for microgen/solar accounts)
        ExportedTodaySensor(coordinator=coordinator, mprn=mprn),
        ExportedLast24HoursSensor(coordinator=coordinator, mprn=mprn),
        ExportedThisWeekSensor(coordinator=coordinator, mprn=mprn),
        ExportedLast7DaysSensor(coordinator=coordinator, mprn=mprn),
        ExportedThisMonthSensor(coordinator=coordinator, mprn=mprn),
        ExportedLast30DaysSensor(coordinator=coordinator, mprn=mprn),
        # Diagnostic sensors
        LastUpdateSensor(coordinator=coordinator, mprn=mprn),
        LatestReadingTimeSensor(coordinator=coordinator, mprn=mprn),
        ApiStatusSensor(coordinator=coordinator, mprn=mprn),
        DataAgeSensor(coordinator=coordinator, mprn=mprn),
        CircuitBreakerStatusSensor(coordinator=coordinator, mprn=mprn),
    ]

    # Add entities - coordinator handles updates
    async_add_entities(sensors)


class BaseSensor(CoordinatorEntity[ESBDataUpdateCoordinator], SensorEntity):
    """Base sensor class for ESB Smart Meter sensors using coordinator."""

    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY
    # Use TOTAL (not TOTAL_INCREASING) since values are recalculated from ESB CSV
    # which may have varying historical data availability
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:flash"

    def __init__(
        self,
        *,
        coordinator: ESBDataUpdateCoordinator,
        mprn: str,
        name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._mprn = mprn
        self._attr_name = name

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._mprn)},
            name=f"ESB Smart Meter ({self._mprn})",
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    @abstractmethod
    def _get_data(self, *, esb_data: ESBData) -> float:
        """Get the data for this sensor from coordinator data."""

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self._get_data(esb_data=self.coordinator.data)


class TodaySensor(BaseSensor):
    """Sensor for today's electricity usage."""

    def __init__(self, *, coordinator: ESBDataUpdateCoordinator, mprn: str) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator=coordinator,
            mprn=mprn,
            name="ESB Electricity Usage: Today",
        )
        self._attr_unique_id = f"{mprn}_today"

    def _get_data(self, *, esb_data: ESBData) -> float:
        """Get today's data."""
        return esb_data.today


class Last24HoursSensor(BaseSensor):
    """Sensor for last 24 hours electricity usage."""

    def __init__(self, *, coordinator: ESBDataUpdateCoordinator, mprn: str) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator=coordinator,
            mprn=mprn,
            name="ESB Electricity Usage: Last 24 Hours",
        )
        self._attr_unique_id = f"{mprn}_last_24_hours"

    def _get_data(self, *, esb_data: ESBData) -> float:
        """Get last 24 hours data."""
        return esb_data.last_24_hours


class ThisWeekSensor(BaseSensor):
    """Sensor for this week's electricity usage."""

    def __init__(self, *, coordinator: ESBDataUpdateCoordinator, mprn: str) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator=coordinator,
            mprn=mprn,
            name="ESB Electricity Usage: This Week",
        )
        self._attr_unique_id = f"{mprn}_this_week"

    def _get_data(self, *, esb_data: ESBData) -> float:
        """Get this week's data."""
        return esb_data.this_week


class Last7DaysSensor(BaseSensor):
    """Sensor for last 7 days electricity usage."""

    def __init__(self, *, coordinator: ESBDataUpdateCoordinator, mprn: str) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator=coordinator,
            mprn=mprn,
            name="ESB Electricity Usage: Last 7 Days",
        )
        self._attr_unique_id = f"{mprn}_last_7_days"

    def _get_data(self, *, esb_data: ESBData) -> float:
        """Get last 7 days data."""
        return esb_data.last_7_days


class ThisMonthSensor(BaseSensor):
    """Sensor for this month's electricity usage."""

    def __init__(self, *, coordinator: ESBDataUpdateCoordinator, mprn: str) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator=coordinator,
            mprn=mprn,
            name="ESB Electricity Usage: This Month",
        )
        self._attr_unique_id = f"{mprn}_this_month"

    def _get_data(self, *, esb_data: ESBData) -> float:
        """Get this month's data."""
        return esb_data.this_month


class Last30DaysSensor(BaseSensor):
    """Sensor for last 30 days electricity usage."""

    def __init__(self, *, coordinator: ESBDataUpdateCoordinator, mprn: str) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator=coordinator,
            mprn=mprn,
            name="ESB Electricity Usage: Last 30 Days",
        )
        self._attr_unique_id = f"{mprn}_last_30_days"

    def _get_data(self, *, esb_data: ESBData) -> float:
        """Get last 30 days data."""
        return esb_data.last_30_days


class CurrentImportSensor(BaseSensor):
    """Most recent 30-minute import interval reading (kWh)."""

    _attr_icon = "mdi:lightning-bolt"

    def __init__(self, *, coordinator: ESBDataUpdateCoordinator, mprn: str) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator=coordinator,
            mprn=mprn,
            name="ESB Electricity Usage: Now",
        )
        self._attr_unique_id = f"{mprn}_usage_now"

    def _get_data(self, *, esb_data: ESBData) -> float | None:
        """Get the most recent import interval value."""
        return esb_data.current_import

    @property
    def last_reset(self) -> datetime | None:
        """Return the start of the current 30-minute interval."""
        if self.coordinator.data is None:
            return None
        ts = self.coordinator.data.current_import_time
        if ts is None:
            return None
        interval_start = ts - timedelta(minutes=30)
        return interval_start.replace(tzinfo=timezone.utc) if interval_start.tzinfo is None else interval_start


class CurrentExportSensor(BaseSensor):
    """Most recent 30-minute export interval reading (kWh)."""

    _attr_icon = "mdi:transmission-tower-export"

    def __init__(self, *, coordinator: ESBDataUpdateCoordinator, mprn: str) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator=coordinator,
            mprn=mprn,
            name="ESB Electricity Export: Now",
        )
        self._attr_unique_id = f"{mprn}_export_now"

    def _get_data(self, *, esb_data: ESBData) -> float | None:
        """Get the most recent export interval value."""
        return esb_data.current_export

    @property
    def last_reset(self) -> datetime | None:
        """Return the start of the current 30-minute interval."""
        if self.coordinator.data is None:
            return None
        ts = self.coordinator.data.current_export_time
        if ts is None:
            return None
        interval_start = ts - timedelta(minutes=30)
        return interval_start.replace(tzinfo=timezone.utc) if interval_start.tzinfo is None else interval_start


class BaseExportedSensor(BaseSensor):
    """Base sensor for grid export readings."""

    _attr_icon = "mdi:transmission-tower-export"


class ExportedTodaySensor(BaseExportedSensor):
    """Sensor for today's electricity exported to the grid."""

    def __init__(self, *, coordinator: ESBDataUpdateCoordinator, mprn: str) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator=coordinator,
            mprn=mprn,
            name="ESB Electricity Exported: Today",
        )
        self._attr_unique_id = f"{mprn}_exported_today"

    def _get_data(self, *, esb_data: ESBData) -> float:
        """Get today's exported data."""
        return esb_data.exported_today


class ExportedLast24HoursSensor(BaseExportedSensor):
    """Sensor for last 24 hours electricity exported to the grid."""

    def __init__(self, *, coordinator: ESBDataUpdateCoordinator, mprn: str) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator=coordinator,
            mprn=mprn,
            name="ESB Electricity Exported: Last 24 Hours",
        )
        self._attr_unique_id = f"{mprn}_exported_last_24_hours"

    def _get_data(self, *, esb_data: ESBData) -> float:
        """Get last 24 hours exported data."""
        return esb_data.exported_last_24_hours


class ExportedThisWeekSensor(BaseExportedSensor):
    """Sensor for this week's electricity exported to the grid."""

    def __init__(self, *, coordinator: ESBDataUpdateCoordinator, mprn: str) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator=coordinator,
            mprn=mprn,
            name="ESB Electricity Exported: This Week",
        )
        self._attr_unique_id = f"{mprn}_exported_this_week"

    def _get_data(self, *, esb_data: ESBData) -> float:
        """Get this week's exported data."""
        return esb_data.exported_this_week


class ExportedLast7DaysSensor(BaseExportedSensor):
    """Sensor for last 7 days electricity exported to the grid."""

    def __init__(self, *, coordinator: ESBDataUpdateCoordinator, mprn: str) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator=coordinator,
            mprn=mprn,
            name="ESB Electricity Exported: Last 7 Days",
        )
        self._attr_unique_id = f"{mprn}_exported_last_7_days"

    def _get_data(self, *, esb_data: ESBData) -> float:
        """Get last 7 days exported data."""
        return esb_data.exported_last_7_days


class ExportedThisMonthSensor(BaseExportedSensor):
    """Sensor for this month's electricity exported to the grid."""

    def __init__(self, *, coordinator: ESBDataUpdateCoordinator, mprn: str) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator=coordinator,
            mprn=mprn,
            name="ESB Electricity Exported: This Month",
        )
        self._attr_unique_id = f"{mprn}_exported_this_month"

    def _get_data(self, *, esb_data: ESBData) -> float:
        """Get this month's exported data."""
        return esb_data.exported_this_month


class ExportedLast30DaysSensor(BaseExportedSensor):
    """Sensor for last 30 days electricity exported to the grid."""

    def __init__(self, *, coordinator: ESBDataUpdateCoordinator, mprn: str) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator=coordinator,
            mprn=mprn,
            name="ESB Electricity Exported: Last 30 Days",
        )
        self._attr_unique_id = f"{mprn}_exported_last_30_days"

    def _get_data(self, *, esb_data: ESBData) -> float:
        """Get last 30 days exported data."""
        return esb_data.exported_last_30_days


class LastUpdateSensor(SensorEntity):
    """Sensor for last update timestamp."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_state_class = None  # Timestamps don't use state class
    _attr_native_unit_of_measurement = None
    _attr_icon = "mdi:clock-outline"

    def __init__(self, *, coordinator: ESBDataUpdateCoordinator, mprn: str) -> None:
        """Initialize the sensor."""
        super().__init__()
        self.coordinator = coordinator
        self._mprn = mprn
        self._attr_name = "ESB Smart Meter: Last Update"
        self._attr_unique_id = f"{mprn}_last_update"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._mprn)},
            name=f"ESB Smart Meter ({self._mprn})",
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(self.coordinator.async_add_listener(self._handle_coordinator_update))

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> datetime | None:
        """Return the timestamp of the last successful update."""
        return self.coordinator.last_successful_update_time


class LatestReadingTimeSensor(SensorEntity):
    """Sensor for the timestamp of the most recent meter reading in the CSV data."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_state_class = None
    _attr_native_unit_of_measurement = None
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, *, coordinator: ESBDataUpdateCoordinator, mprn: str) -> None:
        """Initialize the sensor."""
        super().__init__()
        self.coordinator = coordinator
        self._mprn = mprn
        self._attr_name = "ESB Smart Meter: Latest Reading"
        self._attr_unique_id = f"{mprn}_latest_reading_time"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._mprn)},
            name=f"ESB Smart Meter ({self._mprn})",
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(self.coordinator.async_add_listener(self._handle_coordinator_update))

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> datetime | None:
        """Return the timestamp of the most recent reading in the CSV."""
        if self.coordinator.data is None:
            return None
        latest = self.coordinator.data.latest_reading_time
        if latest is None:
            return None
        return latest.replace(tzinfo=timezone.utc)


class ApiStatusSensor(SensorEntity):
    """Sensor for API status."""

    _attr_device_class = None
    _attr_state_class = None
    _attr_native_unit_of_measurement = None
    _attr_icon = "mdi:api"

    def __init__(self, *, coordinator: ESBDataUpdateCoordinator, mprn: str) -> None:
        """Initialize the sensor."""
        super().__init__()
        self.coordinator = coordinator
        self._mprn = mprn
        self._attr_name = "ESB Smart Meter: API Status"
        self._attr_unique_id = f"{mprn}_api_status"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._mprn)},
            name=f"ESB Smart Meter ({self._mprn})",
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(self.coordinator.async_add_listener(self._handle_coordinator_update))

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> str:
        """Return the API status."""
        if self.coordinator.last_update_success is None:
            return "unknown"
        if self.coordinator.data is None:
            return "error"
        return "online"


class DataAgeSensor(SensorEntity):
    """Sensor for data age in hours."""

    _attr_device_class = None
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "h"
    _attr_icon = "mdi:timer-outline"

    def __init__(self, *, coordinator: ESBDataUpdateCoordinator, mprn: str) -> None:
        """Initialize the sensor."""
        super().__init__()
        self.coordinator = coordinator
        self._mprn = mprn
        self._attr_name = "ESB Smart Meter: Data Age"
        self._attr_unique_id = f"{mprn}_data_age"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._mprn)},
            name=f"ESB Smart Meter ({self._mprn})",
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(self.coordinator.async_add_listener(self._handle_coordinator_update))

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> float | None:
        """Return the age of the data in hours."""
        if self.coordinator.last_successful_update_time is None:
            return None

        age = datetime.now(timezone.utc) - self.coordinator.last_successful_update_time
        return round(age.total_seconds() / 3600, 1)  # Hours with 1 decimal place


class CircuitBreakerStatusSensor(SensorEntity):
    """Sensor showing circuit breaker state and health."""

    _attr_device_class = None
    _attr_state_class = None
    _attr_native_unit_of_measurement = None
    _attr_icon = "mdi:electric-switch"

    def __init__(self, *, coordinator: ESBDataUpdateCoordinator, mprn: str) -> None:
        """Initialize the sensor."""
        super().__init__()
        self.coordinator = coordinator
        self._mprn = mprn
        self._attr_name = "ESB Smart Meter: Circuit Breaker Status"
        self._attr_unique_id = f"{mprn}_circuit_breaker_status"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._mprn)},
            name=f"ESB Smart Meter ({self._mprn})",
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(self.coordinator.async_add_listener(self._handle_coordinator_update))

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> str:
        """Return circuit breaker state."""
        cb = self.coordinator.esb_api._circuit_breaker
        
        if not hasattr(cb, '_is_open'):
            return "unknown"
        
        now = datetime.now()
        
        # Check if circuit is open
        if cb._is_open and cb._last_failure_time:
            # Calculate backoff time
            from .const import CIRCUIT_BREAKER_TIMEOUT, CIRCUIT_BREAKER_MAX_TIMEOUT
            backoff_time = min(
                CIRCUIT_BREAKER_TIMEOUT * (2 ** (cb._failure_count - 1)),
                CIRCUIT_BREAKER_MAX_TIMEOUT,
            )
            elapsed = (now - cb._last_failure_time).total_seconds()
            
            if elapsed < backoff_time:
                return "open"
            return "half_open"
        
        return "closed"

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        cb = self.coordinator.esb_api._circuit_breaker
        
        if not hasattr(cb, '_failure_count'):
            return {}
        
        attrs = {
            "failure_count": cb._failure_count,
            "daily_attempts": cb._daily_attempts,
        }
        
        # Add constants for reference
        from .const import (
            CIRCUIT_BREAKER_FAILURES,
            CIRCUIT_BREAKER_MAX_TIMEOUT,
            MAX_AUTH_ATTEMPTS_PER_DAY,
        )
        attrs["failure_threshold"] = CIRCUIT_BREAKER_FAILURES
        attrs["daily_limit"] = MAX_AUTH_ATTEMPTS_PER_DAY
        
        # Add backoff information if circuit is open
        if cb._is_open and cb._last_failure_time:
            now = datetime.now()
            from .const import CIRCUIT_BREAKER_TIMEOUT
            backoff_time = min(
                CIRCUIT_BREAKER_TIMEOUT * (2 ** (cb._failure_count - 1)),
                CIRCUIT_BREAKER_MAX_TIMEOUT,
            )
            elapsed = (now - cb._last_failure_time).total_seconds()
            remaining = max(0, backoff_time - elapsed)
            
            attrs["backoff_seconds"] = int(backoff_time)
            attrs["time_remaining_seconds"] = int(remaining)
            attrs["time_remaining_minutes"] = round(remaining / 60, 1)
            
            if remaining > 0:
                blocked_until = cb._last_failure_time
                from datetime import timedelta
                blocked_until = blocked_until + timedelta(seconds=backoff_time)
                attrs["blocked_until"] = blocked_until.isoformat()
        
        if cb._last_failure_time:
            attrs["last_failure"] = cb._last_failure_time.isoformat()
        
        if cb._daily_attempts_reset_time:
            attrs["daily_counter_resets"] = cb._daily_attempts_reset_time.date().isoformat()
        
        return attrs

    @property
    def icon(self) -> str:
        """Return icon based on circuit breaker state."""
        state = self.native_value
        return {
            "closed": "mdi:check-circle",
            "open": "mdi:alert-circle",
            "half_open": "mdi:refresh-circle",
            "unknown": "mdi:help-circle",
        }.get(state, "mdi:help-circle")
