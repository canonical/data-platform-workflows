import unittest

from data_platform_workflows_cli.update_bundle import filter_application, parser


class TestUpdateBundle(unittest.TestCase):

    def test_filter_application_exclude_ok(self):
        assert filter_application("package1", [])

    def test_filter_application_exclude_ko(self):
        assert not filter_application("package1",["package1"])

    def test_argument_parsing_vanilla(self):
        args = parser.parse_args([
            "my-file"
        ])
        self.assertEqual("my-file", args.file_path)
        self.assertEqual([], args.exclude)

    def test_argument_parsing_exclude(self):
        args = parser.parse_args([
            "my-file",
            "--exclude", "package1", "--exclude", "package2"
        ])
        self.assertEqual("my-file", args.file_path)
        self.assertEqual(["package1", "package2"], args.exclude)

    def test_argument_parsing_exclude_comma_separated(self):
        args = parser.parse_args([
            "my-file",
            "--exclude", "package1,package2"
        ])
        self.assertEqual("my-file", args.file_path)
        self.assertEqual(["package1", "package2"], args.exclude)

    def test_argument_parsing_exclude_empty_argument(self):
        args = parser.parse_args([
            "my-file",
            "--exclude", ""
        ])
        self.assertEqual("my-file", args.file_path)
        self.assertEqual([], args.exclude)
