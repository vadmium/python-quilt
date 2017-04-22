# vim: fileencoding=utf-8 et sw=4 ts=4 tw=80:

# python-quilt - A Python implementation of the quilt patch system
#
# Copyright (C) 2012 - 2017 Björn Ricks <bjoern.ricks@gmail.com>
#
# See LICENSE comming with the source of python-quilt for details.

from errno import EEXIST, ENOENT
import os
import os.path
from shutil import copyfileobj
from tempfile import NamedTemporaryFile

from quilt.error import QuiltError
from quilt.utils import Process, DirectoryParam, _EqBase, File, FileParam, \
                        SubprocessError


class Patch(_EqBase):

    """ Wrapper around the patch util """

    def __init__(self, patch_name, strip=1, reverse=False):
        """
        strip: May be an integer or a decimal string.
        """
        self.patch_name = patch_name
        self.strip = strip
        self.reverse = reverse

    def run(self, patch_dir=".", backup=None,
            work_dir=".", dry_run=False,
            quiet=False, suppress_output=False):
        """
        patch_dir: Base directory of the patch file.
        backup: Directory to hold backups.
        work_dir: Source tree to be patched.
        """
        # TODO: handle missing newline at EOF case
        if self.reverse:
            cmd.append("-R")

        name = os.path.join(patch_dir, self.get_name())
        _patch_tree(name, work_dir, strip=int(self.strip), dry_run=dry_run,
            backup=backup,
        )

    def get_name(self):
        return self.patch_name

    @DirectoryParam(["patch_dir"])
    def get_header(self, patch_dir=None):
        """ Returns bytes """
        lines = []

        if patch_dir:
            file = patch_dir + File(self.get_name())
            name = file.get_name()
        else:
            name = self.get_name()
        with _Parser(name) as parser:
            for line in parser:
                if parser.get_index() or parser.get_filename():
                    break
                lines.append(line)

        return b"".join(lines)

    def __eq__(self, other):
        return (isinstance(other, Patch) and self.get_name() ==
                other.get_name())

    def __hash__(self):
        return hash(self.get_name())

    def __str__(self):
        return self.get_name()

    def __repr__(self):
        return "<Patch(%r, %r, %r) id=0x%0x>" % (self.get_name(), self.strip,
                                                 self.reverse, id(self))


class RollbackPatch(object):

    @DirectoryParam(["cwd", "backup_dir"])
    def __init__(self, cwd, backup_dir):
        self.cwd = cwd
        self.backup_dir = backup_dir

    def rollback(self, keep=False):
        (dirs, files) = self.backup_dir.content()

        for dir in dirs:
            newdir = self.cwd + dir
            if not newdir.exists():
                newdir.create()

        for file in files:
            file = File(file)
            backup_file = self.backup_dir + file
            rollback_file = self.cwd + file

            if not keep:
                rollback_file.delete_if_exists()
            if not backup_file.is_empty():
                backup_file.copy(rollback_file)

    def delete_backup(self):
        self.backup_dir.delete()


class Diff(object):
    """ Wrapper around the diff util
    """

    @FileParam(["left", "right"])
    def __init__(self, left, right):
        """ left points to the first file and right to the second file
        """
        self.left = left
        if not self.left.exists():
            self.left = File("/dev/null")

        self.right = right
        if not self.right.exists():
            self.right = File("/dev/null")

    def run(self, cwd, left_label=None, right_label=None, unified=True,
            fd=None):
        cmd = ["diff"]

        if unified:
            cmd.append("-u")

        if left_label:
            cmd.append("--label")
            cmd.append(left_label)

        if right_label:
            if not left_label:
                cmd.append("--label")
                cmd.append(self.right.get_name())
            cmd.append("--label")
            cmd.append(right_label)

        cmd.append(self.left.get_name())
        cmd.append(self.right.get_name())

        try:
            Process(cmd).run(cwd=cwd, stdout=fd)
        except SubprocessError as e:
            if e.get_returncode() > 1:
                raise e

    def equal(self, cwd):
        """ Returns True if left and right are equal
        """
        cmd = ["diff"]
        cmd.append("-q")
        cmd.append(self.left.get_name())
        cmd.append(self.right.get_name())

        try:
            Process(cmd).run(cwd=cwd, suppress_output=True)
        except SubprocessError as e:
            if e.get_returncode() == 1:
                return False
            else:
                raise e
        return True


