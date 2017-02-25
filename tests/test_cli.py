from io import StringIO
import runpy
import sys
from unittest import mock
from unittest import TestCase

class Test(TestCase):

    def test_registration(self):
        with mock.patch("sys.argv", ["pquilt", "push", "--help"]), \
                mock.patch("sys.stdout", StringIO()):
            try:
                runpy.run_path("pquilt", run_name="__main__")
            except SystemExit as exit:
                self.assertEqual(exit.code, 0)
            self.assertGreater(sys.stdout.getvalue(), "")
