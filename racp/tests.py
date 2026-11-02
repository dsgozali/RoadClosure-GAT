import polars as pl
from django.test import TestCase
from unittest.mock import patch

from .services import (
    build_matrix_group,
    create_matrix_pdf,
    display_hour_label,
    get_cell_traceability,
)


def sample_frame():
    return pl.DataFrame(
        {
            "ROAD_NAME": ["Aster Road", "Aster Road"],
            "DESCRIPTION": ["Sample access", "Sample access"],
            "GAZETTAL_DIRECTION": ["WB", "WB"],
            "HOUR": ["0 to 1", "1 to 2"],
            "REGION_NAME": ["Sample Region", "Sample Region"],
            "MON": [100, 200],
            "TUE": [200, 300],
            "WED": [300, 400],
            "THU": [400, 500],
            "FRI": [500, 600],
            "SAT": [600, 700],
            "SUN": [700, 800],
        }
    )

class MatrixServiceTests(TestCase):
    def test_hour_labels_match_table_format(self):
        self.assertEqual(display_hour_label("0 to 1"), "12-1am")
        self.assertEqual(display_hour_label("11 to 12"), "11-12pm")
        self.assertEqual(display_hour_label("23 to 0"), "11-12am")

    def test_matrix_has_weekday_and_weekend_rows_with_lane_values(self):
        frame = sample_frame()

        matrix = build_matrix_group(frame, "Sample access", "WB")

        self.assertEqual([row["Day-HR"] for row in matrix], ["Weekday", "SAT", "SUN"])
        self.assertEqual(matrix[0]["12-1am"], 1)
        self.assertEqual(matrix[1]["12-1am"], 1)

    def test_traceability_matches_the_matrix_cell_calculation(self):
        frame = sample_frame()

        trace = get_cell_traceability(
            frame, "Aster Road", "Sample access", "WB", "Weekday", "12-1am"
        )

        self.assertEqual(trace["input_values"], [100, 200, 300, 400, 500])
        self.assertEqual(trace["percentile_85"], 400.0)
        self.assertEqual(trace["lane_value"], 1)

    def test_pdf_export_returns_a_pdf_document(self):
        pdf = create_matrix_pdf(
            [
                {
                    "description": "Sample access",
                    "columns": ["Direction", "Day-HR", "12-1am"],
                    "rows": [{"Direction": "WB", "Day-HR": "Weekday", "12-1am": 1}],
                }
            ],
            "Aster Road",
        )

        self.assertTrue(pdf.getvalue().startswith(b"%PDF"))


class DjangoPageTests(TestCase):
    def setUp(self):
        self.frame = sample_frame()
        self.patches = [
            patch("racp.pages.common.load_traffic_data", return_value=self.frame),
            patch("racp.pages.home.build_map_points", return_value=[]),
        ]
        for mocked in self.patches:
            mocked.start()
            self.addCleanup(mocked.stop)

    def test_home_matrix_and_pdf_pages_render(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/matrix/").status_code, 200)
        self.assertEqual(self.client.get("/pdf/").status_code, 200)

    def test_clicking_a_matrix_cell_shows_traceability(self):
        response = self.client.get(
            "/matrix/",
            {
                "road": "Aster Road",
                "description": "Sample access",
                "direction": "WB",
                "day": "Weekday",
                "hour": "12-1am",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Traffic inputs:")
        self.assertContains(response, "400")

    def test_pdf_download_returns_attachment(self):
        response = self.client.get("/pdf/download/", {"road": "Aster Road"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))
