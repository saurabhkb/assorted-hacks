package com.coep.mynews;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URL;
import java.net.URLEncoder;

import android.content.Context;
import android.net.Uri;
import android.os.AsyncTask;

public class LinkClickNotifier extends AsyncTask<String, Integer, Integer> implements Constants {
	
	NewsListFragment caller_frag;
	Context mContext;
	public LinkClickNotifier(Context c, NewsListFragment nf) {
		caller_frag = nf;
		mContext = c;
	}
	@Override
	protected Integer doInBackground(String... params) {
		int type = Integer.parseInt(params[0]);
		String title = params[1];
		String desc = params[2];
		try {
			int user_id = mContext.getSharedPreferences(PREFS_NAME, 0).getInt("user_id", 0);
			int session_id = mContext.getSharedPreferences(PREFS_NAME, 0).getInt("session_id", 0);
			//URI uri = new URI("http", "//" + BASE + "/clickedArticle/" + user_id + "/" + session_id + "/" + categories[type], title, "");
			String spec = "http://10.0.2.2:5000/clickedArticle/" + user_id + "/" + session_id + "/" + categories[type] + "/" + 
			URLEncoder.encode(title, "utf-8") + "+" + URLEncoder.encode(desc, "utf-8");
			System.out.println("SPEC: " + spec);
			URL url = new URL(spec);
			HttpURLConnection urlConnection = (HttpURLConnection) url.openConnection();
			BufferedReader reader = new BufferedReader(new InputStreamReader(
					urlConnection.getInputStream()), 1024 * 16);
		} catch (IOException e) {
			e.printStackTrace();
		}
		return null;
	}
}
