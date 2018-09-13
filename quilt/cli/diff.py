import os.path
import sys

from .meta import Command
from .parser import OptionArgument
from .. import db
from .. import patch
from ..utils import File, Directory
from ..utils import TmpDirectory

class diff(Command):

    name = "diff"
    help = "Show the diff that would be refreshed for the topmost patch."
    
    z = OptionArgument(action="store_true", help="""unrefreshed changes only,
        relative to the topmost patch""")
    
    def run(self, args):
        applied = self.get_db()
        target_patch = db._get_top(applied)
        if sys.version_info.major >= 3:
            out = sys.stdout.buffer
        else:
            out = sys.stdout
        cwd = self.get_cwd()
        if args.z:
            # Apply original patch in temporary tree; then diff from that
            with TmpDirectory(prefix="pquilt-") as base:
                # Copy patched files from .pc/ to base
                initial = Directory(self.get_pc_dir())
                initial += target_patch.get_name()
                files = initial.files()
                for name in files:
                    if name == ".timestamp":
                        continue
                    file = File(name)
                    (initial + file).copy(base + file)
                # TODO: tolerate missing patch file
                target_patch.run(force=True, cwd=None,
                    patch_dir=os.path.abspath(self.get_patches_dir()),
                    work_dir=base, no_backup_if_mismatch=True,
                    quiet=True,
                )
                for name in files:#TODO: new parameters for generate_patch
                    if name == ".timestamp":
                        continue
                    file = File(name)
                    old = base + file
                    [olabel, nlabel, index] = patch._get_labels(name,
                        old, file, cwd=cwd)
                    patch._write_index(out, index)
                    out.flush()
                    patch.Diff(old, file).run(cwd, olabel, nlabel)
        else:
            patch._generate_patch(cwd,
                self.get_db(), self.get_patches_dir(), out, target_patch)
