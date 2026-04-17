import os
import pytest

# Only run these tests when DATA_QUALITY_CHECK env var is set
# (i.e., after deployment, not on every PR)
pytestmark = pytest.mark.skipif(
    os.getenv("DATA_QUALITY_CHECK") != "true",
    reason="Data quality tests only run post-deployment"
)


class TestEnrollmentDataQuality:
    """Validate enrollment data after pipeline execution."""

    def test_enrollment_table_not_empty(self, db_connection):
        """After a successful load, staging.Enrollment should have rows."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM staging.Enrollment")
        count = cursor.fetchone()[0]
        assert count > 0, "Enrollment table is empty after pipeline run"

    def test_no_null_child_ids(self, db_connection):
        """ChildID is the primary identifier — must never be null."""
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM staging.Enrollment WHERE ChildID IS NULL"
        )
        null_count = cursor.fetchone()[0]
        assert null_count == 0, f"Found {null_count} rows with NULL ChildID"

    def test_enrollment_dates_are_valid(self, db_connection):
        """Enrollment dates should not be in the future."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM staging.Enrollment
            WHERE EnrollmentDate > GETDATE()
        """)
        future_count = cursor.fetchone()[0]
        assert future_count == 0, (
            f"Found {future_count} enrollments with future dates"
        )