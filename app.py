import os
from flask import Flask, request, jsonify, render_template, send_from_directory
import yfinance as yf

app = Flask(__name__)   # templates/index.html 會用到

# ---------- PWA 靜態路由（根路徑供應） ----------
@app.route('/service-worker.js')
def service_worker():
    return send_from_directory('static', 'service-worker.js', mimetype='application/javascript')

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/json')

# （選用）TWA 需要時才放檔案：static/.well-known/assetlinks.json
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
TOP10 = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'V', 'UNH']

@app.route("/api/top10_quotes")
def top10_quotes():
    results = []
    for symbol in TOP10:
        try:
            info = yf.Ticker(symbol).info
            results.append({
                "symbol": symbol,
                "name": info.get("shortName", symbol),
                "price": info.get("regularMarketPrice"),
                "currency": info.get("currency"),
            })
        except Exception as e:
            results.append({"symbol": symbol, "error": str(e)})
    return jsonify(results)

# ---------------- API：個股即時報價 ----------------
@app.route("/api/quote")
def stock_quote():
    symbol = request.args.get("symbol", "AAPL").upper()
    try:
        info = yf.Ticker(symbol).info
        return jsonify({
            "symbol": symbol,
            "name": info.get("shortName", symbol),
            "price": info.get("regularMarketPrice"),
            "currency": info.get("currency"),
        })
    except Exception as e:
        return jsonify({"error": str(e)})

# ---------------- API：歷史資料 ----------------
@app.route("/api/history")
def stock_history():
    symbol = request.args.get("symbol", "AAPL").upper()
    start = request.args.get("start")
    end = request.args.get("end")
    interval = request.args.get("interval", "1d")
    try:
        df = yf.download(symbol, start=start, end=end, interval=interval)
        if df.empty:
            return jsonify({"error": "查無資料"})
        # 攤平 MultiIndex 欄位
        df.columns = ['_'.join(map(str, c)) if isinstance(c, tuple) else str(c) for c in df.columns]
        data = df.reset_index().to_dict(orient="records")
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)})

# ---------------- [可選] Gemini AI 問答 ----------------
@app.route("/api/ai", methods=["POST"])
def ask_gemini():
    # 沒設金鑰就回覆提示，不拋例外
    api_key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if not api_key:
        return jsonify({
            "error": "Gemini 未啟用",
            "hint": "請設定環境變數 GEMINI_API_KEY 後再呼叫 /api/ai"
        }), 503

    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"error": "請提供 question"}), 400

    try:
        import google.generativeai as genai  # 延後載入
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        resp = model.generate_content(question)
        return jsonify({"answer": getattr(resp, "text", "").strip()})
    except Exception as e:
        return jsonify({"error": f"Gemini 調用失敗: {e}"}), 500

# ---------------- 啟動（本機 & Railway/Render 通用） ----------------
if __name__ == '__main__':
    # 本機預設 5000；Railway/Render 會提供 PORT
    port = int(os.environ.get("PORT", 5000))
    # 開關 debug：設環境變數 FLASK_DEBUG=1 即可開啟
    debug = os.environ.get("FLASK_DEBUG") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
