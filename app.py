import os
from flask import Flask, request, jsonify, render_template, send_from_directory
import yfinance as yf
import google.generativeai as genai

app = Flask(__name__)   # ← 保持這樣，因為 index.html 在 templates/

# PWA routes
@app.route('/service-worker.js')
def service_worker():
    return send_from_directory('static', 'service-worker.js', mimetype='application/javascript')

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/json')

# （選用）TWA 需要時才放檔案
@app.route('/.well-known/assetlinks.json')
def assetlinks():
    path = os.path.join('static', '.well-known')
    file_path = os.path.join(path, 'assetlinks.json')
    if not os.path.exists(file_path):
        return jsonify({"error": "assetlinks.json not found"}), 404
    return send_from_directory(path, 'assetlinks.json', mimetype='application/json')

# ---------------- 首頁 ----------------
@app.route("/")
def index():
    return render_template("index.html")

# ---------------- API：前十大美股即時報價 ----------------
@app.route("/api/top10_quotes")
def top10_quotes():
    TOP10 = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'V', 'UNH']
    import yfinance as yf  # 懶載入
    results = []
    for symbol in TOP10:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            results.append({
                "symbol": symbol,
                "name": info.get("shortName", symbol),
                "price": info.get("regularMarketPrice"),
                "currency": info.get("currency")
            })
        except Exception as e:
            results.append({"symbol": symbol, "error": str(e)})
    return jsonify(results)

# ---------------- API：個股即時報價 ----------------
@app.route("/api/quote")
def stock_quote():
    import yfinance as yf
    symbol = request.args.get("symbol", "AAPL").upper()
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return jsonify({
            "symbol": symbol,
            "name": info.get("shortName", symbol),
            "price": info.get("regularMarketPrice"),
            "currency": info.get("currency")
        })
    except Exception as e:
        return jsonify({"error": str(e)})

# ---------------- API：歷史資料 ----------------
@app.route("/api/history")
def stock_history():
    import yfinance as yf
    import pandas as pd  # 保險起見
    symbol = request.args.get("symbol", "AAPL").upper()
    start = request.args.get("start")
    end = request.args.get("end")
    interval = request.args.get("interval", "1d")
    try:
        df = yf.download(symbol, start=start, end=end, interval=interval)
        if df.empty:
            return jsonify({"error": "查無資料"})
        df.columns = ['_'.join(map(str, c)) if isinstance(c, tuple) else str(c) for c in df.columns]
        data = df.reset_index().to_dict(orient="records")
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)})

# ---------------- API：Gemini AI 問答 ----------------
@app.route("/api/ai", methods=["POST"])
def ask_gemini():
    import google.generativeai as genai
    data = request.get_json(silent=True) or {}
    question = data.get("question", "")
    try:
        api_key = os.environ.get("GEMINI_API_KEY", "")  # 優先用環境變數
        if not api_key:
            # 你可以暫時放回你自己的 key，但請不要提交到公開 repo
            api_key = "YOUR_FALLBACK_KEY"
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        resp = model.generate_content(question or "Hello")
        return jsonify({"answer": getattr(resp, "text", "")})
    except Exception as e:
        return jsonify({"error": str(e)})

# ---------------- 入口 ----------------
if __name__ == '__main__':
    app.run(debug=True)
