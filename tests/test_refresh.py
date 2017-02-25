import os
from tempfile import TemporaryDirectory
from unittest import TestCase

from quilt.db import Db, Patch
from quilt.error import QuiltError
import quilt.refresh

class Test(TestCase):

    def test_refresh(self):
        with TemporaryDirectory() as dir:
            old_dir = os.getcwd()
            try:
                os.chdir(dir)
                db = Db(".pc")
                db.create()
                backup = os.path.join(".pc", "patch")
                os.mkdir(backup)
                with open(os.path.join(backup, "file"), "wb") as backup:
                    pass
                db.add_patch(Patch("patch"))
                db.save()
                with open("patch", "wb") as file:
                    pass
                with open("file", "wb") as file:
                    file.write(b"added\n")
                cmd = quilt.refresh.Refresh(".", ".pc", ".")
                cmd.refresh()
                with open("patch", "r") as patch:
                    self.assertTrue(patch.read(30))
            finally:
                os.chdir(old_dir)
