
import requests
import pandas as pd
import time
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from ta.trend import EMAIndicator
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

# Full list of stocks
symbols = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK",
    "AXISBANK", "LT", "ITC", "MARUTI", "HINDUNILVR", "ASIANPAINT", "BAJFINANCE",
    "ULTRACEMCO", "NTPC", "POWERGRID", "TITAN", "WIPRO", "TECHM", "JSWSTEEL",
    "COALINDIA", "HCLTECH", "NESTLEIND", "SUNPHARMA", "TATAMOTORS", "CIPLA",
    "DIVISLAB", "BAJAJFINSV", "BHARTIARTL", "DRREDDY", "GRASIM", "ADANIPORTS",
    "BPCL", "EICHERMOT", "BRITANNIA", "SHREECEM", "HDFCLIFE", "SBILIFE", "HEROMOTOCO",
    "INDUSINDBK", "IOC", "UPL", "ONGC", "TATASTEEL", "M&M", "APOLLOHOSP", "BAJAJ-AUTO",
    "VEDL", "ZOMATO", "DELHIVERY", "ADANIENT", "ADANIGREEN", "ADANITRANS", "DMART",
    "GAIL", "ICICIGI", "ICICIPRULI", "NAUKRI", "PAYTM", "POLYCAB", "RECLTD", "SRF",
    "TORNTPHARM", "YESBANK", "BANKBARODA", "BANDHANBNK", "FEDERALBNK", "IDFCFIRSTB",
    "PNB", "RBLBANK", "AUBANK", "INDIGO", "CHOLAFIN", "MUTHOOTFIN", "L&TFH", "PEL",
    "CANBK", "IRCTC", "ABBOTINDIA", "IEX", "MFSL", "BIOCON", "LALPATHLAB", "TATAPOWER",
    "HAVELLS", "AMBUJACEM", "DABUR", "PAGEIND", "COLPAL", "PIDILITIND", "MARICO",
    "TVSMOTOR", "GLAND", "BOSCHLTD", "HAL", "BEL", "IRFC", "NHPC", "NATIONALUM",
    "COFORGE", "INDIAMART", "NAVINFLUOR"
]

def fetch_stock_data(symbol):
    try:
        url = "https://scanner.tradingview.com/india/scan"
        payload = {
            "symbols": {"tickers": [f"NSE:{symbol}"], "query": {"types": []}},
            "columns": ["open", "high", "low", "close", "volume"]
        }
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()

        raw = data.get("data", [])
        if not raw or 'd' not in raw[0] or not raw[0]['d']:
            return None

        d = raw[0]['d']
        df = pd.DataFrame([d], columns=["open", "high", "low", "close", "volume"])
        df = df.astype(float)
        df.index = pd.date_range(end=pd.Timestamp.now(), periods=1, freq='5min')

        close = df["close"]
        df["rsi"] = RSIIndicator(close, window=14).rsi()
        df["ema8"] = EMAIndicator(close, window=8).ema_indicator()
        df["ema21"] = EMAIndicator(close, window=21).ema_indicator()
        df["atr"] = AverageTrueRange(df["high"], df["low"], df["close"], window=14).average_true_range()

        signal = "Hold"
        if df["close"].iloc[-1] > df["ema8"].iloc[-1] > df["ema21"].iloc[-1] and df["rsi"].iloc[-1] > 55:
            signal = "Buy"
        elif df["close"].iloc[-1] < df["ema8"].iloc[-1] < df["ema21"].iloc[-1] and df["rsi"].iloc[-1] < 45:
            signal = "Sell"

        base_price = df["close"].iloc[-1]
        predicted_price = round(base_price * 1.017, 2)

        try:
            history = pd.read_csv("future_validation.csv")
            match = history[history["symbol"] == symbol]
            if not match.empty:
                success_rate = (match["success"] == "Yes").sum() / len(match)
                predicted_price = round(base_price * (1 + 0.005 * success_rate), 2)
        except:
            pass

        stop_loss = round(base_price - 1.5 * df["atr"].iloc[-1], 2)
        qty = 100
        gain = round((predicted_price - base_price) * qty, 2)

        return {
            "symbol": symbol,
            "close": round(base_price, 2),
            "rsi": round(df["rsi"].iloc[-1], 2),
            "atr": round(df["atr"].iloc[-1], 2),
            "signal": signal,
            "predicted_price": predicted_price,
            "stop_loss": stop_loss,
            "gain": gain
        }
    except:
        return None

class ScreenerLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.add_widget(Label(text='Top Stock Picks (Predicted Gain)', size_hint=(1, 0.1)))
        scroll = ScrollView(size_hint=(1, 0.9))
        self.result_label = Label(size_hint_y=None, text='', halign='left', valign='top')
        self.result_label.bind(texture_size=self.result_label.setter('size'))
        scroll.add_widget(self.result_label)
        self.add_widget(scroll)
        self.run_screener()

    def run_screener(self):
        results = []
        for sym in symbols:
            data = fetch_stock_data(sym)
            if data:
                results.append(data)
        results = sorted(results, key=lambda x: x['gain'], reverse=True)
        output = ""
        for r in results[:15]:
            color = '[color=00FF00]' if r['gain'] > 0 else '[color=FF0000]'
            output += f"{color}{r['symbol']}: ₹{r['close']} → ₹{r['predicted_price']} | Signal: {r['signal']} | Gain: ₹{r['gain']}[/color]
"
        self.result_label.text = output

class ScreenerApp(App):
    def build(self):
        return ScreenerLayout()

if __name__ == '__main__':
    ScreenerApp().run()
