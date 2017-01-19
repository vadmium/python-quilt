# vim: fileencoding=utf-8 et sw=4 ts=4 tw=80:

# python-quilt - A Python implementation of the quilt patch system
#
# Copyright (C) 2012 - 2017 Björn Ricks <bjoern.ricks@gmail.com>
#
# See LICENSE comming with the source of python-quilt for details.

from __future__ import print_function

from argparse import ArgumentParser
import inspect
import os
import six
import sys

from quilt.db import Db, Series
from quilt.utils import _getargspec

command_map = dict()

def register_command(name, command_class):
    command_map[name] = command_class

def find_command(name):
    return command_map.get(name, None)

def list_commands():
    return sorted(command_map.items())


class CommandMetaClass(type):

    def __new__(meta, name, bases, dict):
        cls = type.__new__(meta, name, bases, dict)
        if cls.name is not None:
            register_command(cls.name, cls)
        return cls


@six.add_metaclass(CommandMetaClass)
class Command(object):

    """ Base class for CLI commands
    
    Each subclass defines a "run" method, whose signature determines the
    command-line parameters. Each parameter triggers a call to "Argument-
    Parser.add_argument". Some settings for each parameter are inferred from
    the signature.
    
    The parameter name is passed to "add_argument":
        param => add_argument("param")
    
    A default of False implies a flag:
        param=False => add_argument("--param", action="store_true")
    
    A single-letter option name implies one dash rather than two:
        x=False => add_argument("-x", action="store_true")
    
    Other default values are passed to "add_argument" and imply an optional
    positional parameter (unless it is a CLI option):
        param=default => add_argument("param", nargs="?", default=default)
    
    A "starred" parameter receives multiple values:
        *param => add_argument("param", nargs="*")
    
    The "add_argument" settings are overridden and further specified by
    setting up a "params" attribute of the Command subclass. This attribute
    is a mapping from parameter names to their settings. Each "params" value
    is a mapping holding the "add_argument" settings. The following settings
    are special:
    
    * name: The primary parameter name passed to "add_argument":
        name="alias" => add_argument("alias", dest="param")
        
        If the name starts with one or two dashes, the parameter is a CLI
        option rather than a positional parameter. Whether it is optional or
        mandatory depends if a default value is given:
            name="--param" =>
                add_argument("--param", default=. . .) or
                add_argument("--param", required=True)
    
    * short: Implies a CLI option with a single-letter alias:
        short="-x" => add_argument("-x", "--param")
    
    * mutex_group: Parameters that share the same mutex_group value are added
        to a common group created with "ArgumentParser.add_mutually_
        exclusive_group", rather than the main parser object.
    """
    
    patches_dir = "patches"
    pc_dir = ".pc"
    name = None
    params = dict()

    def parse(self, args):
        prog = "pquilt " + self.name
        parser = ArgumentParser(prog=prog, description=inspect.getdoc(self))
        
        details = dict(self.params)
        params = _getargspec(self.run)
        if params.defaults is None:
            defaults = ()
        else:
            defaults = params.defaults
        groups = dict()
        # Ignore the first parameter (self)
        for [i, dest] in enumerate(params.args[1:], 1 - len(params.args)):
            has_default = i >= -len(defaults)
            if has_default:
                default = defaults[i]
            else:
                default = None
            settings = dict(details.pop(dest, ()))
            try:
                short = (settings.pop("short"),)
            except LookupError:
                short = ()
            if default is False or short:
                if len(dest) == 1:
                    name = "-" + dest
                else:
                    name = "--" + dest
            else:
                name = dest
            if default is False:
                settings.setdefault("action", "store_true")
            name = settings.pop("name", name)
            if name.startswith("-"):
                settings["dest"] = dest
                if not has_default:
                    settings.setdefault("required", True)
            elif has_default:
                settings.setdefault("nargs", "?")
            try:
                g = settings.pop("mutex_group")
            except LookupError:
                group = parser
            else:
                try:
                    group = groups[g]
                except LookupError:
                    group = parser.add_mutually_exclusive_group()
                    groups[g] = group
            group.add_argument(*short + (name,), default=default, **settings)
        
        if params.varargs is not None:
            settings = dict(details.pop(params.varargs, ()))
            settings.setdefault("nargs", "*")
            parser.add_argument(params.varargs, **settings)
        assert not details
        
        kw = vars(parser.parse_args(args))
        pos = kw.pop(params.varargs, ())
        self.run(*pos, **kw)

    def get_patches_dir(self):
        patches_dir = os.environ.get("QUILT_PATCHES")
        if not patches_dir:
            patches_dir = self.patches_dir
        return patches_dir

    def get_pc_dir(self):
        pc_dir = os.environ.get("QUILT_PC")
        if not pc_dir:
            pc_dir = self.pc_dir
        return pc_dir

    def get_db(self):
        return Db(self.get_pc_dir())

    def get_series(self):
        return Series(self.get_patches_dir())

    def get_cwd(self):
        return os.getcwd()

    def exit_error(self, error, value=1):
        print(error, file=sys.stderr)
        sys.exit(value)
