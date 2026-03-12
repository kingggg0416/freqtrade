# SessionFilteredMomentumStrategy

## Purpose
This strategy applies the document's intraday seasonality idea as a conservative entry filter rather than a standalone edge. It trades momentum only during higher-liquidity weekday windows.

## Core Logic
- Use EMA structure, ROC, and ADX to define directional continuation.
- Only open new positions during selected weekday UTC sessions.
- Avoid weekend and off-session entries where smaller accounts are more exposed to noisy price action and worse trading conditions.
- Exit when momentum fades or the trend structure breaks.

## Why It May Work
This is less about predicting a single time-of-day anomaly and more about avoiding the weakest windows for opening fresh risk. For retail-sized systems, filtering poor entry windows can matter as much as changing the indicator set.

## Main Risk
Session filters can reduce noise, but they also reduce opportunity. If the true edge is mostly independent of entry window, the filter can simply lower trade count without improving quality.