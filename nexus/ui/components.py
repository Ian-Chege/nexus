"""NEXUS SYSTEM MONITOR - reusable themed UI components.

Every component implements apply_theme(theme) so a theme switch recolors the
entire application instantly without rebuilding anything.
"""
from __future__ import annotations

import customtkinter as ctk

from ..theme import Theme


class StatCard(ctk.CTkFrame):
    """Big-number card with title, subtitle and an optional progress bar."""

    def __init__(self, master, theme: Theme, fonts, title: str, bar: bool = True, **kw):
        super().__init__(master, fg_color=theme.card, corner_radius=14,
                         border_width=1, border_color=theme.border, **kw)
        self._theme = theme
        self._fonts = fonts
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.title_lbl = ctk.CTkLabel(self, text=title.upper(), anchor="w",
                                      font=fonts["tiny"], text_color=theme.muted)
        self.title_lbl.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 0))
        self.value_lbl = ctk.CTkLabel(self, text="-", anchor="w",
                                      font=fonts["value"], text_color=theme.text)
        self.value_lbl.grid(row=1, column=0, sticky="ew", padx=16, pady=(2, 0))
        self.sub_lbl = ctk.CTkLabel(self, text=" ", anchor="w", justify="left",
                                    font=fonts["small"], text_color=theme.muted,
                                    wraplength=220)
        self.sub_lbl.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 4))
        if bar:
            self.bar = ctk.CTkProgressBar(self, height=6, corner_radius=3,
                                          fg_color=theme.track,
                                          progress_color=theme.accent)
            self.bar.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 14))
            self.bar.set(0)
        else:
            self.bar = None

    def set(self, value: str, sub: str = " ", ratio=None, color: str | None = None):
        t = self._theme
        self.value_lbl.configure(text=value, text_color=color or t.text)
        self.sub_lbl.configure(text=sub or " ")
        if self.bar is not None:
            self.bar.set(0.0 if ratio is None else max(0.0, min(1.0, float(ratio))))
            self.bar.configure(progress_color=color or t.accent)

    def apply_theme(self, theme: Theme):
        self._theme = theme
        self.configure(fg_color=theme.card, border_color=theme.border)
        self.title_lbl.configure(text_color=theme.muted)
        self.value_lbl.configure(text_color=theme.text)
        self.sub_lbl.configure(text_color=theme.muted)
        if self.bar is not None:
            self.bar.configure(fg_color=theme.track)


class InfoCard(ctk.CTkFrame):
    """Compact card: small title, medium value, optional sub-line."""

    def __init__(self, master, theme: Theme, fonts, title: str, **kw):
        super().__init__(master, fg_color=theme.card, corner_radius=14,
                         border_width=1, border_color=theme.border, **kw)
        self._theme = theme
        self.grid_columnconfigure(0, weight=1)
        self.title_lbl = ctk.CTkLabel(self, text=title.upper(), anchor="w",
                                      font=fonts["tiny"], text_color=theme.muted)
        self.title_lbl.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 0))
        self.value_lbl = ctk.CTkLabel(self, text="-", anchor="w",
                                      font=fonts["h2"], text_color=theme.text)
        self.value_lbl.grid(row=1, column=0, sticky="ew", padx=14, pady=(1, 0))
        self.sub_lbl = ctk.CTkLabel(self, text=" ", anchor="w", justify="left",
                                    font=fonts["small"], text_color=theme.muted,
                                    wraplength=250)
        self.sub_lbl.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 10))

    def set(self, value: str, sub: str = " ", color: str | None = None):
        self.value_lbl.configure(text=value, text_color=color or self._theme.text)
        self.sub_lbl.configure(text=sub or " ")

    def apply_theme(self, theme: Theme):
        self._theme = theme
        self.configure(fg_color=theme.card, border_color=theme.border)
        self.title_lbl.configure(text_color=theme.muted)
        self.value_lbl.configure(text_color=theme.text)
        self.sub_lbl.configure(text_color=theme.muted)


