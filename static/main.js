// ==== 美股前十大即時報價 ==== //
function refreshTop10() {
    fetch('/api/top10_quotes')
      .then(res => res.json())
      .then(data => {
        let tbody = document.querySelector('#top10-table tbody');
        tbody.innerHTML = "";
        data.forEach(row => {
            if(row.price !== undefined && row.price !== null) {
                tbody.innerHTML += `<tr>
                    <td>${row.symbol}</td>
                    <td>${row.name}</td>
                    <td class="price">${row.price}</td>
                    <td>${row.currency||""}</td>
                </tr>`;
            } else {
                tbody.innerHTML += `<tr>
                    <td>${row.symbol}</td>
                    <td colspan="3" class="error">${row.error || "查無資料"}</td>
                </tr>`;
            }
        });
      });
}
refreshTop10();
setInterval(refreshTop10, 10 * 1000);

// ==== 自選即時報價 ==== //
function refreshQuote() {
    let symbol = document.getElementById("symbol").value.trim().toUpperCase() || "AAPL";
    fetch('/api/quote?symbol=' + symbol)
      .then(res => res.json())
      .then(data => {
        let msg = document.getElementById("custom-quote-msg");
        let table = document.getElementById("custom-quote-table");
        let tbody = table.querySelector("tbody");
        if(data.price !== undefined && data.price !== null) {
            msg.textContent = "";
            table.style.display = "";
            tbody.innerHTML = `<tr>
                <td>${data.symbol}</td>
                <td>${data.name}</td>
                <td class="price">${data.price}</td>
                <td>${data.currency||""}</td>
            </tr>`;
        } else {
            msg.textContent = data.error || "查無即時價格";
            msg.className = "error";
            table.style.display = "none";
        }
      });
}
refreshQuote();
document.getElementById("custom-quote-btn").onclick = refreshQuote;

// ==== 歷史資料查詢&K線+均線+成交量 ==== //
document.getElementById("history-form").onsubmit = function(e) {
    e.preventDefault();
    let fd = new FormData(this);
    let params = new URLSearchParams(fd).toString();
    fetch('/api/history?' + params)
        .then(res => res.json())
        .then(data => {
            let table = document.getElementById("history-table");
            let msg = document.getElementById("history-msg");
            msg.textContent = "";
            if (Array.isArray(data) && data.length > 0) {
                let headers = Object.keys(data[0]);
                let html = '<tr>' + headers.map(h=>`<th>${h}</th>`).join('') + '</tr>';
                data.forEach(row => {
                    html += '<tr>' + headers.map(h=>`<td>${row[h]}</td>`).join('') + '</tr>';
                });
                table.innerHTML = html;

                // --- 畫K棒+均線+成交量 ---
                let openKey = headers.find(h => /^Open/.test(h));
                let highKey = headers.find(h => /^High/.test(h));
                let lowKey = headers.find(h => /^Low/.test(h));
                let closeKey = headers.find(h => /^Close/.test(h));
                let volKey = headers.find(h => /^Volume/.test(h));
                let dateKey = headers.find(h => /^Date|Datetime/.test(h));
                if (openKey && highKey && lowKey && closeKey && volKey && dateKey) {
                    let x = data.map(row => row[dateKey].slice(0,10));
                    let open = data.map(row => Number(row[openKey]));
                    let high = data.map(row => Number(row[highKey]));
                    let low = data.map(row => Number(row[lowKey]));
                    let close = data.map(row => Number(row[closeKey]));
                    let volume = data.map(row => Number(row[volKey]));
                    function sma(arr, n) {
                        let r = [];
                        for(let i=0; i<arr.length; ++i) {
                            if(i < n-1) r.push(null);
                            else r.push(
                                (arr.slice(i-n+1,i+1).reduce((a,b)=>a+b,0))/n
                            );
                        }
                        return r;
                    }
                    let ma5 = sma(close, 5);
                    let ma10 = sma(close, 10);
                    let candle = {
                        x, open, high, low, close,
                        type: 'candlestick', name:'K線',
                        xaxis: 'x', yaxis: 'y',
                        increasing: {line: {color: '#df382c'}},
                        decreasing: {line: {color: '#228B22'}}
                    };
                    let ma5line = {
                        x, y: ma5, mode:'lines', name:'MA5',
                        line:{color:'#1c78ff', width:1.5}, yaxis:'y'
                    };
                    let ma10line = {
                        x, y: ma10, mode:'lines', name:'MA10',
                        line:{color:'#fbc02d', width:1.2}, yaxis:'y'
                    };
                    let volbar = {
                        x, y: volume, type:'bar', name:'成交量',
                        marker: {color:'#b0b9c6'}, yaxis:'y2', opacity:0.6
                    };
                    let layout = {
                        margin:{t:24,l:60,r:24,b:40},
                        xaxis: {rangeslider:{visible:false}, showline:true},
                        yaxis: {domain:[0.3,1], title:'價格', showline:true},
                        yaxis2: {domain:[0,0.23], title:'成交量', showgrid:false},
                        legend:{orientation:'h', y:1.11},
                        height:420
                    };
                    Plotly.newPlot("plotly-chart", [candle, ma5line, ma10line, volbar], layout, {displayModeBar:false});
                }
            } else if (data.error) {
                table.innerHTML = "";
                msg.textContent = data.error;
                document.getElementById('plotly-chart').innerHTML = '';
            } else {
                table.innerHTML = "";
                msg.textContent = "查無資料";
                document.getElementById('plotly-chart').innerHTML = '';
            }
        });
};

// ==== 問 Gemini AI ==== //
function askGeminiAI(question) {
    let answerDiv = document.getElementById('ai-answer');
    answerDiv.textContent = "AI 回答查詢中...";
    fetch('/api/ai', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({question})
    })
    .then(res => res.json())
    .then(data => {
        if(data.answer) {
            answerDiv.textContent = data.answer;
        } else {
            answerDiv.textContent = "出錯：" + data.error;
        }
    })
    .catch(err => {
        answerDiv.textContent = "伺服器錯誤，請稍後再試";
    });
}

