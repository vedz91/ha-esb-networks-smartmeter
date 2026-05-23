"""Tests for ESB Data manipulation."""

from datetime import datetime, timedelta

import pytest

from custom_components.esb_smart_meter.models import ESBData


class TestESBData:
    """Test ESBData class."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        now = datetime.now()
        data = []

        # Add 100 days of data (some will be filtered out)
        for i in range(100):
            date = now - timedelta(days=i)
            data.append(
                {
                    "Read Date and End Time": date.strftime("%d-%m-%Y %H:%M"),
                    "Read Value": "1.5",
                    "Read Type": "Active Import",
                    "MPRN": "12345678901",
                }
            )

        return data

    def test_esb_data_initialization(self, sample_data):
        """Test ESBData initialization."""
        esb_data = ESBData(data=sample_data)
        assert esb_data is not None
        # Should filter out data older than 90 days
        assert len(esb_data._data) <= 90

    def test_esb_data_today(self):
        """Test today's data calculation."""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        data = [
            {
                "Read Date and End Time": today_start.strftime("%d-%m-%Y %H:%M"),
                "Read Value": "2.5",
            },
            {
                "Read Date and End Time": (today_start + timedelta(hours=1)).strftime("%d-%m-%Y %H:%M"),
                "Read Value": "3.0",
            },
        ]

        esb_data = ESBData(data=data)
        assert esb_data.today == 5.5

    def test_esb_data_last_24_hours(self):
        """Test last 24 hours data calculation."""
        now = datetime.now()

        data = [
            {
                "Read Date and End Time": (now - timedelta(hours=23)).strftime("%d-%m-%Y %H:%M"),
                "Read Value": "1.0",
            },
            {
                "Read Date and End Time": (now - timedelta(hours=25)).strftime("%d-%m-%Y %H:%M"),
                "Read Value": "2.0",  # Should not be included
            },
        ]

        esb_data = ESBData(data=data)
        assert esb_data.last_24_hours == 1.0

    def test_esb_data_this_week(self):
        """Test this week's data calculation."""
        now = datetime.now()
        week_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=now.weekday())

        data = [
            {
                "Read Date and End Time": week_start.strftime("%d-%m-%Y %H:%M"),
                "Read Value": "5.0",
            },
            {
                "Read Date and End Time": (week_start + timedelta(days=1)).strftime("%d-%m-%Y %H:%M"),
                "Read Value": "3.0",
            },
        ]

        esb_data = ESBData(data=data)
        assert esb_data.this_week == 8.0

    def test_esb_data_last_7_days(self):
        """Test last 7 days data calculation."""
        now = datetime.now()

        data = []
        for i in range(7):
            data.append(
                {
                    "Read Date and End Time": (now - timedelta(days=i)).strftime("%d-%m-%Y %H:%M"),
                    "Read Value": "1.0",
                }
            )

        esb_data = ESBData(data=data)
        assert esb_data.last_7_days == 7.0

    def test_esb_data_this_month(self):
        """Test this month's data calculation."""
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        data = [
            {
                "Read Date and End Time": month_start.strftime("%d-%m-%Y %H:%M"),
                "Read Value": "10.0",
            },
            {
                "Read Date and End Time": (month_start + timedelta(days=5)).strftime("%d-%m-%Y %H:%M"),
                "Read Value": "5.0",
            },
        ]

        esb_data = ESBData(data=data)
        assert esb_data.this_month == 15.0

    def test_esb_data_last_30_days(self):
        """Test last 30 days data calculation."""
        now = datetime.now()

        data = []
        for i in range(30):
            data.append(
                {
                    "Read Date and End Time": (now - timedelta(days=i)).strftime("%d-%m-%Y %H:%M"),
                    "Read Value": "2.0",
                }
            )

        esb_data = ESBData(data=data)
        assert esb_data.last_30_days == 60.0

    def test_esb_data_invalid_csv_structure(self):
        """Test invalid CSV structure handling."""
        data = [{"invalid": "data"}]

        with pytest.raises(ValueError, match="Invalid CSV structure"):
            ESBData(data=data)

    def test_esb_data_empty_list(self):
        """Test empty data list."""
        esb_data = ESBData(data=[])
        assert esb_data.today == 0.0
        assert esb_data.last_24_hours == 0.0

    def test_esb_data_filters_old_data(self):
        """Test that data older than MAX_DATA_AGE_DAYS is filtered."""
        now = datetime.now()

        data = [
            {
                "Read Date and End Time": (now - timedelta(days=95)).strftime("%d-%m-%Y %H:%M"),
                "Read Value": "1.0",
            },
            {
                "Read Date and End Time": (now - timedelta(days=50)).strftime("%d-%m-%Y %H:%M"),
                "Read Value": "2.0",
            },
        ]

        esb_data = ESBData(data=data)
        # Only data within 90 days should be kept
        assert len(esb_data._data) == 1

    def test_esb_data_handles_invalid_rows(self):
        """Test that invalid rows are skipped gracefully."""
        now = datetime.now()

        data = [
            {
                "Read Date and End Time": now.strftime("%d-%m-%Y %H:%M"),
                "Read Value": "5.0",
            },
            {
                "Read Date and End Time": "invalid-date",
                "Read Value": "1.0",
            },
            {
                "Read Date and End Time": now.strftime("%d-%m-%Y %H:%M"),
                "Read Value": "not-a-number",
            },
        ]

        esb_data = ESBData(data=data)
        # Should only have the valid row
        assert len(esb_data._data) == 1
        assert esb_data.today == 5.0

    def test_esb_data_partitions_import_and_export(self):
        """Import and export rows are tracked in separate datasets."""
        now = datetime.now()
        today_str = now.strftime("%d-%m-%Y %H:%M")

        data = [
            {"Read Date and End Time": today_str, "Read Value": "2.5", "Read Type": "Active Import"},
            {"Read Date and End Time": today_str, "Read Value": "1.0", "Read Type": "Active Export"},
            {"Read Date and End Time": today_str, "Read Value": "3.5", "Read Type": "Active Import"},
            {"Read Date and End Time": today_str, "Read Value": "0.5", "Read Type": "Active Export"},
        ]

        esb_data = ESBData(data=data)

        assert esb_data.today == 6.0  # 2.5 + 3.5 (import only)
        assert esb_data.exported_today == 1.5  # 1.0 + 0.5 (export only)

    def test_esb_data_matches_read_type_by_substring(self):
        """Real ESB CSVs use 'Active Import Interval (kW)' / 'Active Export Interval (kW)'."""
        now = datetime.now()
        today_str = now.strftime("%d-%m-%Y %H:%M")

        data = [
            {
                "Read Date and End Time": today_str,
                "Read Value": "0.188",
                "Read Type": "Active Import Interval (kW)",
            },
            {
                "Read Date and End Time": today_str,
                "Read Value": "0.250",
                "Read Type": "Active Export Interval (kW)",
            },
        ]

        esb_data = ESBData(data=data)

        assert esb_data.today == 0.188
        assert esb_data.exported_today == 0.250

    def test_esb_data_missing_read_type_treated_as_import(self):
        """Rows without a Read Type column default to import for backwards compat."""
        now = datetime.now()
        today_str = now.strftime("%d-%m-%Y %H:%M")

        data = [
            {"Read Date and End Time": today_str, "Read Value": "4.0"},
        ]

        esb_data = ESBData(data=data)

        assert esb_data.today == 4.0
        assert esb_data.exported_today == 0.0

    def test_esb_data_export_time_buckets(self):
        """All six exported_* time buckets compute correctly from export rows."""
        now = datetime.now()
        week_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=now.weekday())
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        data = [
            # Today (also in week and month)
            {
                "Read Date and End Time": now.strftime("%d-%m-%Y %H:%M"),
                "Read Value": "1.0",
                "Read Type": "Active Export",
            },
            # 23 hours ago (in last_24_hours)
            {
                "Read Date and End Time": (now - timedelta(hours=23)).strftime("%d-%m-%Y %H:%M"),
                "Read Value": "2.0",
                "Read Type": "Active Export",
            },
            # Start of this week
            {
                "Read Date and End Time": week_start.strftime("%d-%m-%Y %H:%M"),
                "Read Value": "3.0",
                "Read Type": "Active Export",
            },
            # 6 days ago (in last_7_days and last_30_days)
            {
                "Read Date and End Time": (now - timedelta(days=6)).strftime("%d-%m-%Y %H:%M"),
                "Read Value": "4.0",
                "Read Type": "Active Export",
            },
            # Start of month
            {
                "Read Date and End Time": month_start.strftime("%d-%m-%Y %H:%M"),
                "Read Value": "5.0",
                "Read Type": "Active Export",
            },
            # Import row that must NOT count in any export property
            {
                "Read Date and End Time": now.strftime("%d-%m-%Y %H:%M"),
                "Read Value": "999.0",
                "Read Type": "Active Import",
            },
        ]

        esb_data = ESBData(data=data)

        # Export sums must exclude the 999.0 import row
        assert esb_data.exported_today >= 1.0
        assert esb_data.exported_last_24_hours >= 3.0  # 1.0 + 2.0
        assert esb_data.exported_this_week >= 1.0  # at minimum today
        assert esb_data.exported_last_7_days >= 7.0  # 1.0 + 2.0 + 4.0
        assert esb_data.exported_this_month >= 6.0  # 1.0 + 5.0 at minimum
        assert esb_data.exported_last_30_days >= 15.0  # all 5 export rows within 30d

    def test_latest_reading_time(self):
        """latest_reading_time returns the most recent timestamp across import and export rows."""
        now = datetime.now().replace(second=0, microsecond=0)
        older = now - timedelta(hours=2)
        data = [
            {"Read Date and End Time": older.strftime("%d-%m-%Y %H:%M"), "Read Value": "1.0"},
            {"Read Date and End Time": now.strftime("%d-%m-%Y %H:%M"), "Read Value": "2.0"},
        ]
        esb_data = ESBData(data=data)
        assert esb_data.latest_reading_time == now

    def test_latest_reading_time_picks_across_import_and_export(self):
        """latest_reading_time considers both import and export rows."""
        now = datetime.now().replace(second=0, microsecond=0)
        older = now - timedelta(hours=1)
        data = [
            {"Read Date and End Time": older.strftime("%d-%m-%Y %H:%M"), "Read Value": "1.0", "Read Type": "Active Import"},
            {"Read Date and End Time": now.strftime("%d-%m-%Y %H:%M"), "Read Value": "0.5", "Read Type": "Active Export"},
        ]
        esb_data = ESBData(data=data)
        assert esb_data.latest_reading_time == now

    def test_latest_reading_time_empty(self):
        """latest_reading_time returns None when there is no data."""
        esb_data = ESBData(data=[])
        assert esb_data.latest_reading_time is None

    def test_current_import_returns_most_recent_value(self):
        """current_import returns the value from the latest import timestamp."""
        now = datetime.now().replace(second=0, microsecond=0)
        older = now - timedelta(hours=1)
        data = [
            {"Read Date and End Time": older.strftime("%d-%m-%Y %H:%M"), "Read Value": "0.150", "Read Type": "Active Import Interval (kW)"},
            {"Read Date and End Time": now.strftime("%d-%m-%Y %H:%M"), "Read Value": "0.264", "Read Type": "Active Import Interval (kW)"},
        ]
        esb_data = ESBData(data=data)
        assert esb_data.current_import == 0.264

    def test_current_import_returns_none_when_empty(self):
        """current_import returns None when there are no import rows."""
        data = [
            {"Read Date and End Time": datetime.now().strftime("%d-%m-%Y %H:%M"), "Read Value": "0.5", "Read Type": "Active Export Interval (kW)"},
        ]
        esb_data = ESBData(data=data)
        assert esb_data.current_import is None

    def test_current_import_time_returns_most_recent_timestamp(self):
        """current_import_time returns the timestamp of the latest import row."""
        now = datetime.now().replace(second=0, microsecond=0)
        older = now - timedelta(hours=1)
        data = [
            {"Read Date and End Time": older.strftime("%d-%m-%Y %H:%M"), "Read Value": "0.100", "Read Type": "Active Import Interval (kW)"},
            {"Read Date and End Time": now.strftime("%d-%m-%Y %H:%M"), "Read Value": "0.264", "Read Type": "Active Import Interval (kW)"},
        ]
        esb_data = ESBData(data=data)
        assert esb_data.current_import_time == now

    def test_current_import_time_returns_none_when_empty(self):
        """current_import_time returns None when there are no import rows."""
        esb_data = ESBData(data=[])
        assert esb_data.current_import_time is None

    def test_current_export_returns_most_recent_value(self):
        """current_export returns the value from the latest export timestamp."""
        now = datetime.now().replace(second=0, microsecond=0)
        older = now - timedelta(hours=1)
        data = [
            {"Read Date and End Time": older.strftime("%d-%m-%Y %H:%M"), "Read Value": "0.100", "Read Type": "Active Export Interval (kW)"},
            {"Read Date and End Time": now.strftime("%d-%m-%Y %H:%M"), "Read Value": "0.333", "Read Type": "Active Export Interval (kW)"},
        ]
        esb_data = ESBData(data=data)
        assert esb_data.current_export == 0.333

    def test_current_export_returns_none_when_empty(self):
        """current_export returns None when there are no export rows."""
        esb_data = ESBData(data=[])
        assert esb_data.current_export is None

    def test_current_export_time_returns_most_recent_timestamp(self):
        """current_export_time returns the timestamp of the latest export row."""
        now = datetime.now().replace(second=0, microsecond=0)
        older = now - timedelta(hours=1)
        data = [
            {"Read Date and End Time": older.strftime("%d-%m-%Y %H:%M"), "Read Value": "0.050", "Read Type": "Active Export Interval (kW)"},
            {"Read Date and End Time": now.strftime("%d-%m-%Y %H:%M"), "Read Value": "0.333", "Read Type": "Active Export Interval (kW)"},
        ]
        esb_data = ESBData(data=data)
        assert esb_data.current_export_time == now

    def test_current_export_time_returns_none_when_empty(self):
        """current_export_time returns None when there are no export rows."""
        esb_data = ESBData(data=[])
        assert esb_data.current_export_time is None

    def test_get_history_since_filters_by_days(self):
        """get_history_since returns only rows within the last N days."""
        now = datetime.now().replace(second=0, microsecond=0)
        data = [
            {"Read Date and End Time": (now - timedelta(days=10)).strftime("%d-%m-%Y %H:%M"), "Read Value": "1.0", "Read Type": "Active Import Interval (kW)"},
            {"Read Date and End Time": (now - timedelta(days=16)).strftime("%d-%m-%Y %H:%M"), "Read Value": "2.0", "Read Type": "Active Import Interval (kW)"},
        ]
        esb_data = ESBData(data=data)
        imp, exp = esb_data.get_history_since(15)
        assert len(imp) == 1
        assert imp[0][1] == 1.0
        assert len(exp) == 0

    def test_get_history_since_returns_sorted_ascending(self):
        """get_history_since returns data sorted by timestamp ascending."""
        now = datetime.now().replace(second=0, microsecond=0)
        data = [
            {"Read Date and End Time": now.strftime("%d-%m-%Y %H:%M"), "Read Value": "0.3", "Read Type": "Active Import Interval (kW)"},
            {"Read Date and End Time": (now - timedelta(hours=1)).strftime("%d-%m-%Y %H:%M"), "Read Value": "0.1", "Read Type": "Active Import Interval (kW)"},
            {"Read Date and End Time": (now - timedelta(hours=2)).strftime("%d-%m-%Y %H:%M"), "Read Value": "0.2", "Read Type": "Active Import Interval (kW)"},
        ]
        esb_data = ESBData(data=data)
        imp, _ = esb_data.get_history_since(15)
        values = [v for _, v in imp]
        assert values == [0.2, 0.1, 0.3]

    def test_get_history_since_separates_import_and_export(self):
        """get_history_since returns import and export in separate lists."""
        now = datetime.now().replace(second=0, microsecond=0)
        data = [
            {"Read Date and End Time": now.strftime("%d-%m-%Y %H:%M"), "Read Value": "0.188", "Read Type": "Active Import Interval (kW)"},
            {"Read Date and End Time": now.strftime("%d-%m-%Y %H:%M"), "Read Value": "0.050", "Read Type": "Active Export Interval (kW)"},
        ]
        esb_data = ESBData(data=data)
        imp, exp = esb_data.get_history_since(15)
        assert len(imp) == 1
        assert len(exp) == 1
        assert imp[0][1] == 0.188
        assert exp[0][1] == 0.050
