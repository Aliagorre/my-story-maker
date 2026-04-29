class Mod:
    def on_load(self, core):
        core.register_service("styled_text", self)

    def on_init(self, core):
        pass

    def on_ready(self, event):
        pass

    def on_shutdown(self, core):
        pass

    COLORS = {
        "black": "30",
        "red": "31",
        "green": "32",
        "yellow": "33",
        "blue": "34",
        "magenta": "35",
        "cyan": "36",
        "white": "37",

        "bright_black": "90",
        "bright_red": "91",
        "bright_green": "92",
        "bright_yellow": "93",
        "bright_blue": "94",
        "bright_magenta": "95",
        "bright_cyan": "96",
        "bright_white": "97",
    }

    BACKGROUNDS = {
        "black": "40",
        "red": "41",
        "green": "42",
        "yellow": "43",
        "blue": "44",
        "magenta": "45",
        "cyan": "46",
        "white": "47",

        "bright_black": "100",
        "bright_red": "101",
        "bright_green": "102",
        "bright_yellow": "103",
        "bright_blue": "104",
        "bright_magenta": "105",
        "bright_cyan": "106",
        "bright_white": "107",
    }

    STYLES = {
        "bold": "1",
        "dim": "2",
        "italic": "3",
        "underline": "4",
        "blink": "5",
        "reverse": "7"
    }

    def style(self, text, color=None, bg=None, styles=None):
        codes = []

        if color in self.COLORS:
            codes.append(self.COLORS[color])

        if bg in self.BACKGROUNDS:
            codes.append(self.BACKGROUNDS[bg])

        if styles:
            for s in styles:
                if s in self.STYLES:
                    codes.append(self.STYLES[s])

        if not codes:
            return text

        return f"\033[{';'.join(codes)}m{text}\033[0m"

    def h1(self, text):
        return self.style(text.upper(), color="bright_blue", styles=["bold"])

    def h2(self, text):
        return self.style(text, color="bright_cyan", styles=["bold"])

    def h3(self, text):
        return self.style(text, color="cyan")

    def frame(self, text, style="simple"):
        lines = text.split("\n")
        width = max(len(l) for l in lines)

        if style == "simple":
            top = "┌" + "─" * width + "┐"
            bottom = "└" + "─" * width + "┘"
            body = [f"│{l.ljust(width)}│" for l in lines]

        elif style == "double":
            top = "╔" + "═" * width + "╗"
            bottom = "╚" + "═" * width + "╝"
            body = [f"║{l.ljust(width)}║" for l in lines]

        elif style == "ascii":
            top = "+" + "-" * width + "+"
            bottom = "+" + "-" * width + "+"
            body = [f"|{l.ljust(width)}|" for l in lines]

        else:
            return text

        return "\n".join([top] + body + [bottom])

    def bullet_list(self, items):
        return "\n".join(f" • {i}" for i in items)

    def numbered_list(self, items):
        return "\n".join(f" {idx+1}. {i}" for idx, i in enumerate(items))

    def blockquote(self, text):
        return "\n".join(f"│ {line}" for line in text.split("\n"))

    def code(self, text):
        return self.frame(text, style="ascii")

    def indent(self, text, level=1):
        prefix = "    " * level
        return "\n".join(prefix + l for l in text.split("\n"))
