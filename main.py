import json
import requests
import quart
import quart_cors
from quart import jsonify, request
from httpx import AsyncClient

app = quart.Quart(__name__)
quart_cors.cors(app, allow_origin="https://chat.openai.com") # 只允许chatgpt官方domin的访问
    
@app.route("/stocks", methods=['GET'])
async def get_stocks():
    ticker = request.args.get('ticker', default='AAPL', type=str)# 股票代码
    from_date = request.args.get('from_date', default='2021-06-21', type=str)#时间范围开始日期
    to_date = request.args.get('to_date', default='2023-06-20', type=str)#时间范围结束日期
    timespan = request.args.get('timespan', default='day', type=str)#时间跨度
    url = f'https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/{timespan}/{from_date}/{to_date}?adjusted=true&sort=asc&limit=50000&apiKey=KP0SneaAKULS4g4SO9l5uTTxwzdFg9xz'
    try:
        async with AsyncClient() as client:
            response = await client.get(url)
            data = response.json()
            return quart.Response(response=json.dumps(data), status=200)
    except Exception as e:
        return quart.Response(response=json.dumps({"error": str(e)}), status=400)
    
@app.get("/logo.jpg")#响应读取logo的请求
async def plugin_logo():
    filename = 'logo.jpg'
    try:
        return await quart.send_file(filename, mimetype='image/jpg')
    except FileNotFoundError:
        return jsonify({"error": f"文件'{filename}'不存在"}), 404

@app.get("/.well-known/ai-plugin.json")#响应读取manifest文件的请求
async def plugin_manifest():
    host = request.headers['Host']
    filename = "./.well-known/ai-plugin.json"
    try:
        with open(filename) as f:
            text = f.read()
            return quart.Response(text, mimetype="text/json")
    except FileNotFoundError:
        return jsonify({"error": f"文件'{filename}'不存在"}), 404

@app.get("/openapi.yaml")#响应读取openAPI规范文件(仕様書)的请求
async def openapi_spec():
    host = request.headers['Host']
    filename = "openapi.yaml"
    try:
        with open(filename) as f:
            text = f.read()
            return quart.Response(text, mimetype="text/yaml")
    except FileNotFoundError:
        return jsonify({"error": f"文件'{filename}'不存在"}), 404

def main():
    app.run(debug=True, host="0.0.0.0", port=5003)#启动服务

if __name__ == "__main__":
    main()