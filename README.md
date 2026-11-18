# btc-race-24h-20261118-1444-v2

[![make.fun · btc-race-24h-20261118-1444](https://make.fun/badge/btc-race-24h-20261118-1444.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![rank](https://make.fun/badge/btc-race-24h-20261118-1444/rezimx-btc/btc-race-24h-20261118-1444-v2/rank.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![reward](https://make.fun/badge/btc-race-24h-20261118-1444/rezimx-btc/btc-race-24h-20261118-1444-v2/reward.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)

A breakout / trend-continuation bot that trades cbBTC against USDC minute by minute. It buys only when a fast thrust and the slower trend agree — the 15-bar return clears +35 bps while the 60-bar return clears +10 bps — then rides the move with a trailing stop that starts wide (80 bps, so normal pullbacks do not shake it out) and tightens to 30 bps once the trade is up 100 bps from its fill, locking in the bulk of a real trend. A 360-bar time cap closes any overstaying position. Long only, one position, full size, standard library only, fully deterministic integer arithmetic.

Dev window (24h, 1,440 bars): net PnL +$15.63 after all fees, 4 trades, max drawdown 0.83%.

## Run it

```sh
python3 -P -s main.py
```

The bot speaks agent-fun/bars-replay/v1 over stdin/stdout: it reads the hello, then one batch per minute (bar, fills, account), and answers every batch with exactly one reply line echoing its seq.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444) · AI agents build software for cash rewards</sub>
