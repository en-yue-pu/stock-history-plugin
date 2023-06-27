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

previous_data = None  # 用于保存上一次的数据

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

            # Extract each type of data into separate lists
            open_prices = [result['o'] for result in data['results']]
            close_prices = [result['c'] for result in data['results']]
            high_prices = [result['h'] for result in data['results']]
            low_prices = [result['l'] for result in data['results']]
            volume_weighted_prices = [result['vm'] for result in data['results']]

            global previous_data
            # Save the data into a dictionary for future use
            previous_data = {
                'open_prices': open_prices,
                'close_prices': close_prices,
                'high_prices': high_prices,
                'low_prices': low_prices,
                'volume_weighted_prices': volume_weighted_prices,
            }

            return quart.Response(response=json.dumps(data), status=200)
    except Exception as e:
        return quart.Response(response=json.dumps({"error": str(e)}), status=400)

@app.route("/predict", methods=['POST'])
async def predict_stock_price():
    try:
        global previous_data
        
        if previous_data is None:
            return quart.Response(response=json.dumps({"error": "No data available"}), status=400)

        # 获取请求参数中的数据类型
        data_type = request.json.get('data_type', 'close_prices')#默认值收盘价
        if data_type not in previous_data:
            return quart.Response(response=json.dumps({"error": "Invalid data type"}), status=400)

        # 使用指定类型的数据进行预测
        feature_data = previous_data[data_type]

        # 将特征数据转换为DataFrame
        df = pd.DataFrame({'feature': feature_data})
        
        # 将数据转换为 numpy 数组
        data = df['feature'].values
        # 定义训练集和测试集的大小
        train_size = int(len(data) * 0.8)
        test_size = len(data) - train_size
        # 分割训练集和测试集
        train_data = data[:train_size]
        test_data = data[test_size:]
        
        scaler = MinMaxScaler()
        # 对训练集进行归一化
        train_data = scaler.fit_transform(train_data.reshape(-1, 1))
        # 对测试集进行归一化
        test_data = scaler.transform(test_data.reshape(-1, 1))

        # 定义一个函数，根据过去 n 天的数据来生成输入和输出
        def create_dataset(data, n):
            x = []
            y = []
            for i in range(n, len(data)):
                x.append(data[i-n:i, 0])
                y.append(data[i, 0])
            return np.array(x), np.array(y)
        
        n = 60 # 过去天数为 60
        
        # 创建训练集和测试集的输入和输出
        x_train, y_train = create_dataset(train_data, n)
        x_test, y_test = create_dataset(test_data, n)
        
        # 调整输入的形状，以适应 LSTM 模型
        x_train = x_train.reshape(x_train.shape[0], x_train.shape[1], 1)
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
        
        model.fit(x_train, y_train, epochs=20, batch_size=30)
        
        y_pred = model.predict(x_test)
        
        # 反归一化预测结果和真实结果
        y_pred = scaler.inverse_transform(y_pred)
        y_test = scaler.inverse_transform(y_test.reshape(-1, 1))

        return quartResponse(response=json.dumps({'prediction': y_pred.tolist(), 'actual': y_test.tolist()}), status=200)
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
    app.run(debug=True, host="0.0.0.0", port=5004)#启动服务

if __name__ == "__main__":
    main()