import unittest
from unittest.mock import patch

from fastapi import HTTPException

from src.app import activities, unregister_from_activity


class UnregisterTests(unittest.TestCase):
    def setUp(self):
        self.activities = patch.dict(
            activities,
            {
                "Chess Club": {"participants": ["first@example.com", "second@example.com"]},
                "Art Club": {"participants": ["first@example.com"]},
            },
            clear=True,
        )
        self.activities.start()
        self.addCleanup(self.activities.stop)

    def test_unregister_removes_only_the_selected_participant(self):
        unregister_from_activity("Chess Club", "first@example.com")

        self.assertEqual(activities["Chess Club"]["participants"], ["second@example.com"])
        self.assertEqual(activities["Art Club"]["participants"], ["first@example.com"])

    def test_unknown_activity_returns_not_found(self):
        with self.assertRaises(HTTPException) as error:
            unregister_from_activity("Missing", "first@example.com")

        self.assertEqual(error.exception.status_code, 404)

    def test_unknown_participant_returns_not_found_without_changes(self):
        with self.assertRaises(HTTPException) as error:
            unregister_from_activity("Chess Club", "missing@example.com")

        self.assertEqual(error.exception.status_code, 404)
        self.assertEqual(
            activities["Chess Club"]["participants"], ["first@example.com", "second@example.com"]
        )


if __name__ == "__main__":
    unittest.main()