class _Parser:
    def __init__(self, name):
        self._f = open(name, "rb")
        self._lines = iter(self._f)
        self._index = None
        self._src_exists = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self._f.close()
    
    def __iter__(self):
        for self._line in self._lines:
            yield self._line
    
    def get_index(self):
        if not self._line.startswith(b"Index:"):
            return False
        
        line = _strip_newline(self._line)
        prefix = b"Index: "
        if not line.startswith(prefix):
            raise QuiltError("Invalid patch index line")
        self._index = line[len(prefix):]
        return True
    
    def get_filename(self):
        if not self._line.startswith(b"---"):
            return None
        
        line = _strip_newline(self._line)
        prefix = b"--- "
        if not line.startswith(prefix):
            raise QuiltError("Invalid source filename line")
        [src, sep, line] = line[len(prefix):].partition(b"\t")
        self._src_exists = src != b"/dev/null"
        
        try:
            line = _strip_newline(next(self._lines))
        except StopIteration:
            raise QuiltError("Truncated filename information")
        prefix = b"+++ "
        if not line.startswith(prefix):
            raise QuiltError("Invalid destination filename line")
        [dest, sep, line] = line[len(prefix):].partition(b"\t")
        self._dest_exists = dest != b"/dev/null"
        
        if self._index is not None:
            filename = self._index
            self._index = None
        elif self._src_exists:
            filename = src
        else:
            filename = dest
        try:  # Python 3
            filename = os.fsdecode(filename)
        except AttributeError:  # Python < 3
            pass
        if filename.startswith("/"):
            raise QuiltError("Absolute filename in patch")
        filename = filename.replace(os.sep, "/")
        return (filename.split("/"), self._src_exists, self._dest_exists)
    
    def get_range(self):
        if self._src_exists is None:
            return None  # No filename information seen yet
        prefix = b"@@ -"
        if not self._line.startswith(prefix):
            return None
        
        [src, line] = self._line[len(prefix):].split(b" +", 1)
        [src_begin, self._src_count] = _parse_range(src, self._src_exists)
        [dest, line] = line.split(b" ", 1)
        [dest_begin, self._dest_count] = \
            _parse_range(dest, self._dest_exists)
        return (src_begin, self._src_count, dest_begin, self._dest_count)
    
    def get_hunk_lines(self):
        while self._src_count or self._dest_count:
            try:
                line = next(self._lines)
            except StopIteration:
                raise QuiltError("Truncated patch hunk")
            stripped = _strip_newline(line)
            in_src = stripped[:1] in {b"", b" ", b"-"}
            in_dest = stripped[:1] in {b"", b" ", b"+"}
            if in_src:
                if self._src_count == 0:
                    raise QuiltError("Expected added line")
                self._src_count -= 1
            if in_dest:
                if self._dest_count == 0:
                    raise QuiltError("Expected deleted line")
                self._dest_count -= 1
            yield (in_src, in_dest, line[1:])


def _parse_range(range, exists):
    [begin, sep, count] = range.partition(b",")
    begin = int(begin)
    if sep:
        count = int(count)
    else:
        count = 1
    if not exists and count:
        raise QuiltError("Invalid line count for absent file")
    if count:
        begin -= 1
    if not exists and begin:
        raise QuiltError("Invalid beginning line number for absent file")
    return (begin, count)


def _strip_newline(line):
    if not line.endswith(b"\n"):
        raise QuiltError("Truncated line in patch file")
    line = line[:-1]
    if line.endswith(b"\r"):
        line = line[:-1]
    if b"\r" in line:
        raise QuiltError("Unexpected CR in patch file")
    return line


def _patch_tree(name, work_dir=".", strip=0, dry_run=False, backup=None):
    with _Parser(name) as parser:
        file = None
        try:
            for line in parser:
                if parser.get_index():
                    continue
                filename = parser.get_filename()
                if filename is not None:
                    if file:
                        file.finish()
                    [filename, src_exists, dest_exists] = filename
                    if len(filename) <= strip:
                        raise \
                            QuiltError("Not enough path components to strip")
                    filename = filename[strip:]
                    file = _FilePatcher(filename, src_exists, dest_exists,
                        work_dir=work_dir, dry_run=dry_run, backup=backup)
                    continue
                
                hunk = parser.get_range()
                if hunk is None:
                    continue
                [src_begin, src_count, dest_begin, dest_count] = hunk
                hunk = parser.get_hunk_lines()
                file.apply_hunk(src_begin, hunk)
            if file:
                file.finish()
        finally:
            if file:
                file.close()


