# mods/simple_ui/pygame_renderer.py
#
# Primitives de rendu pygame.
# Ne connaît ni le moteur ni ui_core.
# Tout ce qui touche à pygame est ici — simple_ui/mod.py n'importe
# jamais pygame directement.

import pygame


# ── Thème ─────────────────────────────────────────────────────────

DEFAULT_THEME = {
    "bg":             (13,  13,  23),
    "header_bg":      (20,  20,  40),
    "header_fg":      (200, 200, 255),
    "title_fg":       (160, 140, 255),
    "text_fg":        (215, 215, 215),
    "choice_bg":      (22,  22,  45),
    "choice_hover":   (45,  45,  85),
    "choice_active":  (60,  60, 110),
    "choice_fg":      (180, 210, 255),
    "choice_index":   ( 90, 140, 255),
    "status_bg":      ( 8,   8,  18),
    "status_fg":      ( 60,  60,  80),
    "border":         ( 35,  35,  60),
    "message_ok_bg":  ( 15,  45,  15),
    "message_ok_fg":  (100, 210, 100),
    "message_err_bg": ( 50,  15,  15),
    "message_err_fg": (210, 100, 100),
    "scrollbar":      ( 35,  35,  60),
    "scrollbar_thumb":( 80,  80, 120),
    "key_hint_fg":    ( 70, 100, 160),
    "window_title_bg":( 18,  18,  38),
    "overlay":        (  0,   0,   0, 160),   # RGBA
}

FONT_MONO = None    # résolu dans init_fonts()

# ── Initialisation ────────────────────────────────────────────────

def init_fonts(size_normal: int = 15, size_title: int = 17,
               size_small: int = 12) -> dict:
    """
    Retourne un dict de polices.
    Appelé une seule fois après pygame.init().
    """
    candidates = ["JetBrains Mono", "Consolas", "Courier New",
                  "DejaVu Sans Mono", "monospace"]
    font_name = None
    for name in candidates:
        if name in pygame.font.get_fonts() or name == "monospace":
            font_name = name
            break

    return {
        "normal": pygame.font.SysFont(font_name, size_normal),
        "title":  pygame.font.SysFont(font_name, size_title, bold=True),
        "bold":   pygame.font.SysFont(font_name, size_normal, bold=True),
        "small":  pygame.font.SysFont(font_name, size_small),
    }


# ── Utilitaires ───────────────────────────────────────────────────

def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """Découpe le texte en lignes tenant dans max_width pixels."""
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        words = paragraph.split()
        current: list[str] = []
        for word in words:
            test = " ".join(current + [word])
            if font.size(test)[0] <= max_width:
                current.append(word)
            else:
                if current:
                    lines.append(" ".join(current))
                current = [word]
        lines.append(" ".join(current))
    return lines or [""]


def draw_rect(surface, color, rect, radius: int = 0,
              border_color=None, border_width: int = 1) -> None:
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border_color:
        pygame.draw.rect(surface, border_color, rect,
                         border_width, border_radius=radius)


def draw_text(surface, font, text: str, color, x: int, y: int,
              max_width: int | None = None) -> pygame.Rect:
    """Rend une ligne de texte. Tronque si max_width est fourni."""
    if max_width:
        while text and font.size(text)[0] > max_width:
            text = text[:-1]
    surf = font.render(text, True, color)
    surface.blit(surf, (x, y))
    return surf.get_rect(topleft=(x, y))


# ── Composants ────────────────────────────────────────────────────

