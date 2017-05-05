from helpers import make_file, QuiltTest, run_cli, tmp_series
import os.path
from quilt.db import Db

from quilt.cli import patchimport


class Test(QuiltTest):

    def test_patch_options(self):
        """ Import a patch with -p -R options """
        with tmp_series() as [dir, series]:
            applied = Db(os.path.join(dir, ".pc"))
            patch = os.path.join(dir, "test.patch")
            make_file(b"", patch)
            run_cli(patchimport.PatchImportCommand,
                dict(patchfile=[patch], patchname=None, p="0", R=True),
                series.dirname, applied.dirname)
            self.assert_series_lines(series, (b"test.patch -p0 -R",))
