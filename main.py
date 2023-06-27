import json
import quart
import quart_cors
from httpx import AsyncClient
from quart import jsonify, request
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
import matplotlib.pyplot as plt

app = quart.Quart(__name__)
quart_cors.cors(app, allow_origin="https://chat.openai.com") # 只允许chatgpt官方domin的访问

@app.route("/stocks", methods=['GET'])
async def get_stocks():
    ticker = request.args.get('stocksTicker', default='AAPL', type=str) # 股票代码
    from_date = request.args.get('from', default='2021-06-21', type=str) #时间范围开始日期
    to_date = request.args.get('to', default='2023-06-20', type=str) #时间范围结束日期
    multiplier = request.args.get('multiplier', default='1', type=str)#和timespan配合,表示timespan之前的乘数比如说2day
    timespan = request.args.get('timespan', default='day', type=str) #时间跨度
    sort_order = request.args.get('sort', default='asc', type=str) #结果是升序还是降序
    adjusted = request.args.get('adjusted', default='true', type=str) #结果是否调整了股票拆分
    limit = request.args.get('limit', default=50000, type=int) #查询的基础聚合的数量限制
    url = f'https://api.polygon.io/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}?adjusted={adjusted}&sort={sort_order}&limit={limit}&apiKey=KP0SneaAKULS4g4SO9l5uTTxwzdFg9xz'
    try:
        async with AsyncClient() as client:
            response = await client.get(url)
            data = response.json()
            return quart.Response(response=json.dumps(data), status=200)
    except Exception as e:
        return quart.Response(response=json.dumps({"error": str(e)}), status=400)

@app.route("/predict", methods=['POST'])
async def predict_stock_price():
    try:
        data = await request.get_json()
        feature_data = data['feature_data']
        target_data = data['target_data']

        df = pd.DataFrame({'Close': feature_data, 'Prediction': target_data})

        scaler = MinMaxScaler()
        df['Close'] = scaler.fit_transform(df['Close'].values.reshape(-1, 1))
        df['Prediction'] = scaler.transform(df['Prediction'].values.reshape(-1, 1))

        n = 60
        x_test = np.array(df['Close'][-n:]).reshape(1, -1)
        y_test = np.array(df['Prediction'][-n:]).reshape(1, -1)

        x_test = x_test.reshape(x_test.shape[0], x_test.shape[1], 1)

        model = Sequential()
        model.add(LSTM(50, return_sequences=True, input_shape=(n, 1)))
        model.add(Dropout(0.2))
        model.add(LSTM(50, return_sequences=True))
        model.add(Dropout(0.2))
        model.add(LSTM(50))
        model.add(Dropout(0.2))
        model.add(Dense(1))

        model.compile(loss='mean_squared_error', optimizer='adam')

        x_train = np.array(df['Close'][:-n]).reshape(1, -1)
        y_train = np.array(df['Prediction'][:-n]).reshape(1, -1)

        x_train = x_train.reshape(x_train.shape[0], x_train.shape[1], 1)

        model.fit(x_train, y_train, epochs=20, batch_size=30)

        y_pred = model.predict(x_test)

        prediction = scaler.inverse_transform(y_pred)
        actual = scaler.inverse_transform(y_test)

        return quart.Response(response=json.dumps({'prediction': prediction.tolist(), 'actual': actual.tolist()}), status=200)
    except Exception as e:
        return quart.Response(response=json.dumps({"error": str(e)}), status=400)
    
@app.get("/logo.jpg")#响应读取logo的请求
async def plugin_logo():
    filename = 'logo.jpg'
    try:
        return await quart.send_file(filename, mimetype='image/jpg')
    except FileNotFoundError:
        return jsonify({"error": f"File '{filename}' not found"}), 404

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
        return jsonify({"error": f"File '{filename}' not found"}), 404

def main():
    app.run(debug=True, host="0.0.0.0", port=5003)#启动服务

if __name__ == "__main__":
    main()