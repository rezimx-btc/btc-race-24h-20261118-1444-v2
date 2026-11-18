"""Breakout / trend-continuation bot for agent-fun/bars-replay/v1.

Strategy (long only, one position, full size):
  * Entry: buy when the close is breaking out with momentum on two horizons
    at once -- the 15-bar return is at least +35 bps AND the 60-bar return
    is at least +10 bps. A fast thrust that the slower trend confirms is a
    trend continuation; a fast thrust against a flat or falling 60-bar trend
    is chop and is skipped.
  * Exit: a trailing stop measured from the highest close seen while long.
    The stop is wide (80 bps) while the trade is young so normal pullbacks
    do not shake it out, and it tightens to 30 bps once the trade is up
    100 bps from its fill, locking in the bulk of a real move. A hard time
    cap of 360 bars closes any position that has overstayed.
  * Everything is integer arithmetic on the raw price units (no floats, no
    clock, no randomness, no files, no network), so two runs on the same
    bars answer every batch with the same orders.

The bot speaks the protocol through the kit's Python shim (vendor/).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"

# Bars of closes needed before the first trade (the 60-bar return needs 61
# closes; 121 keeps the bot out of the window's unsettled opening stretch).
MIN_CLOSES = 121
# Fast thrust: 15-bar return, in basis points.
ROC_FAST_BARS = 15
ROC_FAST_MIN_BPS = 35
# Slow confirmation: 60-bar return, in basis points.
ROC_SLOW_BARS = 60
ROC_SLOW_MIN_BPS = 10
# Profit lock: once the trade is up this much from its fill price, the
# trailing stop tightens from BASE_STOP_BPS to LOCK_STOP_BPS.
LOCK_GAIN_BPS = 100
LOCK_STOP_BPS = 30
BASE_STOP_BPS = 80
# Hard time cap on a position, in bars.
MAX_HOLD_BARS = 360
# Fills land at the next bar's open; on the dev window the open never moved
# more than 19 bps from the previous close, so 150 bps is ample headroom
# while still refusing an absurd fill.
MAX_SLIPPAGE_BPS = 150


class TrendBot:
    """Keeps the closes and the open position's cost basis and peak close."""

    def __init__(self):
        self.closes = []
        self.entry_px = None
        self.entry_seq = None
        self.peak = None

    def on_batch(self, state, batch):
        fresh_bar = False
        for bar in batch.get("bars", []):
            if bar.get("symbol") == SYMBOL:
                self.closes.append(int(bar["c"]))
                fresh_bar = True
        # A buy fill opens the position: its fill price is the cost basis.
        for fill in batch.get("fills", []):
            if fill.get("side") == "buy" and fill.get("status") == "filled":
                self.entry_px = int(fill["price"])
                self.entry_seq = state.seq
                self.peak = self.entry_px
        holding = state.positions.get(SYMBOL)
        if holding is None or holding.qty <= 0:
            self.entry_px = None
            self.entry_seq = None
            self.peak = None
            return self._maybe_enter(state, fresh_bar)
        return self._maybe_exit(state, holding, fresh_bar)

    def _maybe_enter(self, state, fresh_bar):
        if state.warming_up:
            return []
        if not fresh_bar:
            # No new bar this minute: the latest close is stale, and an
            # order decided on it would fill at an open the bot has not
            # seen. Wait for the next real bar.
            return []
        if len(self.closes) < MIN_CLOSES:
            return []
        close = self.closes[-1]
        fast_then = self.closes[-1 - ROC_FAST_BARS]
        slow_then = self.closes[-1 - ROC_SLOW_BARS]
        roc_fast = (close - fast_then) * 10000 // fast_then
        roc_slow = (close - slow_then) * 10000 // slow_then
        if roc_fast >= ROC_FAST_MIN_BPS and roc_slow >= ROC_SLOW_MIN_BPS:
            return [{
                "side": "buy",
                "symbol": SYMBOL,
                "notional_quote_units": state.cash,
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            }]
        return []

    def _maybe_exit(self, state, holding, fresh_bar):
        close = self.closes[-1] if self.closes else None
        if close is None or not fresh_bar:
            return []
        if self.entry_px is None:
            # Holding without a fill on record (should not happen): anchor
            # the cost basis at the latest close so the stops still work.
            self.entry_px = close
            self.entry_seq = state.seq
            self.peak = close
        if close > self.peak:
            self.peak = close
        gain_bps = (close - self.entry_px) * 10000 // self.entry_px
        stop_bps = LOCK_STOP_BPS if gain_bps >= LOCK_GAIN_BPS else BASE_STOP_BPS
        if close * 10000 < self.peak * (10000 - stop_bps):
            return [self._sell_all(holding)]
        if self.entry_seq is not None and state.seq - self.entry_seq >= MAX_HOLD_BARS:
            return [self._sell_all(holding)]
        return []

    def _sell_all(self, holding):
        return {
            "side": "sell",
            "symbol": SYMBOL,
            "qty": holding.qty,
            "max_slippage_bps": MAX_SLIPPAGE_BPS,
        }


def main():
    makefun_bars.run(TrendBot().on_batch)


if __name__ == "__main__":
    main()
