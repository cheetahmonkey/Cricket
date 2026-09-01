import subprocess
import unittest
from unittest.mock import patch

from cricket.sources.base import SourceAdapter


class SourceAdapterTest(unittest.TestCase):
    def test_curl_fetch_treats_http_errors_as_failures(self):
        source = SourceAdapter({"name": "example", "fetch_via_curl": True})
        completed = subprocess.CompletedProcess([], 0, stdout=b"ok", stderr=b"")
        with patch("cricket.sources.base.subprocess.run", return_value=completed) as run:
            self.assertEqual(source.fetch("https://example.test/data"), "ok")

        command = run.call_args.args[0]
        self.assertEqual(command[:2], ["curl", "-LfsS"])
        self.assertTrue(run.call_args.kwargs["check"])


if __name__ == "__main__":
    unittest.main()
