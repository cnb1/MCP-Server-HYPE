from mcp.server import MCPServer

from tool_functions import fetch_hype_candles, calculate_mfi

mcp = MCPServer("Hype Analytics MCP")


@mcp.tool()
def get_hype_candles(lookback_days: int = 5, interval: str = "4h") -> str:
    """Fetch HYPE candlestick (OHLCV) data from Hyperliquid.
    Use this to get price history for analysis.

    Args:
        lookback_days: Number of days of historical data to fetch. Default 5.
        interval: Candle interval. Options: 1m, 5m, 15m, 30m, 1h, 4h, 1d. Default 4h.
    """
    return fetch_hype_candles(lookback_days=lookback_days, interval=interval)


@mcp.tool()
def get_mfi(interval: str = "4h", period: int = 10) -> str:
    """Calculate the Money Flow Index (MFI) for HYPE using the trailing N candles.
    Returns the MFI value and a BUY/SELL/NEUTRAL signal.
    MFI below 30 = BUY (oversold), above 70 = SELL (overbought).

    Args:
        interval: Candle interval. Options: 1m, 5m, 15m, 30m, 1h, 4h, 1d. Default 4h.
        period: Number of trailing candles to use for the MFI calculation. Default 10.
    """
    return calculate_mfi(interval=interval, period=period)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--transport", choices=["stdio", "sse"], default="sse",
        help="Transport protocol (default: sse for network access)",
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5051)
    args = parser.parse_args()

    if args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")
