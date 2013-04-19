package com.coep.mynews;

import android.app.Activity;
import android.graphics.Bitmap;
import android.os.Bundle;
import android.view.Menu;
import android.view.Window;
import android.webkit.WebChromeClient;
import android.webkit.WebView;
import android.webkit.WebViewClient;

public class WebViewActivity extends Activity {

	String url;
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		requestWindowFeature(Window.FEATURE_PROGRESS);
		WebView wv = new WebView(this);
		//wv.getSettings().setJavaScriptEnabled(true);
		wv.setWebChromeClient(new WebChromeClient() {
			@Override
			public void onProgressChanged(WebView webview, int progress) {
				setProgress(progress * 100);
			}
		});
		wv.setWebViewClient(new WebViewClient() {
			@Override
			public void onPageStarted(WebView view, String url, Bitmap favicon) {
				setTitle(url);
			}
		});
		setContentView(wv);
		Bundle extras = getIntent().getExtras();
		wv.loadUrl(extras.getString("URL"));
		/*Intent intent = getIntent();
		if(intent.getData() != null) {
			wv.loadUrl(intent.getDataString());
		}*/
	}
}