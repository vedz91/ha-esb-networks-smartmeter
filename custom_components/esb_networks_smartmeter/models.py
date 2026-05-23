"""Data models for ESB Smart Meter integration."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

from .const import (
    CSV_COLUMN_DATE,
    CSV_COLUMN_READ_TYPE,
    CSV_COLUMN_VALUE,
    CSV_DATE_FORMAT,
    MAX_DATA_AGE_DAYS,
    READ_TYPE_EXPORT,
    READ_TYPE_IMPORT,
)

_LOGGER = logging.getLogger(__name__)


class ESBData:
    """Class to manipulate data retrieved from ESB with memory optimization."""

    def __init__(self, *, data: List[Dict[str, Any]]) -> None:
        """Initialize with raw CSV data, filtering old data to prevent memory leaks."""
        # Validate CSV structure
        if data:
            if not self._validate_csv_structure(data[0]):
                _LOGGER.error("CSV validation failed. First row keys: %s", list(data[0].keys()))
                _LOGGER.error("Expected columns: %s, %s", CSV_COLUMN_DATE, CSV_COLUMN_VALUE)
                _LOGGER.error("First row data: %s", data[0])
                raise ValueError(f"Invalid CSV structure. Expected columns: " f"{CSV_COLUMN_DATE}, {CSV_COLUMN_VALUE}")

        # Filter out data older than MAX_DATA_AGE_DAYS to prevent memory leaks
        cutoff_date = datetime.now() - timedelta(days=MAX_DATA_AGE_DAYS)
        self._import_data, self._export_data = self._filter_and_parse_data(data, cutoff_date)
        # Backwards-compatible alias for the consumption stream.
        self._data: List[Tuple[datetime, float]] = self._import_data
        _LOGGER.debug(
            "Loaded %d import rows, %d export rows (filtered data older than %d days)",
            len(self._import_data),
            len(self._export_data),
            MAX_DATA_AGE_DAYS,
        )

    @staticmethod
    def _validate_csv_structure(row: dict[str, Any]) -> bool:
        """Validate that required CSV columns exist."""
        required_columns = [CSV_COLUMN_DATE, CSV_COLUMN_VALUE]
        available_columns = list(row.keys())
        has_required = all(col in row for col in required_columns)

        if not has_required:
            _LOGGER.error("CSV validation failed. Required: %s, Available: %s", required_columns, available_columns)

        return has_required

    def _filter_and_parse_data(
        self, data: list[dict[str, Any]], cutoff_date: datetime
    ) -> tuple[list[tuple[datetime, float]], list[tuple[datetime, float]]]:
        """Filter old data, pre-parse for performance, and partition by Read Type."""
        import_data: list[tuple[datetime, float]] = []
        export_data: list[tuple[datetime, float]] = []
        for row in data:
            try:
                timestamp = datetime.strptime(row[CSV_COLUMN_DATE], CSV_DATE_FORMAT)
                if timestamp < cutoff_date:
                    continue
                value = float(row[CSV_COLUMN_VALUE])
                # ESB Read Type column contains values like "Active Import Interval (kW)"
                # or "Active Export Interval (kW)" — match by substring. Rows missing
                # the column fall through to import for backwards compatibility with
                # non-microgen accounts and older fixtures.
                read_type = row.get(CSV_COLUMN_READ_TYPE, "")
                if READ_TYPE_EXPORT in read_type:
                    export_data.append((timestamp, value))
                else:
                    import_data.append((timestamp, value))
            except (ValueError, KeyError) as err:
                _LOGGER.warning("Skipping invalid row: %s", err)
                continue
        return import_data, export_data

    @staticmethod
    def __sum_since(dataset: list[tuple[datetime, float]], since: datetime) -> float:
        """Sum values in a dataset since a specific datetime."""
        return sum(value for timestamp, value in dataset if timestamp >= since)

    @staticmethod
    def _today_start() -> datetime:
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def _week_start() -> datetime:
        now = datetime.now()
        return now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=now.weekday())

    @staticmethod
    def _month_start() -> datetime:
        return datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    @property
    def today(self) -> float:
        """Get today's consumption."""
        return self.__sum_since(self._import_data, self._today_start())

    @property
    def last_24_hours(self) -> float:
        """Get last 24 hours consumption."""
        return self.__sum_since(self._import_data, datetime.now() - timedelta(days=1))

    @property
    def this_week(self) -> float:
        """Get this week's consumption."""
        return self.__sum_since(self._import_data, self._week_start())

    @property
    def last_7_days(self) -> float:
        """Get last 7 days consumption."""
        return self.__sum_since(self._import_data, datetime.now() - timedelta(days=7))

    @property
    def this_month(self) -> float:
        """Get this month's consumption."""
        return self.__sum_since(self._import_data, self._month_start())

    @property
    def last_30_days(self) -> float:
        """Get last 30 days consumption."""
        return self.__sum_since(self._import_data, datetime.now() - timedelta(days=30))

    @property
    def exported_today(self) -> float:
        """Get today's grid export."""
        return self.__sum_since(self._export_data, self._today_start())

    @property
    def exported_last_24_hours(self) -> float:
        """Get last 24 hours of grid export."""
        return self.__sum_since(self._export_data, datetime.now() - timedelta(days=1))

    @property
    def exported_this_week(self) -> float:
        """Get this week's grid export."""
        return self.__sum_since(self._export_data, self._week_start())

    @property
    def exported_last_7_days(self) -> float:
        """Get last 7 days of grid export."""
        return self.__sum_since(self._export_data, datetime.now() - timedelta(days=7))

    @property
    def exported_this_month(self) -> float:
        """Get this month's grid export."""
        return self.__sum_since(self._export_data, self._month_start())

    @property
    def exported_last_30_days(self) -> float:
        """Get last 30 days of grid export."""
        return self.__sum_since(self._export_data, datetime.now() - timedelta(days=30))

    @property
    def latest_reading_time(self) -> datetime | None:
        """Return the timestamp of the most recent meter reading in the CSV."""
        all_timestamps = [ts for ts, _ in self._import_data] + [ts for ts, _ in self._export_data]
        return max(all_timestamps) if all_timestamps else None

    @property
    def current_import(self) -> float | None:
        """Return the most recent import interval value (kWh)."""
        if not self._import_data:
            return None
        return max(self._import_data, key=lambda x: x[0])[1]

    @property
    def current_import_time(self) -> datetime | None:
        """Return the timestamp of the most recent import interval."""
        if not self._import_data:
            return None
        return max(self._import_data, key=lambda x: x[0])[0]

    @property
    def current_export(self) -> float | None:
        """Return the most recent export interval value (kWh)."""
        if not self._export_data:
            return None
        return max(self._export_data, key=lambda x: x[0])[1]

    @property
    def current_export_time(self) -> datetime | None:
        """Return the timestamp of the most recent export interval."""
        if not self._export_data:
            return None
        return max(self._export_data, key=lambda x: x[0])[0]

    def get_history_since(self, days: int) -> tuple[list[tuple[datetime, float]], list[tuple[datetime, float]]]:
        """Return (import_data, export_data) sorted ascending for the last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        imp = sorted([(ts, v) for ts, v in self._import_data if ts >= cutoff], key=lambda x: x[0])
        exp = sorted([(ts, v) for ts, v in self._export_data if ts >= cutoff], key=lambda x: x[0])
        return imp, exp
