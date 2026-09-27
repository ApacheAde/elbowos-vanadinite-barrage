#!/usr/bin/env python3
"""Vanadinite Barrage — neon tower-lite arcade for ElbowOS."""
from __future__ import annotations

import math
import os
import random
import subprocess
import sys

import pygame

W, H = 1080, 1920
FPS = 30
TITLE = "VANADINITE BARRAGE"
HANDLE = "x.com/ElbowOS"
BG, INK, GOLD = (18, 6, 8), (255, 236, 214), (255, 196, 64)
EMBER, CRIMSON, COPPER = (255, 92, 36), (220, 36, 54), (196, 92, 48)
TEAL, LAVA, ASH = (48, 220, 196), (255, 140, 40), (52, 18, 22)
LANES = 5
LANE_X = [180, 360, 540, 720, 900]
BASE_Y = 1580
SPAWN_Y = 280


class Spark:
    __slots__ = ("x", "y", "vx", "vy", "life", "col", "r")

    def __init__(self, x, y, vx, vy, life, col, r=5):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life, self.col, self.r = life, col, r


class Drone:
    __slots__ = ("lane", "y", "hp", "kind", "wobble")

    def __init__(self, lane, kind):
        self.lane, self.y, self.kind = lane, SPAWN_Y, kind
        self.hp = 2 if kind == "heavy" else 1
        self.wobble = random.random() * 6.28


class Shell:
    __slots__ = ("x", "y", "tx", "ty", "t", "dur")

    def __init__(self, x, y, tx, ty):
        self.x, self.y, self.tx, self.ty = x, y, tx, ty
        dist = max(180.0, math.hypot(tx - x, ty - y))
        self.t, self.dur = 0.0, dist / 1400.0


