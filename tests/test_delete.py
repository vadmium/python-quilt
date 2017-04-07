import os, os.path
from quilt.db import Series
from quilt.patch import Patch
from quilt.utils import TmpDirectory
from six.moves import cStringIO
import sys

from helpers import QuiltTest, tmp_mapping

from quilt.delete import Delete
from quilt.cli.delete import DeleteCommand

class Test(QuiltTest):

    def test_next_first(self):
        """ Delete the next patch with only unapplied patches """
        with TmpDirectory() as dir:
            patches = Series(dir.get_name())
            patches.add_patch(Patch("patch"))
            patches.save()
            cmd = Delete(dir.get_name(), dir.get_name(), patches.dirname)
            cmd.delete_next()
            patches.read()
            self.assertTrue(patches.is_empty())
    
    def test_no_backup(self):
        """ Remove a patch without leaving a backup """
        with TmpDirectory() as dir:
            patches = Series(dir.get_name())
            patches.add_patch(Patch("patch"))
            patches.save()
            patch = os.path.join(dir.get_name(), "patch")
            with open(patch, "wb"):
                pass
            class options:
                next = True
                remove = True
                backup = False
            with tmp_mapping(os.environ) as env, \
                    tmp_mapping(vars(sys)) as tmp_sys:
                env.set("QUILT_PATCHES", patches.dirname)
                env.set("QUILT_PC", dir.get_name())
                tmp_sys.set("stdout", cStringIO())
                DeleteCommand().run(options, [])
            self.assertFalse(os.path.exists(patch))
            self.assertFalse(os.path.exists(patch + "~"))
