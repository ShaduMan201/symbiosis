"""
visualization.py — Symbiosis: The Iterated Prisoner's Dilemma
=============================================================
A polished UI with relative layout positioning, Main Menu tooltips,
1v1 Faceoff with specific playback controls, and a Tournament Mode
featuring an evolutionary cycle and a Live Leaderboard.
Now includes Tournament Setup for initial populations and NOISE injection.
"""

import pygame
import sys
import math
import random
import wave
import struct
import io
from typing import List

from agents import (
    TitForTat, Grudger, Pavlov, GenerousTitForTat, TitForTwoTats,
    SuspiciousTitForTat, Detective, Gradual, SoftMajority, AlwaysCooperate, AlwaysDefect,
    COOPERATE, DEFECT, REWARD, TEMPTATION, SUCKER, PUNISHMENT,
)
from agents import Random as RandomBot

# ── Globals & Palette ────────────────────────────────────────────────────────
# Relative resolution scaled down further to accommodate smaller screens/taskbars
W, H = 1100, 720
FPS = 60

BG_DARK = (15, 20, 25)
BG_PANEL = (25, 30, 40)
BG_CARD = (35, 45, 60)
BG_ACTIVE = (55, 70, 95)
TEXT_WHITE = (245, 250, 255)
TEXT_DIM = (150, 160, 180)
TEXT_MUTED = (90, 100, 120)

C_NICE_1 = (16, 185, 129)
C_NICE_2 = (56, 189, 248)
C_NICE_3 = (134, 239, 172)
C_NICE_4 = (20, 184, 166)
C_NICE_5 = (163, 230, 53)
C_NICE_6 = (14, 165, 233)
C_NASTY_1 = (239, 68, 68)
C_NASTY_2 = (249, 115, 22)
C_NASTY_3 = (244, 63, 94)
C_NASTY_4 = (217, 70, 239)
C_NEUT_1 = (168, 85, 247)
C_NEUT_2 = (156, 163, 175)

C_CLR = (52, 211, 153)
D_CLR = (244, 63, 94)
GOLD = (251, 191, 36)

STRATEGY_META = [
    (AlwaysCooperate,     "AC",  "Always Cooperate", C_NICE_1, "The Dove. Unconditionally cooperative."),
    (AlwaysDefect,        "AD",  "Always Defect",    C_NASTY_1, "The Hawk. Unconditionally predatory."),
    (TitForTat,           "TfT", "Tit-for-Tat",      C_NICE_2, "The Reactive Strategist. Mirrors your last move."),
    (Grudger,             "GRD", "The Grudger",      C_NASTY_2, "Unforgiving. Betray it once, it defects forever."),
    (Pavlov,              "PAV", "Pavlov",           C_NEUT_1, "Win-Stay, Lose-Shift. Highly adaptive."),
    (GenerousTitForTat,   "GTf", "Generous TfT",     C_NICE_3, "Like TfT, but randomly forgives 10% of defections."),
    (TitForTwoTats,       "T2T", "Tit-for-Two-Tats", C_NICE_4, "Extremely tolerant. Waits for 2 defections to retaliate."),
    (SuspiciousTitForTat, "STf", "Suspicious TfT",   C_NASTY_3, "Like TfT but opens with a Defection."),
    (Detective,           "DET", "The Detective",    C_NASTY_4, "Probes for 4 rounds. Exploits unretaliating foes."),
    (Gradual,             "GRA", "Gradual",          C_NICE_6, "Escalating punishment for every defection."),
    (SoftMajority,        "SMJ", "Soft Majority",    C_NICE_5, "Cooperates if your historical coop rate is >50%."),
    (RandomBot,           "RND", "True Random",      C_NEUT_2, "Pure chaos. Flips a coin every round."),
]

ROUNDS_PER_GEN = 200

fonts = {}

_PAY = {
    (COOPERATE, COOPERATE): (REWARD, REWARD),
    (COOPERATE, DEFECT):    (SUCKER, TEMPTATION),
    (DEFECT,    COOPERATE): (TEMPTATION, SUCKER),
    (DEFECT,    DEFECT):    (PUNISHMENT, PUNISHMENT),
}

# ── Audio ────────────────────────────────────────────────────────────────────
def make_sound(freq, duration, volume=0.1, wave_type='sine'):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        for i in range(n_samples):
            t = float(i) / sample_rate
            env = 1.0
            if t < 0.05: env = t / 0.05
            elif t > duration - 0.05: env = (duration - t) / 0.05
            if wave_type == 'sine':
                v = int(volume * env * 32767 * math.sin(2 * math.pi * freq * t))
            else:
                v = int(volume * env * 32767 * (1 if math.sin(2 * math.pi * freq * t) > 0 else -1))
            w.writeframesraw(struct.pack('<h', v))
    buf.seek(0)
    return pygame.mixer.Sound(buf)

# ── UI Utilities ─────────────────────────────────────────────────────────────
def draw_rounded_rect(surf, color, rect, radius=8, width=0):
    pygame.draw.rect(surf, color, rect, border_radius=radius, width=width)

class Button:
    def __init__(self, x, y, w, h, text, color=BG_PANEL, hover=BG_ACTIVE, text_color=TEXT_WHITE, font_k='md_b'):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color, self.hover = color, hover
        self.text_color = text_color
        self.font_k = font_k

    def draw(self, surf):
        hov = self.rect.collidepoint(pygame.mouse.get_pos())
        c = self.hover if hov else self.color
        draw_rounded_rect(surf, c, self.rect, radius=8)
        txt = fonts[self.font_k].render(self.text, True, self.text_color if not hov else TEXT_WHITE)
        surf.blit(txt, txt.get_rect(center=self.rect.center))

    def clicked(self, ev):
        return ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and self.rect.collidepoint(ev.pos)