class _FilePatcher:
    def __init__(self, filename, src_exists, dest_exists,
            work_dir=".", dry_run=False, backup=None):
        self._filename = os.path.join(work_dir, *filename)
        self._dest_exists = dest_exists
        
        if backup is not None:
            for i in range(len(filename) - 1):
                backup = os.path.join(backup, filename[i])
                try:
                    os.mkdir(backup)
                except OSError as err:
                    if err.errno != EEXIST:
                        raise
            backup = os.path.join(backup, filename[-1])
        if src_exists:
            try:
                if backup is None:
                    src_name = self._filename
                else:
                    os.rename(self._filename, backup)
                    src_name = backup
                self._src = open(src_name, "rb")
            except EnvironmentError as err:
                if err.errno != ENOENT:
                    raise
                raise Conflict(err)
        else:
            if os.path.exists(self._filename):
                raise Conflict("File already exists: " + self._filename)
            if backup is not None:
                with open(backup, "w"):
                    pass
            self._src = None
        self._src_lines = 0
        
        if self._dest_exists and not dry_run:
            if backup is None:
                self._dest = NamedTemporaryFile(delete=False,
                    dir=os.path.join(work_dir, *filename[:-1]),
                    prefix=filename[-1] + "~",
                )
                self._temp_dest = self._dest.name
            else:
                self._dest = open(self._filename, "w+b")
                self._temp_dest = None
        else:
            self._dest = None
    
    def apply_hunk(self, begin, hunk):
        if begin < self._src_lines:
            raise QuiltError("Source hunks out of order")
        if begin > self._src_lines and not self._dest_exists:
            raise QuiltError("Missing deleted lines")
        if self._src:
            src_line = self._src_lines
            src_pos = self._src.tell()
            if self._dest:
                dest_pos = self._dest.tell()
        try:
            for i in range(self._src_lines, begin):
                line = self._src.readline()
                if not line:
                    src_hunk_stop = None
                    raise Conflict("Source file too short")
                self._src_lines += 1
                if self._dest:
                    self._dest.write(line)
            if self._src:
                src_hunk_start = self._src.tell()
                if self._dest:
                    dest_hunk_start = self._dest.tell()
            for [in_src, in_dest, line] in hunk:
                if in_src:
                    src_hunk_stop = self._src.tell()
                    if self._src.readline() != line:
                        raise Conflict("Source line mismatch")
                    self._src_lines += 1
                if in_dest and self._dest:
                    self._dest.write(line)
        except Conflict:
            if not self._dest_exists:
                raise
            
            self._src.seek(src_pos)
            src = b"\n" + self._src.read()  # Newline helps find whole lines
            
            begin_pos = 0
            try:
                for i in range(begin - src_line):
                    begin_pos = src.index(b"\n", begin_pos + 1)
            except ValueError:
                begin_pos = len(src) - 1
            
            if src_hunk_stop is None:
                src_hunk = bytearray(b"\n")  # Newline sentinel
            else:
                src_hunk_start -= src_pos
                src_hunk_stop -= src_pos
                src_hunk = bytearray(src[src_hunk_start : 1 + src_hunk_stop])
                src_hunk.extend(line)
            size = self._dest.tell() - dest_hunk_start
            self._dest.seek(dest_hunk_start)
            dest_hunk = bytearray(self._dest.read(size))
            for [in_src, in_dest, line] in hunk:
                if in_src:
                    src_hunk.extend(line)
                if in_dest:
                    dest_hunk.extend(line)
            self._src_lines = src_line + src_hunk.count(b"\n", 1)
            
            forward = src.find(src_hunk, begin_pos)
            backward = src.rfind(src_hunk, 0, begin_pos + 1)
            if forward < 0 and backward < 0:
                raise Conflict("Source hunk not found")
            if backward < 0 or forward >= 0 \
                    and forward - begin_pos >= begin_pos - backward:
                found = forward
            else:
                found = backward
            
            intervening = src[1:found + 1]
            lines = intervening.count(b"\n")
            self._src_lines += lines
            self._src.seek(src_pos + found + len(src_hunk))
            if self._dest:
                self._dest.seek(dest_pos)
                self._dest.write(intervening)
                self._dest.write(dest_hunk)
    
    def finish(self):
        if self._src:
            if self._dest:
                copyfileobj(self._src, self._dest)
            if not self._dest_exists and self._src.read(1):
                raise Conflict("Extra data in deleted file")
            self._src.close()
        if self._dest:
            self._dest.truncate()
            self._dest.close()
            if self._temp_dest is not None:
                if self._src:
                    os.remove(self._filename)
                    self._dest = None
                os.rename(self._temp_dest, self._filename)
                self._dest = None
    
    def close(self):
        if self._src:
            self._src.close()
        if self._dest:
            self._dest.close()
            if self._temp_dest is not None:
                os.remove(self._temp_dest)


class Conflict(QuiltError):
    pass