class ScrollableText:
    """
    Zone de texte scrollable.
    Instanciée par fenêtre (garde l'offset de scroll).
    """

    def __init__(self):
        self._offset: int = 0   # offset en lignes

    def reset(self) -> None:
        self._offset = 0

    def scroll(self, delta: int, total_lines: int, visible_lines: int) -> None:
        max_off = max(0, total_lines - visible_lines)
        self._offset = max(0, min(self._offset + delta, max_off))

    def draw(self, surface: pygame.Surface, text: str,
             font: pygame.font.Font, color,
             rect: pygame.Rect, theme: dict) -> None:
        """Dessine le texte dans rect avec scroll. Gère la scrollbar."""
        PAD    = 8
        lines  = wrap_text(text, font, rect.width - PAD * 2 - 10)
        line_h = font.get_linesize()
        vis_n  = max(1, (rect.height - PAD * 2) // line_h)

        max_off = max(0, len(lines) - vis_n)
        self._offset = min(self._offset, max_off)

        # Clip
        surface.set_clip(rect)

        y = rect.top + PAD
        for line in lines[self._offset: self._offset + vis_n]:
            if y + line_h > rect.bottom:
                break
            surf = font.render(line, True, color)
            surface.blit(surf, (rect.left + PAD, y))
            y += line_h

        surface.set_clip(None)

        # Scrollbar
        if max_off > 0:
            sb_x  = rect.right - 6
            sb_h  = rect.height
            th_h  = max(20, int(sb_h * vis_n / max(len(lines), 1)))
            th_y  = rect.top + int((sb_h - th_h) * self._offset / max_off)
            pygame.draw.rect(surface, theme["scrollbar"],
                             (sb_x, rect.top, 5, sb_h), border_radius=2)
            pygame.draw.rect(surface, theme["scrollbar_thumb"],
                             (sb_x, th_y, 5, th_h), border_radius=2)


class WindowPanel:
    """
    Panneau d'une fenêtre UI.
    Gère l'affichage du titre, du contenu texte, et d'une image optionnelle.
    """

    def __init__(self, theme: dict, fonts: dict):
        self.theme      = theme
        self.fonts      = fonts
        self._scroll    = ScrollableText()

    def reset_scroll(self) -> None:
        self._scroll.reset()

    def scroll(self, delta: int) -> None:
        # delta est en lignes ; ScrollableText a besoin du nb total/visible
        # → on stocke le delta et on l'applique au prochain draw()
        self._pending_scroll = getattr(self, "_pending_scroll", 0) + delta

    def draw(self, surface: pygame.Surface,
             rect: pygame.Rect,
             title: str,
             content: str,
             image: pygame.Surface | None = None) -> None:
        T = self.theme
        F = self.fonts
        PAD = 10

        draw_rect(surface, T["bg"], rect)
        draw_rect(surface, T["border"], rect, border_color=T["border"])

        y = rect.top

        # Titre de panneau
        if title:
            title_rect = pygame.Rect(rect.left, y, rect.width, 28)
            draw_rect(surface, T["window_title_bg"], title_rect)
            draw_text(surface, F["bold"], title, T["title_fg"],
                      rect.left + PAD, y + 6,
                      max_width=rect.width - PAD * 2)
            pygame.draw.line(surface, T["border"],
                             (rect.left, y + 28), (rect.right, y + 28), 1)
            y += 30

        # Image (future extension)
        if image:
            img_rect = image.get_rect(topleft=(rect.left + PAD, y + PAD))
            img_rect.width  = min(img_rect.width,  rect.width  - PAD * 2)
            img_rect.height = min(img_rect.height, rect.height // 3)
            surface.blit(pygame.transform.scale(image, img_rect.size),
                         img_rect.topleft)
            y += img_rect.height + PAD

        # Texte scrollable
        text_rect = pygame.Rect(rect.left, y, rect.width, rect.bottom - y)

        # Appliquer le scroll en attente
        pending = getattr(self, "_pending_scroll", 0)
        if pending:
            lines  = wrap_text(content, F["normal"], text_rect.width - 26)
            vis_n  = max(1, (text_rect.height - 16) // F["normal"].get_linesize())
            self._scroll.scroll(pending, len(lines), vis_n)
            self._pending_scroll = 0

        self._scroll.draw(surface, content, F["normal"],
                          T["text_fg"], text_rect, T)


class ChoiceBar:
    """
    Barre de choix en bas de l'écran.
    Gère hover, active, et navigation clavier.
    """

    def __init__(self, theme: dict, fonts: dict):
        self.theme       = theme
        self.fonts       = fonts
        self._rects: list[tuple[pygame.Rect, int]] = []
        self.hovered     = -1
        self.active      = -1

    CHOICE_H   = 38
    CHOICE_GAP = 4
    PAD        = 16

    def height(self, n_choices: int) -> int:
        if n_choices == 0:
            return 0
        return n_choices * (self.CHOICE_H + self.CHOICE_GAP) + self.PAD * 2 + 1

    def draw(self, surface: pygame.Surface,
             choices: list[dict],
             rect: pygame.Rect,
             selected: int = -1) -> None:
        T = self.theme
        F = self.fonts

        if not choices:
            return

        pygame.draw.line(surface, T["border"],
                         (rect.left, rect.top),
                         (rect.right, rect.top), 1)

        self._rects.clear()
        for i, choice in enumerate(choices):
            cy   = rect.top + self.PAD + i * (self.CHOICE_H + self.CHOICE_GAP)
            r    = pygame.Rect(rect.left + self.PAD, cy,
                               rect.width - self.PAD * 2, self.CHOICE_H)

            if i == self.active:
                bg = T["choice_active"]
            elif i == self.hovered or i == selected:
                bg = T["choice_hover"]
            else:
                bg = T["choice_bg"]

            draw_rect(surface, bg, r, radius=6,
                      border_color=T["border"])

            idx_s   = F["bold"].render(f" {i+1}.", True, T["choice_index"])
            label_s = F["normal"].render(choice.get("text", ""), True, T["choice_fg"])
            mid_y   = r.y + self.CHOICE_H // 2

            surface.blit(idx_s,   (r.x + 8, mid_y - idx_s.get_height() // 2))
            surface.blit(label_s, (r.x + 40, mid_y - label_s.get_height() // 2))

            self._rects.append((r, i))

    def update_hover(self, pos) -> None:
        self.hovered = -1
        for r, i in self._rects:
            if r.collidepoint(pos):
                self.hovered = i

    def set_active(self, pos) -> None:
        self.active = -1
        for r, i in self._rects:
            if r.collidepoint(pos):
                self.active = i

    def get_clicked(self, pos) -> int | None:
        self.active = -1
        for r, i in self._rects:
            if r.collidepoint(pos):
                return i
        return None


class StatusBar:
    def __init__(self, theme: dict, fonts: dict, height: int = 24):
        self.theme  = theme
        self.fonts  = fonts
        self.height = height

    def draw(self, surface: pygame.Surface,
             rect: pygame.Rect,
             message: str,
             hints: list[str]) -> None:
        T = self.theme
        draw_rect(surface, T["status_bg"], rect)
        pygame.draw.line(surface, T["border"],
                         (rect.left, rect.top), (rect.right, rect.top), 1)

        # Message temporaire à gauche
        if message:
            is_err = message.startswith("✗")
            fg  = T["message_err_fg"] if is_err else T["message_ok_fg"]
            draw_text(surface, self.fonts["small"], message, fg,
                      rect.left + 8, rect.top + 5)

        # Hints à droite
        hint_str = "  ".join(hints)
        s = self.fonts["small"].render(hint_str, True, T["key_hint_fg"])
        surface.blit(s, (rect.right - s.get_width() - 8, rect.top + 5))


class HeaderBar:
    def __init__(self, theme: dict, fonts: dict, height: int = 36):
        self.theme  = theme
        self.fonts  = fonts
        self.height = height

    def draw(self, surface: pygame.Surface,
             rect: pygame.Rect,
             adventure_name: str,
             screen_title: str,
             windows: list) -> None:
        T = self.theme
        draw_rect(surface, T["header_bg"], rect)
        pygame.draw.line(surface, T["border"],
                         (rect.left, rect.bottom),
                         (rect.right, rect.bottom), 1)

        # Nom de l'aventure à gauche
        draw_text(surface, self.fonts["title"], adventure_name,
                  T["header_fg"], rect.left + 12,
                  rect.top + rect.height // 2 - self.fonts["title"].get_height() // 2)

        # Onglets des fenêtres à droite
        x = rect.right - 8
        for win in reversed(windows):
            label = f" {win.title} " if win.title else f" {win.name} "
            s = self.fonts["small"].render(label, True,
                T["header_fg"] if win.visible else T["key_hint_fg"])
            x -= s.get_width() + 4
            bg = T["choice_hover"] if win.visible else T["header_bg"]
            draw_rect(surface, bg,
                      pygame.Rect(x - 2, rect.top + 6,
                                  s.get_width() + 4, rect.height - 12),
                      radius=4)
            surface.blit(s, (x, rect.top + rect.height // 2 - s.get_height() // 2))