class Slider:
    def __init__(self, x, y, w, h, min_v, max_v, init_v, label, is_pct=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_v, self.max_v = min_v, max_v
        self.val = init_v
        self.label = label
        self.is_pct = is_pct
        self.drag = False

    def draw(self, surf):
        draw_rounded_rect(surf, BG_CARD, self.rect, radius=self.rect.h//2)
        pct = (self.val - self.min_v) / (self.max_v - self.min_v)
        fw = int(self.rect.w * pct)
        if fw > 0:
            draw_rounded_rect(surf, GOLD, pygame.Rect(self.rect.x, self.rect.y, fw, self.rect.h), radius=self.rect.h//2)
        pygame.draw.circle(surf, TEXT_WHITE, (self.rect.x + fw, self.rect.centery), self.rect.h)
        
        disp = f"{int(self.val*100)}%" if self.is_pct else f"{self.val:.1f}x"
        txt = fonts['sm'].render(f"{self.label}: {disp}", True, TEXT_WHITE)
        surf.blit(txt, (self.rect.x, self.rect.y - 20))

    def handle(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and self.rect.collidepoint(ev.pos):
            self.drag = True; self._upd(ev.pos[0]); return True
        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            self.drag = False
        elif ev.type == pygame.MOUSEMOTION and self.drag:
            self._upd(ev.pos[0]); return True
        return False

    def _upd(self, mx):
        rel = max(0, min(self.rect.w, mx - self.rect.x))
        nv = self.min_v + (rel / self.rect.w) * (self.max_v - self.min_v)
        if nv < 0.005 and self.is_pct: nv = 0.0
        self.val = nv

def draw_face(surf, cx, cy, radius, color, state="IDLE"):
    pygame.draw.circle(surf, color, (int(cx), int(cy)), radius)
    pygame.draw.circle(surf, BG_DARK, (int(cx), int(cy)), radius, max(2, radius//8))
    
    eye_r = max(2, radius // 5)
    ex, ey = radius // 2.5, radius // 4
    
    if state == "IDLE":
        pygame.draw.circle(surf, BG_DARK, (int(cx - ex), int(cy - ey)), eye_r)
        pygame.draw.circle(surf, BG_DARK, (int(cx + ex), int(cy - ey)), eye_r)
        mw = radius // 2
        pygame.draw.line(surf, BG_DARK, (cx - mw//2, cy + radius//3), (cx + mw//2, cy + radius//3), max(2, radius//10))
    elif state == "COOP":
        hw = eye_r * 1.5
        pygame.draw.arc(surf, BG_DARK, (cx - ex - hw/2, cy - ey - hw/2, hw, hw), 0, math.pi, max(2, radius//10))
        pygame.draw.arc(surf, BG_DARK, (cx + ex - hw/2, cy - ey - hw/2, hw, hw), 0, math.pi, max(2, radius//10))
        sm_w = radius * 0.8
        pygame.draw.arc(surf, BG_DARK, pygame.Rect(cx - sm_w/2, cy, sm_w, sm_w/1.5), math.pi, math.pi*2, max(3, radius//8))
    elif state == "DEFECT":
        pygame.draw.line(surf, BG_DARK, (cx - ex*1.5, cy - ey*1.5), (cx - ex*0.5, cy - ey*0.5), max(3, radius//8))
        pygame.draw.line(surf, BG_DARK, (cx + ex*1.5, cy - ey*1.5), (cx + ex*0.5, cy - ey*0.5), max(3, radius//8))
        sm_w = radius * 0.6
        pygame.draw.arc(surf, BG_DARK, pygame.Rect(cx - sm_w/2, cy + radius//4, sm_w, sm_w/2), 0, math.pi, max(3, radius//8))

# ── Tournament Agent ─────────────────────────────────────────────────────────
class TAgent:
    def __init__(self, meta_idx):
        self.cls, self.abbr, self.name, self.color, self.desc = STRATEGY_META[meta_idx]
        self.meta_idx = meta_idx
        self.agent = self.cls()
        self.score = 0
        self.x = random.uniform(W*0.05, W*0.55)
        self.y = random.uniform(H*0.15, H*0.85)
        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(-1, 1)
        self.state = "IDLE"  # IDLE, DEAD, CLONE
        self.alpha = 255

    def update(self, dt):
        if self.state == "IDLE":
            self.x += self.vx * 30 * dt
            self.y += self.vy * 30 * dt
            if self.x < W*0.05: self.vx *= -1; self.x = W*0.05
            if self.x > W*0.55: self.vx *= -1; self.x = W*0.55
            if self.y < H*0.15: self.vy *= -1; self.y = H*0.15
            if self.y > H*0.85: self.vy *= -1; self.y = H*0.85

    def draw(self, surf):
        r = int(H * 0.015)
        if self.state == "DEAD":
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            draw_face(s, r, r, r, (100,100,100, self.alpha))
            surf.blit(s, (self.x-r, self.y-r))
        elif self.state == "CLONE":
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            c = (*self.color, self.alpha)
            draw_face(s, r, r, r, c)
            pygame.draw.circle(s, GOLD, (r,r), r, 2)
            surf.blit(s, (self.x-r, self.y-r))
        else:
            draw_face(surf, self.x, self.y, r, self.color)

# ── Application ──────────────────────────────────────────────────────────────
class App:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        pygame.display.set_caption("Symbiosis: The Iterated Prisoner's Dilemma")
        self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()
        self.t = 0.0

        fonts['xl'] = pygame.font.SysFont("Segoe UI", int(H*0.055), bold=True)
        fonts['lg'] = pygame.font.SysFont("Segoe UI", int(H*0.028), bold=True)
        fonts['md_b'] = pygame.font.SysFont("Segoe UI", int(H*0.02), bold=True)
        fonts['md'] = pygame.font.SysFont("Segoe UI", int(H*0.018))
        fonts['sm'] = pygame.font.SysFont("Segoe UI", int(H*0.015), bold=True)
        fonts['xs'] = pygame.font.SysFont("Segoe UI", int(H*0.013))

        self.snd_ping = make_sound(880, 0.1, 0.1, 'sine')
        self.snd_thud = make_sound(150, 0.2, 0.15, 'square')

        self.state = "MENU" # MENU, FACEOFF_SEL, FACEOFF, TOURN_SEL, TOURNAMENT
        
        # General Buttons
        self.btn_back = Button(W*0.02, H*0.03, W*0.08, H*0.045, "<- BACK", BG_CARD)
        
        # Menu
        self.btn_f_mode = Button(W*0.3, H*0.75, W*0.15, H*0.08, "FACEOFF", C_NICE_4, text_color=BG_DARK)
        self.btn_t_mode = Button(W*0.55, H*0.75, W*0.15, H*0.08, "TOURNAMENT", C_NASTY_2, text_color=BG_DARK)

        # Global Setup Sliders (Pushing Noise slider down & right to prevent overlap)
        self.sl_noise = Slider(W*0.35, H*0.77, W*0.3, 10, 0.0, 0.50, 0.05, "Noise (Miscommunication Risk)", is_pct=True)

        # Faceoff Select
        self.fo_sel_A = None
        self.fo_sel_B = None
        # Push buttons down slightly more and center them alongside slider if needed
        self.btn_fo_start = Button(W*0.4, H*0.88, W*0.2, H*0.05, "START MATCH", GOLD, text_color=BG_DARK)
        
        # Faceoff Arena
        self.fo_round = 0
        self.fo_anim_t = 0.0
        self.fo_speed = 1.0
        self.fo_paused = False
        self.fo_history = []
        
        self.btn_s_dn = Button(W*0.35, H*0.15, W*0.03, H*0.04, "-", BG_CARD)
        self.btn_s_up = Button(W*0.62, H*0.15, W*0.03, H*0.04, "+", BG_CARD)
        self.btn_fo_play = Button(W*0.4, H*0.15, W*0.08, H*0.04, "PAUSE", BG_CARD)
        self.btn_fo_ff = Button(W*0.5, H*0.15, W*0.1, H*0.04, "FAST FWD >>", BG_CARD)

        # Tournament Setup
        self.tourn_counts = {i: 5 for i in range(12)} # Standard 60 total
        # Adjusting Tournament Setup buttons to be more compact vertically
        self.btn_t_setup_min = [Button(W*0.55, H*0.23 + i*H*0.042, W*0.03, H*0.03, "-", BG_CARD) for i in range(12)]
        self.btn_t_setup_add = [Button(W*0.65, H*0.23 + i*H*0.042, W*0.03, H*0.03, "+", BG_CARD) for i in range(12)]
        self.btn_t_start = Button(W*0.4, H*0.88, W*0.2, H*0.05, "START TOURNAMENT", GOLD, text_color=BG_DARK)

        # Tournament
        self.pop = []
        self.tourn_gen = 1
        self.tourn_tstate = "PLAYING"
        self.tourn_timer = 0.0
        self.tombstones = []
        self.btn_t_ff = Button(W*0.77, H*0.03, W*0.1, H*0.04, "NEXT GEN >>", BG_CARD)
        self.btn_t_finish = Button(W*0.89, H*0.03, W*0.09, H*0.04, "FINISH", C_NASTY_1, text_color=BG_DARK)
        self.btn_main_menu = Button(W*0.4, H*0.86, W*0.2, H*0.08, "MAIN MENU", GOLD, text_color=BG_DARK)

    # ── States ───────────────────────────────────────────────────────────────
    def _draw_menu(self):
        self.screen.fill(BG_DARK)
        
        tt = fonts['xl'].render("Symbiosis: The Iterated Prisoner's Dilemma", True, TEXT_WHITE)
        st = fonts['lg'].render("An interactive evolutionary experiment decoding the math of trust.", True, TEXT_DIM)
        self.screen.blit(tt, tt.get_rect(center=(W//2, H*0.1)))
        self.screen.blit(st, st.get_rect(center=(W//2, H*0.16)))
        
        mx, my = pygame.mouse.get_pos()
        # Changed cols from 4 to 3 so 12 icons fit in a 3x4 grid centered nicely
        box_w, box_h = int(W*0.18), int(H*0.08)
        cols = 3
        total_w = cols * box_w + (cols-1) * 20
        start_x = W//2 - total_w//2
        start_y = H * 0.28
        
        tooltip = None
        for i, (cls, ab, nm, clr, dsc) in enumerate(STRATEGY_META):
            x = start_x + (i % cols) * (box_w + 20)
            y = start_y + (i // cols) * (box_h + 20)
            r = pygame.Rect(x, y, box_w, box_h)
            
            draw_rounded_rect(self.screen, BG_PANEL, r, 12)
            draw_face(self.screen, x + box_h//2, y + box_h//2, box_h//3, clr)
            
            nt = fonts['md_b'].render(nm, True, TEXT_WHITE)
            self.screen.blit(nt, (x + box_h, y + box_h*0.2))
            at = fonts['xs'].render(ab, True, clr)
            self.screen.blit(at, (x + box_h, y + box_h*0.55))

            if r.collidepoint((mx, my)):
                draw_rounded_rect(self.screen, clr, r, 12, 2)
                tooltip = (nm, dsc, clr)

        if tooltip:
            tr = pygame.Rect(mx + 15, my + 15, int(W*0.25), int(H*0.08))
            draw_rounded_rect(self.screen, BG_PANEL, tr, 8)
            pygame.draw.rect(self.screen, tooltip[2], tr, 2, 8)
            self.screen.blit(fonts['md_b'].render(tooltip[0], True, tooltip[2]), (tr.x+10, tr.y+10))
            self.screen.blit(fonts['sm'].render(tooltip[1], True, TEXT_WHITE), (tr.x+10, tr.y+H*0.04))

        self.btn_f_mode.draw(self.screen)
        self.btn_t_mode.draw(self.screen)

    # ── Faceoff Setup ────────────────────────────────────────────────────────
    def _draw_faceoff_select(self):
        self.screen.fill(BG_DARK)
        self.btn_back.draw(self.screen)
        tt = fonts['xl'].render("FACEOFF: Select Two Strategies", True, TEXT_WHITE)
        self.screen.blit(tt, tt.get_rect(center=(W//2, H*0.12)))

        mx, my = pygame.mouse.get_pos()
        cols = 6
        box_w = int(W*0.08)
        total_w = cols * box_w + (cols-1)*20
        start_x = W//2 - total_w//2
        start_y = H * 0.25
        
        for i, (cls, ab, nm, clr, dsc) in enumerate(STRATEGY_META):
            x = start_x + (i%cols)*(box_w+20)
            y = start_y + (i//cols)*(box_w+20)
            r = pygame.Rect(x, y, box_w, box_w)
            
            cbg = BG_PANEL
            if self.fo_sel_A == i or self.fo_sel_B == i:
                cbg = BG_ACTIVE
            
            draw_rounded_rect(self.screen, cbg, r, 12)
            if self.fo_sel_A == i and self.fo_sel_B == i:
                self.screen.blit(fonts['sm'].render("x2", True, GOLD), (r.x+8, r.y+8))
            elif self.fo_sel_A == i:
                self.screen.blit(fonts['sm'].render("P1", True, GOLD), (r.x+8, r.y+8))
            elif self.fo_sel_B == i:
                self.screen.blit(fonts['sm'].render("P2", True, GOLD), (r.x+8, r.y+8))

            draw_face(self.screen, r.centerx, r.y + box_w*0.4, box_w//4, clr)
            nt = fonts['sm'].render(ab, True, TEXT_WHITE)
            self.screen.blit(nt, nt.get_rect(center=(r.centerx, r.y + box_w*0.8)))

            if r.collidepoint((mx, my)) and getattr(self, "ev_click", False):
                if self.fo_sel_A == i and self.fo_sel_B == i:
                    self.fo_sel_B = None
                elif self.fo_sel_B == i:
                    self.fo_sel_B = None
                elif self.fo_sel_A == i and self.fo_sel_B is not None:
                    self.fo_sel_A = None
                elif self.fo_sel_A is None:
                    self.fo_sel_A = i
                elif self.fo_sel_B is None:
                    self.fo_sel_B = i

        self.sl_noise.draw(self.screen)

        if self.fo_sel_A is not None and self.fo_sel_B is not None:
            self.btn_fo_start.draw(self.screen)

    # ── Faceoff Arena ────────────────────────────────────────────────────────
    def _start_faceoff(self):
        m1 = STRATEGY_META[self.fo_sel_A]
        m2 = STRATEGY_META[self.fo_sel_B]
        self.charA = {'ag': m1[0](), 'col': m1[3], 'nm': m1[2], 'sc': 0, 'st': 'IDLE', 'act': None}
        self.charB = {'ag': m2[0](), 'col': m2[3], 'nm': m2[2], 'sc': 0, 'st': 'IDLE', 'act': None}
        self.fo_round = 0
        self.fo_anim_t = 0.0
        self.fo_history = [(0,0)]
        self.state = "FACEOFF"
        self.fo_paused = False

    def _play_fo_round(self):
        ia, ib = self.charA['ag'].choose_move(), self.charB['ag'].choose_move()
        # Evaluate Noise
        na = DEFECT if ia == COOPERATE and random.random() < self.sl_noise.val else ia
        nb = DEFECT if ib == COOPERATE and random.random() < self.sl_noise.val else ib
        
        self.charA['act'], self.charB['act'] = na, nb
        pa, pb = _PAY[(na, nb)]
        self.charA['ag'].record_round(na, nb, pa)
        self.charB['ag'].record_round(nb, na, pb)
        self.charA['sc'] += pa
        self.charB['sc'] += pb
        self.fo_history.append((self.charA['sc'], self.charB['sc']))
        
        if na == COOPERATE: self.snd_ping.play()
        else: self.snd_thud.play()
        if nb == COOPERATE: self.snd_ping.play()
        else: self.snd_thud.play()
        self.fo_round += 1

    def _draw_faceoff(self, dt):
        self.screen.fill(BG_DARK)
        self.btn_back.draw(self.screen)
        
        rd = fonts['xl'].render(f"ROUND {self.fo_round}/200", True, TEXT_WHITE)
        self.screen.blit(rd, rd.get_rect(center=(W//2, H*0.08)))

        self.btn_fo_play.text = "PLAY" if self.fo_paused else "PAUSE"
        self.btn_s_dn.draw(self.screen)
        self.btn_s_up.draw(self.screen)
        self.btn_fo_play.draw(self.screen)
        self.btn_fo_ff.draw(self.screen)
        
        spd = fonts['md_b'].render(f"Speed: {self.fo_speed:.1f}x", True, GOLD)
        self.screen.blit(spd, spd.get_rect(center=(W//2, H*0.22)))

        gx, gy, gw, gh = W*0.1, H*0.7, W*0.8, H*0.2
        draw_rounded_rect(self.screen, BG_PANEL, pygame.Rect(gx, gy, gw, gh), 8)
        pygame.draw.line(self.screen, BG_CARD, (gx, gy+gh//2), (gx+gw, gy+gh//2), 2)
        
        if len(self.fo_history) > 1:
            ptsA, ptsB = [], []
            max_sc = max(10, max(max(a, b) for a, b in self.fo_history))
            for i, (sa, sb) in enumerate(self.fo_history):
                px = gx + (i / 200) * gw
                ptsA.append((px, gy + gh - (sa/max_sc)*gh))
                ptsB.append((px, gy + gh - (sb/max_sc)*gh))
            if len(ptsA) > 1: pygame.draw.lines(self.screen, self.charA['col'], False, ptsA, 3)
            if len(ptsB) > 1: pygame.draw.lines(self.screen, self.charB['col'], False, ptsB, 3)

        ax, ay = W*0.25, H*0.45
        bx, by = W*0.75, H*0.45
        
        if not self.fo_paused and self.fo_round < ROUNDS_PER_GEN:
            self.fo_anim_t += dt * self.fo_speed * 2.0
            if self.fo_anim_t > 2.0:
                self.fo_anim_t = 0.0
                self._play_fo_round()
            
            p = self.fo_anim_t
            move_dist = W*0.18
            if p < 0.5:
                ax += move_dist * (p/0.5)
                bx -= move_dist * (p/0.5)
                self.charA['st'] = 'IDLE'; self.charB['st'] = 'IDLE'
            elif p < 1.5:
                ax += move_dist; bx -= move_dist
                self.charA['st'] = "COOP" if self.charA.get('act')==COOPERATE else "DEFECT"
                self.charB['st'] = "COOP" if self.charB.get('act')==COOPERATE else "DEFECT"
            else:
                p2 = (p-1.5)/0.5
                ax = (W*0.25 + move_dist) - move_dist*p2
                bx = (W*0.75 - move_dist) + move_dist*p2
                
        r = int(H*0.08)
        draw_face(self.screen, ax, ay, r, self.charA['col'], self.charA['st'])
        draw_face(self.screen, bx, by, r, self.charB['col'], self.charB['st'])
        
        na = fonts['lg'].render(f"{self.charA['nm']}: {self.charA['sc']}", True, self.charA['col'])
        nb = fonts['lg'].render(f"{self.charB['nm']}: {self.charB['sc']}", True, self.charB['col'])
        self.screen.blit(na, na.get_rect(center=(W*0.25, ay + r + int(H*0.04))))
        self.screen.blit(nb, nb.get_rect(center=(W*0.75, by + r + int(H*0.04))))

        if 0.5 < self.fo_anim_t < 1.5 and self.charA.get('act'):
            cta = fonts['xl'].render(self.charA['act'], True, C_CLR if self.charA['act']==COOPERATE else D_CLR)
            ctb = fonts['xl'].render(self.charB['act'], True, C_CLR if self.charB['act']==COOPERATE else D_CLR)
            self.screen.blit(cta, cta.get_rect(center=(ax, ay - r - int(H*0.05))))
            self.screen.blit(ctb, ctb.get_rect(center=(bx, by - r - int(H*0.05))))

    # ── Tournament Setup ─────────────────────────────────────────────────────
    def _draw_tourn_select(self):
        self.screen.fill(BG_DARK)
        self.btn_back.draw(self.screen)
        
        tt = fonts['xl'].render("TOURNAMENT: Initial Population", True, TEXT_WHITE)
        self.screen.blit(tt, tt.get_rect(center=(W//2, H*0.12)))

        total_pop = sum(self.tourn_counts.values())
        lt = fonts['lg'].render(f"Total Agents: {total_pop}", True, GOLD)
        self.screen.blit(lt, lt.get_rect(center=(W//2, H*0.17)))

        for i, (cls, ab, nm, clr, dsc) in enumerate(STRATEGY_META):
            y = H*0.23 + i * H*0.042
            
            draw_face(self.screen, W*0.35, y + 15, 12, clr)
            nt = fonts['lg'].render(nm, True, TEXT_WHITE)
            self.screen.blit(nt, (W*0.38, y + 2))
            
            self.btn_t_setup_min[i].draw(self.screen)
            ct = fonts['lg'].render(str(self.tourn_counts[i]), True, GOLD)
            self.screen.blit(ct, ct.get_rect(center=(W*0.615, y + 17)))
            self.btn_t_setup_add[i].draw(self.screen)

        self.sl_noise.draw(self.screen)

        if total_pop >= 2:
            self.btn_t_start.draw(self.screen)

    # ── Tournament Arena ─────────────────────────────────────────────────────
    def _start_tournament(self):
        self.pop = []
        for i, count in self.tourn_counts.items():
            for _ in range(count):
                self.pop.append(TAgent(i))
        self.tourn_gen = 1
        self.tourn_tstate = "PLAYING"
        self.tourn_timer = 0.0
        self.tombstones = []
        self.state = "TOURNAMENT"
        self.tourn_math_queue = []
        self.tourn_math_total = 1
        self.tourn_total_points = {i: 0 for i in range(12)}

    def _draw_tournament(self, dt):
        self.screen.fill(BG_DARK)
        self.btn_back.draw(self.screen)
        self.btn_t_ff.draw(self.screen)
        self.btn_t_finish.draw(self.screen)
        
        sbx, sbw = W * 0.65, W * 0.32
        sby, sbh = H * 0.1, H * 0.85
        draw_rounded_rect(self.screen, BG_PANEL, pygame.Rect(sbx, sby, sbw, sbh), 16)
        
        gt = fonts['xl'].render(f"GENERATION {self.tourn_gen}", True, TEXT_WHITE)
        self.screen.blit(gt, gt.get_rect(center=(sbx + sbw//2, sby + H*0.05)))
        
        cx, cy, rad = sbx + sbw//2, sby + H*0.22, int(H*0.11)
        cnts = {i:0 for i in range(12)}
        for p in self.pop: cnts[p.meta_idx] += 1
        
        ang = -math.pi/2
        for i in range(12):
            c = cnts[i]
            if c == 0: continue
            swp = (c / len(self.pop)) * 2 * math.pi
            pts = [(cx,cy)]
            for s in range(max(3, int(swp*20))+1):
                a = ang + s*swp/max(3, int(swp*20))
                pts.append((cx + rad*math.cos(a), cy + rad*math.sin(a)))
            if len(pts)>2: pygame.draw.polygon(self.screen, STRATEGY_META[i][3], pts)
            ang += swp
        pygame.draw.circle(self.screen, BG_PANEL, (cx,cy), rad - int(H*0.03))

        lh = fonts['lg'].render("LEADERBOARD", True, GOLD)
        self.screen.blit(lh, lh.get_rect(center=(sbx + sbw//2, sby + H*0.4)))
        
        rankings = [(i, cnts[i], sum(p.score for p in self.pop if p.meta_idx == i)) for i in range(12)]
        rankings.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        ly = sby + H*0.45
        for idx, count, total_sc in rankings:
            if count > 0:
                cls, ab, nm, clr, _ = STRATEGY_META[idx]
                pygame.draw.circle(self.screen, clr, (sbx + 30, ly + 10), 8)
                lt = fonts['md_b'].render(f"{nm}: {count} reps", True, TEXT_WHITE)
                st = fonts['sm'].render(f"sc: {total_sc}", True, TEXT_DIM)
                self.screen.blit(lt, (sbx + 50, ly))
                self.screen.blit(st, (sbx + sbw - 120, ly+2))
                ly += H*0.032

        grid_r = pygame.Rect(W*0.05, H*0.1, W*0.55, H*0.85)
        draw_rounded_rect(self.screen, BG_PANEL, grid_r, 16, width=2)
        
        self.tourn_timer += dt
        
        if self.tourn_tstate == "PLAYING":
            for p in self.pop:
                p.state = "IDLE"; p.update(dt); p.draw(self.screen)
            for _ in range(10):
                if len(self.pop) > 1:
                    a, b = random.sample(self.pop, 2)
                    pygame.draw.line(self.screen, TEXT_WHITE, (a.x, a.y), (b.x, b.y), 1)
                
            tt = fonts['lg'].render(f"Observing Generation {self.tourn_gen}...", True, GOLD)
            self.screen.blit(tt, tt.get_rect(center=(grid_r.centerx, grid_r.bottom - H*0.08)))
            
            if self.tourn_timer > 2.0: 
                # Setup the Math Queue
                for p in self.pop: 
                    p.agent.reset()
                    p.score = 0
                self.tourn_math_queue = []
                N = len(self.pop)
                for i in range(N):
                    for j in range(i+1, N):
                        self.tourn_math_queue.append((self.pop[i], self.pop[j]))
                self.tourn_math_total = max(1, len(self.tourn_math_queue))
                
                self.tourn_tstate = "CALCULATING"
                self.tourn_timer = 0.0

        elif self.tourn_tstate == "CALCULATING":
            for p in self.pop:
                p.state = "IDLE"; p.update(dt*0.2); p.draw(self.screen)
                
            s = pygame.Surface((grid_r.w, grid_r.h), pygame.SRCALPHA)
            s.fill((15, 20, 25, 200))
            self.screen.blit(s, grid_r.topleft)

            chunk_size = max(1, self.tourn_math_total // 3) 
            nl = self.sl_noise.val
            
            for _ in range(chunk_size):
                if not self.tourn_math_queue: break
                a, b = self.tourn_math_queue.pop()
                for _ in range(ROUNDS_PER_GEN):
                    ma, mb = a.agent.choose_move(), b.agent.choose_move()
                    na = DEFECT if ma == COOPERATE and random.random() < nl else ma
                    nb = DEFECT if mb == COOPERATE and random.random() < nl else mb
                    pa, pb = _PAY[(na, nb)]
                    a.agent.record_round(na, nb, pa)
                    b.agent.record_round(nb, na, pb)
                    a.score += pa
                    b.score += pb
                    self.tourn_total_points[a.meta_idx] += pa
                    self.tourn_total_points[b.meta_idx] += pb

            tt = fonts['xl'].render(f"Evaluating Generation {self.tourn_gen}...", True, GOLD)
            self.screen.blit(tt, tt.get_rect(center=(grid_r.centerx, grid_r.centery - H*0.05)))
            
            calc_count = self.tourn_math_total - len(self.tourn_math_queue)
            st = fonts['lg'].render(f"{calc_count} / {self.tourn_math_total} Matches Simulated", True, TEXT_WHITE)
            self.screen.blit(st, st.get_rect(center=(grid_r.centerx, grid_r.centery + H*0.05)))

            if not self.tourn_math_queue:
                # If we hit FINISH, we might have set a forced overlay timer
                if getattr(self, 'tourn_finish_overlay_timer', 0) > 0:
                    self.tourn_finish_overlay_timer -= dt
                    if self.tourn_finish_overlay_timer <= 0:
                        self.state = "PODIUM"
                        self.tourn_timer = 0.0
                else:
                    self.tourn_tstate = "ELIMINATING"
                    self.tourn_timer = 0.0
                
        elif self.tourn_tstate == "ELIMINATING":
            self.pop.sort(key=lambda x: x.score)
            alp = max(0, 255 - int(255 * (self.tourn_timer / 2.0)))
            num_elim = max(1, len(self.pop)//10) if len(self.pop)//10 > 0 else 0
            for i in range(num_elim):
                self.pop[i].state = "DEAD"; self.pop[i].alpha = alp
            for p in self.pop: 
                if p.state != "DEAD": p.update(dt)
                p.draw(self.screen)
                
            tt = fonts['lg'].render(f"Eliminating Bottom 10%...", True, D_CLR)
            self.screen.blit(tt, tt.get_rect(center=(grid_r.centerx, grid_r.bottom - H*0.08)))
            
            if self.tourn_timer > 2.0:
                self.tourn_tstate = "REPLICATING"
                self.tourn_timer = 0.0
                
        elif self.tourn_tstate == "REPLICATING":
            alp = min(255, int(255 * (self.tourn_timer / 2.0)))
            num_elim = max(1, len(self.pop)//10) if len(self.pop)//10 > 0 else 0
            for i in range(num_elim):
                dead = self.pop[i]
                parent = self.pop[-(i+1)]
                if cnts[dead.meta_idx] == 1 and dead.meta_idx != parent.meta_idx:
                    self.tombstones.append({"txt": f"EXTINCT: {STRATEGY_META[dead.meta_idx][2]}", "t": 4.0})
                
                if dead.meta_idx != parent.meta_idx:
                    cnts[dead.meta_idx] -= 1
                    cnts[parent.meta_idx] += 1
                
                dead.state = "CLONE"; dead.alpha = alp
                if self.tourn_timer < 0.1:
                    dead.meta_idx = parent.meta_idx
                    dead.color = parent.color
                    dead.name = parent.name
                    dead.abbr = parent.abbr
                    dead.cls = parent.cls

            for p in self.pop: 
                if p.state != "CLONE": p.update(dt)
                p.draw(self.screen)
                
            tt = fonts['lg'].render(f"Replicating Top 10%...", True, C_CLR)
            self.screen.blit(tt, tt.get_rect(center=(grid_r.centerx, grid_r.bottom - H*0.08)))
            
            if self.tourn_timer > 2.0:
                self.tourn_gen += 1; self.tourn_tstate = "PLAYING"; self.tourn_timer = 0.0
                for p in self.pop: p.state = "IDLE"; p.agent = p.cls()

        # Tombstones
        ty = H*0.08
        for tb in self.tombstones[:]:
            tb['t'] -= dt
            if tb['t'] <= 0: self.tombstones.remove(tb)
            else:
                s = fonts['lg'].render(tb['txt'], True, D_CLR, BG_DARK)
                self.screen.blit(s, (grid_r.centerx - s.get_width()//2, ty))
                ty += H*0.06

    def _draw_podium(self, dt):
        self.screen.fill(BG_DARK)
        self.tourn_timer += dt
        tt = fonts['xl'].render("TOURNAMENT RESULTS", True, GOLD)
        self.screen.blit(tt, tt.get_rect(center=(W//2, H*0.1)))

        # Only rank strategies that participated initially!
        rankings = [(i, self.tourn_total_points[i]) for i in range(12) if self.tourn_counts[i] > 0]
        rankings.sort(key=lambda x: x[1], reverse=True)
        top3 = rankings[:3]

        if self.tourn_timer > 0.5 and len(top3) > 2:
            idx = top3[2][0]
            cls, ab, nm, clr, _ = STRATEGY_META[idx]
            draw_face(self.screen, W*0.25, H*0.6, int(H*0.1), clr)
            st = fonts['lg'].render("3rd Place", True, TEXT_DIM)
            self.screen.blit(st, st.get_rect(center=(W*0.25, H*0.75)))
            nt = fonts['lg'].render(nm, True, clr)
            self.screen.blit(nt, nt.get_rect(center=(W*0.25, H*0.8)))

        if self.tourn_timer > 1.0 and len(top3) > 1:
            idx = top3[1][0]
            cls, ab, nm, clr, _ = STRATEGY_META[idx]
            draw_face(self.screen, W*0.75, H*0.5, int(H*0.12), clr)
            st = fonts['lg'].render("2nd Place", True, TEXT_DIM)
            self.screen.blit(st, st.get_rect(center=(W*0.75, H*0.68)))
            nt = fonts['lg'].render(nm, True, clr)
            self.screen.blit(nt, nt.get_rect(center=(W*0.75, H*0.73)))

        if self.tourn_timer > 1.5 and len(top3) > 0:
            idx = top3[0][0]
            cls, ab, nm, clr, _ = STRATEGY_META[idx]
            draw_face(self.screen, W*0.5, H*0.4, int(H*0.15), clr)
            st = fonts['xl'].render("1st Place", True, GOLD)
            self.screen.blit(st, st.get_rect(center=(W*0.5, H*0.62)))
            nt = fonts['xl'].render(nm, True, clr)
            self.screen.blit(nt, nt.get_rect(center=(W*0.5, H*0.68)))

        if self.tourn_timer > 3.0:
            self.state = "TOURN_RESULTS"

    def _draw_tourn_results(self):
        self.screen.fill(BG_DARK)
        tt = fonts['xl'].render("Full Results Dashboard", True, GOLD)
        self.screen.blit(tt, tt.get_rect(center=(W//2, H*0.08)))

        cnts = {i:0 for i in range(12)}
        for p in self.pop: cnts[p.meta_idx] += 1

        rankings = [(i, cnts[i], self.tourn_total_points[i]) for i in range(12)]
        rankings.sort(key=lambda x: x[2], reverse=True)

        header_y = H*0.18
        self.screen.blit(fonts['md_b'].render("Strategy", True, TEXT_DIM), (W*0.25, header_y))
        self.screen.blit(fonts['md_b'].render("Initial Pop", True, TEXT_DIM), (W*0.5, header_y))
        self.screen.blit(fonts['md_b'].render("Final Pop", True, TEXT_DIM), (W*0.65, header_y))
        self.screen.blit(fonts['md_b'].render("Total Points", True, TEXT_DIM), (W*0.8, header_y))
        pygame.draw.line(self.screen, BG_CARD, (W*0.15, header_y+25), (W*0.9, header_y+25))

        y = header_y + 40
        for idx, f_pop, t_pts in rankings:
            cls, ab, nm, clr, _ = STRATEGY_META[idx]
            i_pop = self.tourn_counts[idx]
            
            draw_face(self.screen, W*0.2, y+10, int(H*0.025), clr)
            self.screen.blit(fonts['lg'].render(nm, True, clr), (W*0.24, y))
            self.screen.blit(fonts['lg'].render(str(i_pop), True, TEXT_WHITE), (W*0.53, y))
            self.screen.blit(fonts['lg'].render(str(f_pop), True, TEXT_WHITE), (W*0.68, y))
            self.screen.blit(fonts['lg'].render(str(t_pts), True, GOLD), (W*0.83, y))
            
            y += H*0.052

        self.btn_main_menu.draw(self.screen)

    # ── Main Loop ────────────────────────────────────────────────────────────
    def run(self):
        self.ev_click = False
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            self.t += dt
            self.ev_click = False
            
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    self.ev_click = True
                    
                if self.state == "MENU":
                    if self.btn_f_mode.clicked(ev): self.state = "FACEOFF_SEL"
                    if self.btn_t_mode.clicked(ev): self.state = "TOURN_SEL"
                    
                elif self.state == "FACEOFF_SEL":
                    if self.btn_back.clicked(ev): self.state = "MENU"; self.fo_sel_A = self.fo_sel_B = None
                    if self.fo_sel_A is not None and self.fo_sel_B is not None:
                        if self.btn_fo_start.clicked(ev): self._start_faceoff()
                    self.sl_noise.handle(ev)
                        
                elif self.state == "FACEOFF":
                    if self.btn_back.clicked(ev): self.state = "FACEOFF_SEL"
                    
                    if self.btn_s_dn.clicked(ev): self.fo_speed = max(0.5, self.fo_speed - 0.5)
                    if self.btn_s_up.clicked(ev): self.fo_speed = min(5.0, self.fo_speed + 0.5)
                    if self.btn_fo_play.clicked(ev): self.fo_paused = not self.fo_paused
                    if self.btn_fo_ff.clicked(ev):
                        self.fo_speed = 5.0
                        while self.fo_round < ROUNDS_PER_GEN:
                            self._play_fo_round()
                        self.fo_anim_t = 0.0

                elif self.state == "TOURN_SEL":
                    if self.btn_back.clicked(ev): self.state = "MENU"
                    self.sl_noise.handle(ev)
                    for i in range(12):
                        if self.btn_t_setup_min[i].clicked(ev):
                            self.tourn_counts[i] = max(0, self.tourn_counts[i] - 1)
                        if self.btn_t_setup_add[i].clicked(ev):
                            self.tourn_counts[i] += 1
                    if sum(self.tourn_counts.values()) >= 2:
                        if self.btn_t_start.clicked(ev): self._start_tournament()

                elif self.state == "TOURNAMENT":
                    if self.btn_back.clicked(ev): self.state = "TOURN_SEL"
                    if self.btn_t_finish.clicked(ev):
                        # Instantly crunch all remaining math in the current state
                        if self.tourn_tstate == "CALCULATING" or self.tourn_tstate == "PLAYING":
                            if self.tourn_tstate == "PLAYING":
                                for p in self.pop: 
                                    p.agent.reset()
                                    p.score = 0
                                self.tourn_math_queue = []
                                N = len(self.pop)
                                for i in range(N):
                                    for j in range(i+1, N):
                                        self.tourn_math_queue.append((self.pop[i], self.pop[j]))
                                self.tourn_math_total = max(1, len(self.tourn_math_queue))
                                self.tourn_tstate = "CALCULATING"

                            nl = self.sl_noise.val
                            while self.tourn_math_queue:
                                a, b = self.tourn_math_queue.pop()
                                for _ in range(ROUNDS_PER_GEN):
                                    ma, mb = a.agent.choose_move(), b.agent.choose_move()
                                    na = DEFECT if ma == COOPERATE and random.random() < nl else ma
                                    nb = DEFECT if mb == COOPERATE and random.random() < nl else mb
                                    pa, pb = _PAY[(na, nb)]
                                    a.agent.record_round(na, nb, pa)
                                    b.agent.record_round(nb, na, pb)
                                    a.score += pa
                                    b.score += pb
                                    self.tourn_total_points[a.meta_idx] += pa
                                    self.tourn_total_points[b.meta_idx] += pb
                            self.tourn_finish_overlay_timer = 2.0
                        else:
                            self.state = "PODIUM"
                            self.tourn_timer = 0.0

                    if self.btn_t_ff.clicked(ev):
                        if self.tourn_tstate == "PLAYING": self.tourn_timer = 4.0
                        elif self.tourn_tstate == "CALCULATING":
                            nl = self.sl_noise.val
                        
                elif self.state == "TOURN_RESULTS":
                    if self.btn_main_menu.clicked(ev):
                        self.state = "MENU"

            if self.state == "MENU": self._draw_menu()
            elif self.state == "FACEOFF_SEL": self._draw_faceoff_select()
            elif self.state == "FACEOFF": self._draw_faceoff(dt)
            elif self.state == "TOURN_SEL": self._draw_tourn_select()
            elif self.state == "TOURNAMENT": self._draw_tournament(dt)
            elif self.state == "PODIUM": self._draw_podium(dt)
            elif self.state == "TOURN_RESULTS": self._draw_tourn_results()

            pygame.display.flip()

if __name__ == "__main__":
    App().run()
