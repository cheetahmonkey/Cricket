import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPOSITORY_ROOT / "scripts" / "run_daily_cricket_healthchecked.sh"
TEST_URL = "https://hc-ping.com/test-check-id"


class HealthcheckWrapperTest(unittest.TestCase):
    def run_wrapper(self, runner_exit=0, curl_exit=0):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            ping_log = root / "pings.log"
            runner_log = root / "runner.log"
            url_file = root / "healthchecks_url"
            url_file.write_text(TEST_URL + "\n", encoding="utf-8")

            fake_curl = bin_dir / "curl"
            fake_curl.write_text(
                textwrap.dedent(
                    """\
                    #!/usr/bin/env bash
                    printf '%s\n' "${!#}" >> "$CRICKET_TEST_PING_LOG"
                    exit "${CRICKET_TEST_CURL_EXIT:-0}"
                    """
                ),
                encoding="utf-8",
            )
            fake_curl.chmod(0o755)

            fake_runner = root / "runner.sh"
            fake_runner.write_text(
                textwrap.dedent(
                    """\
                    #!/usr/bin/env bash
                    echo ran >> "$CRICKET_TEST_RUNNER_LOG"
                    exit "${CRICKET_TEST_RUNNER_EXIT:-0}"
                    """
                ),
                encoding="utf-8",
            )
            fake_runner.chmod(0o755)

            env = os.environ.copy()
            env.update(
                {
                    "PATH": "%s:%s" % (bin_dir, env.get("PATH", "")),
                    "CRICKET_HEALTHCHECK_URL_FILE": str(url_file),
                    "CRICKET_DAILY_RUNNER": str(fake_runner),
                    "CRICKET_TEST_PING_LOG": str(ping_log),
                    "CRICKET_TEST_RUNNER_LOG": str(runner_log),
                    "CRICKET_TEST_CURL_EXIT": str(curl_exit),
                    "CRICKET_TEST_RUNNER_EXIT": str(runner_exit),
                }
            )
            completed = subprocess.run(
                ["/bin/bash", str(WRAPPER)],
                env=env,
                capture_output=True,
                text=True,
            )
            pings = ping_log.read_text(encoding="utf-8").splitlines()
            runner_calls = runner_log.read_text(encoding="utf-8").splitlines()
            return completed, pings, runner_calls

    def test_sends_start_and_success(self):
        completed, pings, runner_calls = self.run_wrapper()

        self.assertEqual(completed.returncode, 0)
        self.assertEqual(pings, [TEST_URL + "/start", TEST_URL])
        self.assertEqual(runner_calls, ["ran"])

    def test_reports_runner_exit_status_as_failure(self):
        completed, pings, runner_calls = self.run_wrapper(runner_exit=7)

        self.assertEqual(completed.returncode, 7)
        self.assertEqual(pings, [TEST_URL + "/start", TEST_URL + "/7"])
        self.assertEqual(runner_calls, ["ran"])

    def test_monitoring_failure_does_not_fail_cricket(self):
        completed, pings, runner_calls = self.run_wrapper(curl_exit=22)

        self.assertEqual(completed.returncode, 0)
        self.assertEqual(pings, [TEST_URL + "/start", TEST_URL])
        self.assertEqual(runner_calls, ["ran"])
        self.assertIn("could not send start ping", completed.stderr)
        self.assertIn("could not send success ping", completed.stderr)


if __name__ == "__main__":
    unittest.main()
