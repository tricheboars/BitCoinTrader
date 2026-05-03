"""Geometric Brownian motion price walker."""
import math
import random


def step(price: float, drift: float, volatility: float, dt: float = 1.0) -> float:
    z = random.gauss(0.0, 1.0)
    new_price = price * math.exp(
        (drift - 0.5 * volatility ** 2) * dt
        + volatility * math.sqrt(dt) * z
    )
    return max(new_price, 0.0001)
