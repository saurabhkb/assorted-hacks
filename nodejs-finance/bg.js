var req = require('request');
var mysql = require('mysql');
var conString = {host: 'localhost', user: 'root', password: 'saurabh', database: 'finance'};

var symblist = {'AAPL':['A', 'B'], 'MSFT':['D'], 'GOOG':['A', 'B'], 'AMZN':['C'], 'BAC':['A', 'B', 'C'], 'GS':['C'], 'ORCL':['E'], 'WMT':['X']};
var symb = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'BAC', 'GS', 'ORCL', 'WMT'];

function Parse(num) {
	var x = parseFloat(num);
	if(isNaN(x)) return 1;
	else return x;
}
function updateDB(symb) {
	var list = symblist[symb];
	console.log("Start===> " + symb + ", " + list);
	console.log(list + ", " + list[0]);
	var url = 'http://query.yahooapis.com/v1/public/yql?q=select * from yahoo.finance.quotes where symbol in ("' + symb + '")&env=store://datatables.org/alltableswithkeys&format=json';
	req.post(url, {}, function(err, resp) {
		var conn = mysql.createConnection(conString);
		conn.connect();
		json = JSON.parse(resp.body);
		quote = json.query.results.quote;
		t = Math.random;
		for(var i = 0; i < list.length; i++) {
			x = list[i];
			conn.query("UPDATE `stock` SET `last_trade_price` = ?, `ask` = ?, `open` = ?, `prev_close` = ?, `dividend` = ?, `year_high` = ?, `year_low` = ?, `day_high` = ?, `day_low` = ?, `avg_daily_volume` = ?, `twohundred_day_avg` = ?, `fifty_day_avg` = ?, `PEG` = ?, `PE` = ?, `bid` = ?, `price_per_sales` = ?, `one_year_target_price` = ?, `price_per_book` = ? WHERE `symbol` = ? AND `type` = ?", [Parse(quote.LastTradePriceOnly) * t(), Parse(quote.Ask) * t(), Parse(quote.Open) * t(), Parse(quote.PreviousClose) * t(), Parse(quote.DividendShare) * t(), Parse(quote.YearHigh) * t(), Parse(quote.YearLow) * t(), Parse(quote.DaysHigh) * t(), Parse(quote.DaysLow) * t(), Parse(quote.AverageDailyVolume) * t(), Parse(quote.TwoHundreddayMovingAverage) * t(), Parse(quote.FiftydayMovingAverage) * t(), Parse(quote.PEGRatio) * t(), Parse(quote.PERatio) * t(), Parse(quote.Bid) * t(), Parse(quote.PriceSales) * t(), Parse(quote.OneyrTargetPrice) * t(), Parse(quote.PriceBook) * t(), quote.symbol, list[i]], function(err, result) {
				if(err) throw err;
				console.log("End===> " + symb + ", " + x);
			});
		}
	});
	return;
}
for(var i = 0; i < symb.length; i++)
	updateDB(symb[i]);
