
# 获取一个股票的一段时间内的(每天/每周...自己设定)数据
数据可以是每天最高价/最低价/中间价等等

利用API polygon.io
Your Plan
Stocks Basic
5 API Calls / Minute
End of Day Data
2 Years Historical Data

预测用的数据不能太少 至少半年的数据
否则会元祖越位

# API Doc
 https://polygon.io/docs/stocks/get_v2_aggs_ticker__stocksticker__range__multiplier___timespan___from___to

# Usage 
pip install -r requirements.txt
python main.py
ngrok http 5005
# 不用ngrok也可以
在连接plugin输入框http://localhost:5003 一定要输入完整就能安装

python 3.8

.well-known/ai-plugin.json文件中，
name_for_human 和 description_for_human 是给用户看的，
name_for_model 和 description_for_model 是给模型看的。
auth 字段表示这个插件不需要任何认证。
api 字段告诉插件如何与您的 API 交互，
logo_url 是你的品牌或应用的 logo 链接。
contact_email 是你的电子邮件地址，用户或OpenAI可以通过这个邮箱与你联系。
legal_info_url 是一个链接到你的应用的法律信息的网页。
