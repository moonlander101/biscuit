from __future__ import annotations

import re
import tkinter as tk
import tkinter.font as tkfont
import typing

import tkextrafont as extra

from src.biscuit.common import ActionSet, extract_commands, formalize_command, get_games

from .bindings import Bindings
from .config import Config
from .resources import Resources
from .styles import Style

if typing.TYPE_CHECKING:
    from ... import App


URL = re.compile(r"^(?:http)s?:")


class Formattable(str):
    """For formatting github urls in the palette
    - If the term is a url, it will be returned as is
    - Otherwise, it will be formatted as a github url"""

    def format(self, term) -> str:
        default = "https://github.com/"
        if not term or URL.match(term):
            return super().format(term)

        return super().format(f"{default}{term}")


# TODO: functional settings editor
# TODO: load/store config in sqlite3 db
class Settings:
    """Settings for the application

    - Contains the configuration, style, resources, and bindings
    - Registers commands to the action set
    """

    def __init__(self, base: App) -> None:
        self.base = base

        self.config = Config(self)
        self.style = Style(self.base, self.config.theme)
        self.res = Resources(self)
        self.bindings = Bindings(self)

        self.commands = []

        self.setup_font()
        self.setup_icon()

    def register_command(self, command: str, callback: typing.Callable) -> None:
        """Registers a new palette command.

        Args:
            command (str): The command to be displayed.
            callback (typing.Callable): The callback function to be called.
        """
        self.commands.append((command, callback))
        self.generate_actionset()

    def generate_actionset(self) -> None:
        self._actionset = ActionSet(
            "Show and run commands", ">", self.commands + get_games(self.base)
        )

    def setup_icon(self) -> None:
        self.base.call(
            "wm",
            "iconphoto",
            self.base._w,
            tk.PhotoImage(file=self.res.get_res_path("icon.png")),
        )

    def setup_font(self) -> None:
        try:
            self.iconfont = extra.Font(
                file=self.res.get_res_path("codicon.ttf"), family="codicon"
            )
        except tk.TclError:
            pass

        self.font = tkfont.Font(family=self.config.font[0], size=self.config.font[1])
        self.font_bold = tkfont.Font(
            family=self.config.font[0], size=self.config.font[1], weight="bold"
        )
        self.autocomplete_font = tkfont.Font(
            family=self.config.font[0], size=self.config.font[1] - 1
        )
        self.uifont = tkfont.Font(
            family=self.config.uifont[0], size=self.config.uifont[1]
        )

    def late_setup(self) -> None:
        """Configurations that require full initialization of editor"""

        self.commands = [
            (
                formalize_command(name),
                lambda _, method=method: method(self.base.commands),
            )
            for name, method in extract_commands(self.base.commands)
        ]

        self.generate_actionset()
        self.base.palette.register_actionset(lambda: self.actionset)

        clone_actionset = ActionSet(
            "Clone git repository",
            "clone:",
            pinned=[[Formattable("clone {}"), self.base.clone_repo]],
        )
        self.base.palette.register_actionset(lambda: clone_actionset)

        self.symbols_actionset = ActionSet("Go to symbol in editor", "@", [])
        self.base.palette.register_actionset(lambda: self.symbols_actionset)

    @property
    def actionset(self):
        return self._actionset
