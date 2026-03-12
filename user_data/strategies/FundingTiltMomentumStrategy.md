# FundingTiltMomentumStrategy

## Purpose
This strategy implements the document's idea of combining medium-horizon trend with a funding-rate overlay. It trades with the trend, but avoids paying excessive carry when the market looks crowded.

## Core Logic
- Start from a slow directional momentum signal.
- Require the fast EMA to agree with the broader direction.
- For longs, avoid entry when average recent funding is too positive.
- For shorts, prefer conditions where funding is flat-to-positive, since that makes short carry less hostile or favorable.
- Scale stake modestly based on recent funding instead of using aggressive leverage changes.

## Why It May Work
Funding can act as a crowding indicator in perpetual futures. When trend and carry align, the trade can have both directional and structural support.

## Main Risk
Funding filters can become too restrictive and cause the strategy to miss valid trends. Hourly execution also increases turnover versus the slower 4h strategies.