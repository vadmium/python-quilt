# vim: fileencoding=utf-8 et sw=4 ts=4 tw=80:

# python-quilt - A Python implementation of the quilt patch system
#
# Copyright (C) 2012 - 2017 Björn Ricks <bjoern.ricks@gmail.com>
#
# See LICENSE comming with the source of python-quilt for details.

from quilt.cli.meta import Command
from quilt.delete import Delete

class delete(Command):

    params = dict(
        remove=dict(name="-r", help="Remove the deleted patch file from the " \
                                     "patches directory as well."),
        patch=dict(mutex_group="patch"),
        next=dict(name="-n", mutex_group="patch",
                          help="Delete the next patch after topmost, " \
                                      "rather than the specified or topmost " \
                                      "patch. Cannot be combined with the " \
                                      '"patch" parameter.'),
        backup=dict(name="--backup", help="Rename the patch file to patch~ " \
                                      "rather than deleting it. Ignored if " \
                                      "not used with `-r'."),
    )
    def run(self, patch=None, remove=False, next=False, backup=False):
        delete = Delete(self.get_cwd(), self.get_pc_dir(),
                        self.get_patches_dir())
        delete.deleted_patch.connect(self.deleted_patch)
        delete.deleting_patch.connect(self.deleting_patch)

        if next:
            delete.delete_next(remove, backup)
        else:
            delete.delete_patch(patch, remove, backup)

    def deleted_patch(self, patch):
        print("Removed patch %s" % patch.get_name())

    def deleting_patch(self, patch, applied):
        if applied:
            print("Removing currently applied patch %s" % patch.get_name())
        else:
            print("Removing patch %s" % patch.get_name())