class Game:
    def __init__(self, record: bool):
        self.record = record
        self.surf = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        self.font_lg = pygame.font.Font(None, 62)
        self.font_md = pygame.font.Font(None, 46)
        self.font_sm = pygame.font.Font(None, 32)
        self.reset()

    def reset(self) -> None:
        self.lane = 2
        self.score = 0
        self.lives = 3
        self.charge = 1.0
        self.cool = 0.0
        self.pulse = 0.0
        self.spawn_t = 0.2
        self.drones: list[Drone] = []
        self.shells: list[Shell] = []
        self.sparks: list[Spark] = []
        self.shake = 0.0
        self.over = False

    def burst(self, x, y, col, n=14) -> None:
        for _ in range(n):
            ang = random.random() * 6.283
            spd = random.uniform(80, 360)
            self.sparks.append(
                Spark(x, y, spd * math.cos(ang), spd * math.sin(ang),
                      random.uniform(0.25, 0.7), col, random.randint(3, 9))
            )

    def fire(self) -> None:
        if self.cool > 0 or self.over or self.charge < 0.25:
            return
        aim = self.pick_target()
        tx = LANE_X[aim]
        ty = next((d.y for d in self.drones if d.lane == aim), 520)
        sx, sy = LANE_X[self.lane], BASE_Y - 40
        self.shells.append(Shell(sx, sy, tx, ty - 10))
        self.burst(sx, sy, GOLD, 8)
        self.cool = 0.18
        self.charge = max(0.0, self.charge - 0.22)

    def pick_target(self) -> int:
        if not self.drones:
            return self.lane
        threat = max(self.drones, key=lambda d: d.y)
        return threat.lane

    def autoplay(self) -> None:
        if self.over:
            if self.cool <= 0:
                self.reset()
            return
        target = self.pick_target()
        if target < self.lane:
            self.lane -= 1
        elif target > self.lane:
            self.lane += 1
        if self.drones and self.charge > 0.35:
            self.fire()

    def update(self, dt: float) -> None:
        self.pulse += dt
        self.cool = max(0.0, self.cool - dt)
        self.shake = max(0.0, self.shake - dt)
        self.charge = min(1.0, self.charge + dt * 0.55)
        if self.record:
            self.autoplay()
        if not self.over:
            self.spawn_t -= dt
            if self.spawn_t <= 0:
                kind = "heavy" if random.random() < 0.22 else "scout"
                taken = {d.lane for d in self.drones if d.y < SPAWN_Y + 90}
                free = [i for i in range(LANES) if i not in taken] or list(range(LANES))
                self.drones.append(Drone(random.choice(free), kind))
                self.spawn_t = max(0.35, 0.95 - self.score * 0.001)
        speed = 118 + min(90, self.score * 0.08)
        keep = []
        for d in self.drones:
            d.y += speed * dt * (0.72 if d.kind == "heavy" else 1.0)
            d.wobble += dt * 4.0
            if d.y >= BASE_Y - 70:
                self.lives -= 1
                self.shake = 0.35
                self.burst(LANE_X[d.lane], BASE_Y - 40, CRIMSON, 18)
                if self.lives <= 0:
                    self.over = True
                    self.cool = 1.4
                continue
            keep.append(d)
        self.drones = keep
        live_shells = []
        for sh in self.shells:
            sh.t += dt / sh.dur
            if sh.t >= 1.0:
                self.impact(sh.tx, sh.ty)
            else:
                live_shells.append(sh)
        self.shells = live_shells
        alive = []
        for sp in self.sparks:
            sp.life -= dt
            if sp.life <= 0:
                continue
            sp.x += sp.vx * dt
            sp.y += sp.vy * dt
            sp.vy += 280 * dt
            alive.append(sp)
        self.sparks = alive

    def impact(self, x, y) -> None:
        self.burst(x, y, LAVA, 16)
        hit = []
        for d in self.drones:
            if abs(LANE_X[d.lane] - x) < 70 and abs(d.y - y) < 90:
                d.hp -= 1
                if d.hp <= 0:
                    self.score += 40 if d.kind == "heavy" else 20
                    self.burst(LANE_X[d.lane], d.y, TEAL if d.kind == "scout" else GOLD, 20)
                else:
                    hit.append(d)
                    self.score += 8
            else:
                hit.append(d)
        self.drones = hit

    def handle(self, ev) -> None:
        if ev.type != pygame.KEYDOWN:
            return
        if ev.key in (pygame.K_LEFT, pygame.K_a):
            self.lane = max(0, self.lane - 1)
        elif ev.key in (pygame.K_RIGHT, pygame.K_d):
            self.lane = min(LANES - 1, self.lane + 1)
        elif ev.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
            self.fire()
        elif ev.key == pygame.K_r:
            self.reset()

    def shell_pos(self, sh: Shell):
        t = min(1.0, sh.t)
        x = sh.x + (sh.tx - sh.x) * t
        y = sh.y + (sh.ty - sh.y) * t - math.sin(t * math.pi) * 220
        return x, y

    def draw(self, s: pygame.Surface) -> None:
        s.fill(BG)
        ox = int(math.sin(self.pulse * 40) * 10 * self.shake)
        for i in range(18):
            y = int((self.pulse * 80 + i * 120) % (H + 40)) - 20
            pygame.draw.line(s, (36, 10, 12), (0, y), (W, y), 2)
        pygame.draw.rect(s, ASH, (40, 240, W - 80, BASE_Y - 200), border_radius=28)
        pygame.draw.rect(s, COPPER, (40, 240, W - 80, BASE_Y - 200), 4, border_radius=28)
        for i, x in enumerate(LANE_X):
            pygame.draw.line(s, (80, 28, 24), (x + ox, 260), (x + ox, BASE_Y - 20), 4)
            pygame.draw.circle(s, (90, 30, 26), (x + ox, BASE_Y - 10), 10)
        for d in self.drones:
            x = LANE_X[d.lane] + ox + int(math.sin(d.wobble) * 8)
            y = int(d.y)
            col = CRIMSON if d.kind == "heavy" else TEAL
            pygame.draw.circle(s, col, (x, y), 34 if d.kind == "heavy" else 26)
            pygame.draw.circle(s, GOLD, (x, y), 12)
            pygame.draw.polygon(s, LAVA, [(x - 18, y + 8), (x, y + 36), (x + 18, y + 8)])
        for sh in self.shells:
            x, y = self.shell_pos(sh)
            pygame.draw.circle(s, GOLD, (int(x) + ox, int(y)), 14)
            pygame.draw.circle(s, (255, 250, 210), (int(x) + ox, int(y)), 6)
        bx = LANE_X[self.lane] + ox
        pygame.draw.rect(s, EMBER, (bx - 54, BASE_Y - 36, 108, 54), border_radius=16)
        pygame.draw.rect(s, GOLD, (bx - 54, BASE_Y - 36, 108, 54), 3, border_radius=16)
        pygame.draw.polygon(s, LAVA, [(bx - 16, BASE_Y - 36), (bx + 16, BASE_Y - 36), (bx, BASE_Y - 88)])
        bar = pygame.Rect(120, BASE_Y + 50, 840, 28)
        pygame.draw.rect(s, (40, 12, 14), bar, border_radius=10)
        pygame.draw.rect(s, GOLD, (120, BASE_Y + 50, int(840 * self.charge), 28), border_radius=10)
        for sp in self.sparks:
            pygame.draw.circle(s, sp.col, (int(sp.x) + ox, int(sp.y)), max(1, int(sp.r * sp.life * 2)))
        title = self.font_lg.render(TITLE, True, GOLD)
        s.blit(title, title.get_rect(center=(W // 2, 78)))
        handle = self.font_sm.render(HANDLE, True, TEAL)
        s.blit(handle, handle.get_rect(center=(W // 2, 128)))
        meta = self.font_md.render(f"SCORE  {self.score}    LIVES  {max(0, self.lives)}", True, INK)
        s.blit(meta, meta.get_rect(center=(W // 2, 190)))
        hint = self.font_sm.render("← → move   SPACE fire   R reset", True, (210, 150, 120))
        s.blit(hint, hint.get_rect(center=(W // 2, H - 48)))
        if self.over:
            over = self.font_md.render("FORT BREACHED", True, CRIMSON)
            s.blit(over, over.get_rect(center=(W // 2, 230)))

    def play(self) -> None:
        screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITLE)
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                else:
                    self.handle(ev)
            self.update(dt)
            self.draw(self.surf)
            screen.blit(self.surf, (0, 0))
            pygame.display.flip()

    def record_mp4(self, path: str) -> None:
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart", path,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        frames = FPS * 15
        for i in range(frames):
            self.update(1.0 / FPS)
            self.draw(self.surf)
            proc.stdin.write(pygame.image.tostring(self.surf, "RGB"))
            if i % 30 == 0:
                print(f"frame {i}/{frames}", flush=True)
        proc.stdin.close()
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed: {rc}")
        print("wrote", path)


def main() -> None:
    record = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
    play = "--play" in sys.argv
    if record or not play:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    pygame.font.init()
    g = Game(record or not play)
    if record or not play:
        out = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/VANADINITE_BARRAGE_ElbowOS.mp4")
        g.record_mp4(out)
    else:
        g.play()
    pygame.quit()


if __name__ == "__main__":
    main()
