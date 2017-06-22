import sys

from .meta import Command
from .. import db
from ..patch import _generate_patch

class diff(Command):

    name = "diff"
    help = "Show the diff that would be refreshed for the topmost patch."
    
    def run(self, args):
        applied = self.get_db()
        patch = db._get_top(applied)
        if sys.version_info.major >= 3:
            out = sys.stdout.buffer
        else:
            out = sys.stdout
        _generate_patch(self.get_cwd(),
            self.get_db(), self.get_patches_dir(), out, patch)
