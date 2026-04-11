import math
import time


# ─── Easing Functions ────────────────────────────────────────────────

def ease_out_cubic(t):
    """Fast start, slow end. Great for card movements."""
    return 1.0 - (1.0 - t) ** 3

def ease_in_out_quad(t):
    """Smooth start and end. Good for UI transitions."""
    if t < 0.5:
        return 2 * t * t
    return 1 - (-2 * t + 2) ** 2 / 2

def ease_out_back(t):
    """Slight overshoot. Good for card arrivals."""
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * (t - 1.0) ** 3 + c1 * (t - 1.0) ** 2

def ease_out_elastic(t):
    """Bouncy. Good for celebrations."""
    if t == 0 or t == 1:
        return t
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi / 3)) + 1

def linear(t):
    return t


# ─── Animation Class ────────────────────────────────────────────────

class Animation:
    """A single animation tween."""
    def __init__(self, start_val, end_val, duration, easing=ease_out_cubic, delay=0.0, on_complete=None):
        self.start_val = start_val  # Can be (x, y) tuple or single float
        self.end_val = end_val
        self.duration = max(duration, 0.001)
        self.easing = easing
        self.delay = delay
        self.on_complete = on_complete

        self.elapsed = -delay  # Negative = delayed
        self.is_complete = False
        self.is_tuple = isinstance(start_val, (tuple, list))

    def update(self, dt):
        """Advance the animation by dt seconds. Returns current value."""
        self.elapsed += dt
        if self.elapsed < 0:
            # Still in delay period
            return self.start_val

        t = min(self.elapsed / self.duration, 1.0)
        eased = self.easing(t)

        if self.is_tuple:
            val = tuple(
                s + (e - s) * eased
                for s, e in zip(self.start_val, self.end_val)
            )
        else:
            val = self.start_val + (self.end_val - self.start_val) * eased

        if t >= 1.0 and not self.is_complete:
            self.is_complete = True
            if self.on_complete:
                self.on_complete()

        return val

    @property
    def current_value(self):
        """Get the current interpolated value without advancing time."""
        if self.elapsed < 0:
            return self.start_val
        t = min(self.elapsed / self.duration, 1.0)
        eased = self.easing(t)
        if self.is_tuple:
            return tuple(
                s + (e - s) * eased
                for s, e in zip(self.start_val, self.end_val)
            )
        return self.start_val + (self.end_val - self.start_val) * eased


# ─── Animation Manager ──────────────────────────────────────────────

class AnimationManager:
    """Manages multiple concurrent animations with named channels."""
    def __init__(self):
        self.animations = {}  # name → Animation
        self.blocking = set() # Names of blocking animations

    def add(self, name, animation, blocking=False):
        """Add or replace a named animation."""
        self.animations[name] = animation
        if blocking:
            self.blocking.add(name)

    def update(self, dt):
        """Update all animations. Returns True if any blocking animation is active."""
        completed = []
        for name, anim in self.animations.items():
            anim.update(dt)
            if anim.is_complete:
                completed.append(name)

        for name in completed:
            self.blocking.discard(name)
            del self.animations[name]

        return len(self.blocking) > 0

    def get_value(self, name, default=None):
        """Get the current value of a named animation."""
        if name in self.animations:
            return self.animations[name].current_value
        return default

    def is_active(self, name):
        return name in self.animations

    def is_any_blocking(self):
        return len(self.blocking) > 0

    def clear(self):
        self.animations.clear()
        self.blocking.clear()


# ─── Timer Utility ───────────────────────────────────────────────────

class Timer:
    """Non-blocking countdown timer."""
    def __init__(self, duration, on_complete=None):
        self.duration = duration
        self.elapsed = 0.0
        self.on_complete = on_complete
        self.is_complete = False

    def update(self, dt):
        if self.is_complete:
            return True
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.is_complete = True
            if self.on_complete:
                self.on_complete()
            return True
        return False

    @property
    def progress(self):
        return min(self.elapsed / self.duration, 1.0)


# ─── Particle System (Simple) ───────────────────────────────────────

class Particle:
    def __init__(self, x, y, vx, vy, color, size, lifetime, gravity=True):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.age = 0.0
        self.gravity = gravity

    def update(self, dt):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.gravity:
            self.vy += 200 * dt  # Gravity
        return self.age < self.lifetime

    @property
    def alpha(self):
        return max(0, 1.0 - self.age / self.lifetime)


class ParticleEmitter:
    """Spawns particles at a position."""
    def __init__(self):
        self.particles = []

    def emit(self, x, y, count=10, colors=None, speed=150, lifetime=0.8, size=4, gravity=True):
        import random
        if colors is None:
            colors = [(255, 215, 0), (255, 180, 0), (255, 255, 100)]
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            spd = random.uniform(speed * 0.5, speed)
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd - (100 if gravity else 0)
            color = random.choice(colors)
            sz = random.uniform(size * 0.5, size * 1.5)
            lt = random.uniform(lifetime * 0.6, lifetime)
            self.particles.append(Particle(x, y, vx, vy, color, sz, lt, gravity))

    def update(self, dt):
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, surface):
        import pygame
        for p in self.particles:
            alpha = int(255 * p.alpha)
            if alpha <= 0: continue
            
            # Draw a glowing circle
            s = pygame.Surface((int(p.size*2), int(p.size*2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p.color, alpha), (p.size, p.size), p.size)
            surface.blit(s, (int(p.x - p.size), int(p.y - p.size)))
