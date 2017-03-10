# vim: fileencoding=utf-8 et sw=4 ts=4 tw=80:

# python-quilt - A Python implementation of the quilt patch system
#
# Copyright (C) 2012 - 2017 Björn Ricks <bjoern.ricks@gmail.com>
#
# See LICENSE comming with the source of python-quilt for details.

from argparse import ArgumentParser
import inspect
import os
import sys

from quilt.db import Db, Series

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


class Command(metaclass=CommandMetaClass):

    """ Base class for CLI commands
    
    Each subclass defines a "run" method, whose signature determines the
    command-line parameters. Each parameter triggers a call to "Argument-
    Parser.add_argument". Settings for each parameter are inferred from
    the signature.
    
    For positional parameters, the name is passed to "add_argument":
        param => add_argument("param")
    
    For keyword-only parameters, the name is converted to a CLI option:
        param => add_argument("--param", required=True)
        x => add_argument("-x", required=True)
    
    A keyword-only parameter with a default of False implies a flag:
        param=False => add_argument("--param", action="store_true")
    
    Other default values are passed to "add_argument" and either imply an
    optional positional parameter or cancel the "required" status of a CLI
    option:
        param=default =>
            add_argument("param", nargs="?", default=default) or
            add_argument("--param", default=default)
    
    A "starred" parameter receives multiple values:
        *param => add_argument("param", nargs="*")
    
    The "add_argument" settings are overridden and further specified by
    parameter annotations. Each annotation is a mapping holding the "add_
    argument" settings. The following settings are special:
    
    * name: The primary parameter name passed to "add_argument":
        param: dict(name="alias") => add_argument("alias", dest="param")
    
    * short: Implies a CLI option with a single-letter alias:
        param: dict(short="-x") => add_argument("-x", "--param")
    
    * mutex_group: Parameters that share the same mutex_group value are added
        to a common group created with "ArgumentParser.add_mutually_
        exclusive_group", rather than the main parser object.
    """
    
    patches_dir = "patches"
    pc_dir = ".pc"
    name = None

    def parse(self, args):
        prog = "pquilt " + self.name
        parser = ArgumentParser(prog=prog, description=inspect.getdoc(self))
        
        pos = None
        pos_kinds = {inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD}
        groups = dict()
        for param in inspect.signature(self.run).parameters.values():
            if param.annotation is inspect.Parameter.empty:
                settings = dict()
            else:
                settings = dict(param.annotation)
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
            if param.kind in pos_kinds:
                if param.default is not inspect.Parameter.empty:
                    settings.setdefault("nargs", "?")
                group.add_argument(param.name, default=param.default,
                    **settings)
                continue
            if param.kind == inspect.Parameter.VAR_POSITIONAL:
                settings.setdefault("nargs", "*")
                pos = param.name
                group.add_argument(pos, **settings)
                continue
            if param.kind == inspect.Parameter.KEYWORD_ONLY:
                try:
                    short = (settings.pop("short"),)
                except LookupError:
                    short = ()
                if len(param.name) == 1:
                    name = "-" + param.name
                else:
                    name = "--" + param.name
                name = settings.pop("name", name)
                if param.default is False:
                    settings.setdefault("action", "store_true")
                elif param.default is inspect.Parameter.empty:
                    settings.setdefault("required", True)
                group.add_argument(*short, name,
                    dest=param.name, default=param.default, **settings)
                continue
            assert False
        
        kw = vars(parser.parse_args(args))
        pos = kw.pop(pos, ())
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
