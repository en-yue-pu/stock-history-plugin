import json
import requests
import quart
import quart_cors
from quart import jsonify, request
from httpx import AsyncClient

app = quart.Quart(__name__)
quart_cors.cors(app, allow_origin="https://chat.openai.com") # 只允许chatgpt官方domin的访问

@app.route("/stock_data", methods=['GET'])
async def get_stock_data():
    url = 'https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2021-06-21/2023-06-20'
    parameters = {
      'adjusted': 'true',
      'sort': 'asc',
      'limit': '50000'
    }
    headers = {
      'Accepts': 'application/json',
      'apiKey': 'KP0SneaAKULS4g4SO9l5uTTxwzdFg9xz',
    }
    try:
        async with AsyncClient() as client:
            response = await client.get(url, params=parameters, headers=headers)
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