class SectionTitle(ctk.CTkFrame):
    """Uppercase section heading with a short neon underline."""

    def __init__(self, master, theme: Theme, fonts, text: str, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self._theme = theme
        self.lbl = ctk.CTkLabel(self, text=text.upper(), anchor="w",
                                font=fonts["h3"], text_color=theme.text)
        self.lbl.pack(anchor="w")
        self.rule = ctk.CTkFrame(self, height=3, width=34, corner_radius=2,
                                 fg_color=theme.accent)
        self.rule.pack(anchor="w", pady=(4, 0))

    def apply_theme(self, theme: Theme):
        self._theme = theme
        self.lbl.configure(text_color=theme.text)
        self.rule.configure(fg_color=theme.accent)


class MiniTable(ctk.CTkFrame):
    """Lightweight text table (header row + N data rows)."""

    def __init__(self, master, theme: Theme, fonts,
                 columns: list[tuple[str, str]], row_height: int = 22, **kw):
        # columns: [(title, "w"/"e" anchor), ...]
        super().__init__(master, fg_color="transparent", **kw)
        self._theme = theme
        self._fonts = fonts
        self._anchors = [a for _t, a in columns]
        n = len(columns)
        for i in range(n):
            self.grid_columnconfigure(i, weight=1, uniform="tbl")
        self._head = []
        for i, (title, _a) in enumerate(columns):
            lbl = ctk.CTkLabel(self, text=title.upper(), anchor="w",
                               font=fonts["tiny"], text_color=theme.muted)
            lbl.grid(row=0, column=i, sticky="ew", pady=(0, 2))
            self._head.append(lbl)
        self._rows: list[list[ctk.CTkLabel]] = []
        self._nrows = 0

    def set_rows(self, rows: list[tuple[str, ...]]):
        t = self._theme
        for r, row in enumerate(rows, start=1):
            if r > self._nrows:
                cell_lbls = []
                for i in range(len(self._anchors)):
                    lbl = ctk.CTkLabel(self, text="-", anchor=self._anchors[i],
                                       font=self._fonts["mono_small"],
                                       text_color=t.text)
                    lbl.grid(row=r, column=i, sticky="ew", pady=0)
                    cell_lbls.append(lbl)
                self._rows.append(cell_lbls)
            for i in range(len(self._anchors)):
                self._rows[r - 1][i].configure(
                    text=row[i] if i < len(row) else "-",
                    text_color=t.text if r % 2 else t.muted)

    def apply_theme(self, theme: Theme):
        self._theme = theme
        for lbl in self._head:
            lbl.configure(text_color=theme.muted)
        for r, cells in enumerate(self._rows, start=1):
            for lbl in cells:
                lbl.configure(text_color=theme.text if r % 2 else theme.muted)


class KeyRow(ctk.CTkFrame):
    """'Label ..... value' row used in detail panels."""

    def __init__(self, master, theme: Theme, fonts, label: str, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self._theme = theme
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.key = ctk.CTkLabel(self, text=label.upper(), anchor="w",
                                font=fonts["small"], text_color=theme.muted)
        self.key.grid(row=0, column=0, sticky="w")
        self.val = ctk.CTkLabel(self, text="-", anchor="e",
                                font=fonts["mono_small"], text_color=theme.text)
        self.val.grid(row=0, column=1, sticky="e")

    def set(self, text: str, color: str | None = None):
        self.val.configure(text=text, text_color=color or self._theme.text)

    def apply_theme(self, theme: Theme):
        self._theme = theme
        self.key.configure(text_color=theme.muted)
        self.val.configure(text_color=theme.text)


class CoreBar(ctk.CTkFrame):
    """Per-core usage bar: 'C0' label + progress bar."""

    def __init__(self, master, theme: Theme, fonts, index: int, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self._theme = theme
        self.grid_columnconfigure(1, weight=1)
        lbl = ctk.CTkLabel(self, text=f"C{index}", width=30, anchor="w",
                           font=fonts["mono_small"], text_color=theme.muted)
        lbl.grid(row=0, column=0, sticky="w")
        self.bar = ctk.CTkProgressBar(self, height=10, corner_radius=5,
                                      fg_color=theme.track,
                                      progress_color=theme.accent)
        self.bar.grid(row=0, column=1, sticky="ew", padx=(4, 8))
        self.pct = ctk.CTkLabel(self, text="0%", width=42, anchor="e",
                                font=fonts["mono_small"], text_color=theme.text)
        self.pct.grid(row=0, column=2, sticky="e")
        self.bar.set(0)

    def set(self, value: float, color: str):
        self.bar.set(max(0.0, min(1.0, value / 100.0)))
        self.bar.configure(progress_color=color)
        self.pct.configure(text=f"{value:.0f}%", text_color=color)

    def apply_theme(self, theme: Theme):
        self._theme = theme
        for child in (self.bar,):
            child.configure(fg_color=theme.track)


class ThemeCard(ctk.CTkFrame):
    """Clickable theme swatch: name + three color dots, outlined when active."""

    def __init__(self, master, fonts, theme_def: Theme, active: bool, command, **kw):
        super().__init__(master, corner_radius=12, cursor="hand2", **kw)
        self.theme_def = theme_def
        self._fonts = fonts
        self._current: Theme | None = None
        self._command = command

        self.name_lbl = ctk.CTkLabel(self, text=theme_def.name, anchor="w",
                                     font=fonts["small"], text_color="#FFFFFF")
        self.name_lbl.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        self.grid_columnconfigure(0, weight=1)

        dots = ctk.CTkFrame(self, fg_color="transparent")
        dots.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 10))
        for color, border in ((theme_def.accent, None),
                              (theme_def.accent2, None),
                              (theme_def.bg, theme_def.border)):
            dot = ctk.CTkFrame(dots, width=16, height=16, corner_radius=8,
                               fg_color=color,
                               border_color=border or color, border_width=1)
            dot.pack(side="left", padx=(0, 6))
        self.bind("<Button-1>", lambda _e: self._command())
        self.name_lbl.bind("<Button-1>", lambda _e: self._command())
        self._active = False
        self.set_active(active, force=True)

    def set_active(self, active: bool, force: bool = False):
        if self._active == active and not force:
            return
        self._active = active
        t = self._current or self.theme_def
        if active:
            self.configure(border_width=2, border_color=t.accent,
                           fg_color=t.card)
            self.name_lbl.configure(text_color=t.accent)
        else:
            self.configure(border_width=1, border_color=t.border,
                           fg_color=t.card)
            self.name_lbl.configure(text_color=t.text)

    def apply_theme(self, theme: Theme):
        self._current = theme
        self.configure(fg_color=theme.card,
                       border_color=theme.accent if self._active else theme.border)
        self.name_lbl.configure(text_color=theme.accent if self._active else theme.text)


class Toast(ctk.CTkFrame):
    """Non-blocking notification card placed bottom-right over the UI."""

    WIDTH = 330

    def __init__(self, master, theme: Theme, fonts, title: str, message: str,
                 color: str, on_dismiss, **kw):
        super().__init__(master, width=self.WIDTH, height=84, corner_radius=12,
                         fg_color=theme.card, border_width=1,
                         border_color=color, **kw)
        self._on_dismiss = on_dismiss
        self._color = color
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 0))
        head.grid_columnconfigure(0, weight=1)
        self.title_lbl = ctk.CTkLabel(head, text=title, anchor="w",
                                      font=fonts["small_bold"],
                                      text_color=color)
        self.title_lbl.grid(row=0, column=0, sticky="w")
        close = ctk.CTkButton(head, text="\u00d7", width=24, height=24,
                              corner_radius=6, fg_color="transparent",
                              hover_color=theme.track, border_width=0,
                              text_color=theme.muted,
                              font=fonts["small_bold"],
                              command=self.dismiss)
        close.grid(row=0, column=1, sticky="e")

        self.msg_lbl = ctk.CTkLabel(self, text=message, anchor="w", justify="left",
                                    wraplength=self.WIDTH - 56,
                                    font=fonts["small"], text_color=theme.text)
        self.msg_lbl.grid(row=1, column=0, sticky="ew", padx=14, pady=(2, 10))

        self.place(relx=1.0, rely=0.0, x=-24, y=-200, anchor="ne")
        self._slide_in()

    # -- animation ---------------------------------------------------------
    def _slide_in(self):
        target_y = None          # computed by the app on relayout
        self._anim_y = 40
        self._animate()

    def _animate(self):
        self._anim_y *= 0.6
        if self._anim_y < 1:
            self._anim_y = 0
        self._apply_position()
        if self._anim_y > 0:
            self.after(16, self._animate)

    def _apply_position(self):
        # the app recomputes 'y' for stacking; we just add the animation offset
        info = getattr(self, "_stack_y", None)
        if info is None:
            return
        self.place_configure(y=info + self._anim_y)

    def set_stack_y(self, y: int):
        self._stack_y = y
        self._apply_position()

    def dismiss(self):
        try:
            self._on_dismiss(self)
        except Exception:
            pass
