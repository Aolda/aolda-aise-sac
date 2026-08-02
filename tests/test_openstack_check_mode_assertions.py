from pathlib import Path
import unittest

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class OpenStackCheckModeValidationTest(unittest.TestCase):
    def test_post_change_validation_is_disabled_in_check_mode(self):
        components = ("keystone", "nova", "cinder")

        for component in components:
            with self.subTest(component=component):
                task_file = (
                    PROJECT_ROOT
                    / "roles"
                    / f"{component}-security"
                    / "tasks"
                    / "main.yml"
                )
                tasks = yaml.safe_load(task_file.read_text(encoding="utf-8"))
                validation_tasks = [
                    task
                    for task in tasks
                    if task.get("ansible.builtin.import_tasks") == "validate.yml"
                ]

                self.assertEqual(len(validation_tasks), 1)
                conditions = validation_tasks[0].get("when", [])
                if isinstance(conditions, str):
                    conditions = [conditions]
                self.assertIn("not ansible_check_mode", conditions)


if __name__ == "__main__":
    unittest.main()
