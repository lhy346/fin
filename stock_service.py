# stock_service.py
import yfinance as yf
import twstock

def get_market_info(symbol, market):
    realtime_info, history_info = "", ""
    if market == "US":
        ticker = yf.Ticker(symbol)
        info = ticker.info
        price = info.get("regularMarketPrice")
        realtime_info = f"{symbol} 現價：{price} 美元"
        hist = yf.download(symbol, period="1mo")
        history_info = hist.tail(5).to_string()
    elif market == "TW":
        stock = twstock.Stock(symbol)
        price = stock.price[-1] if stock.price else "無資料"
        realtime_info = f"{symbol} 現價：{price} 新台幣"
        history_info = f"收盤價（最近5日）：{stock.price[-5:] if stock.price else '無資料'}"
    return realtime_info, history_info
