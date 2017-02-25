""" Test operations that list patches """

from contextlib import contextmanager
from io import StringIO
import os.path
import sys
from unittest import mock
from unittest import TestCase

from quilt.cli.next import NextCommand
from quilt.cli.previous import PreviousCommand

class Test(TestCase):

    def test_previous_only_unapplied(self):
        with self._setup_test_data(), \
                mock.patch("sys.stderr", StringIO()):
            with self.assertRaises(SystemExit) as caught:
                PreviousCommand().run(None, [])
            self.assertEqual(caught.exception.code, 1)
            self.assertIn("No patches applied", sys.stderr.getvalue())
    
    def test_next_topmost(self):
        with self._setup_test_data(), \
                mock.patch("sys.stdout", StringIO()):
            NextCommand().run(None, [])
            self.assertEqual("p1.patch\n", sys.stdout.getvalue())
    
    @contextmanager
    def _setup_test_data(self):
        data = os.path.join(os.path.dirname(__file__), "data")
        patches = os.path.join(data, "push", "test2", "patches")
        no_applied = os.path.join(data, "push", "test2")
        
        with mock.patch.dict("os.environ", (
            ("QUILT_PATCHES", patches),
            ("QUILT_PC", no_applied),
        )):
            yield
