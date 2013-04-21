package com.coep.mynews;

import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.ConnectException;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import android.app.DialogFragment;
import android.content.Context;
import android.os.AsyncTask;
import android.widget.Toast;

public class FeedRetriever extends AsyncTask<Integer, NewsStory, ArrayList<NewsStory>> implements Constants {
	NewsListFragment caller_frag;
	Context mContext;
	boolean conn_fail = false;

	public FeedRetriever(Context c, NewsListFragment nf) {
		caller_frag = nf;
		mContext = c;
	}

	@Override
	protected ArrayList<NewsStory> doInBackground(Integer... params) {
		int type = params[0];
		ArrayList<NewsStory> list = new ArrayList<NewsStory>();
		try {
			int user_id = mContext.getSharedPreferences(PREFS_NAME, 0).getInt("user_id", 0);
			int session_id = mContext.getSharedPreferences(PREFS_NAME, 0).getInt("session_id", 0);
			String spec = "http://" + BASE + "/getArticles/" + user_id + "/" + session_id + "/" + categories[type];
			System.out.println("SPEC: " + spec);
			URL url = new URL(spec);
			HttpURLConnection urlConnection = (HttpURLConnection) url
					.openConnection();
			BufferedReader reader = new BufferedReader(new InputStreamReader(
					urlConnection.getInputStream()), 1024 * 16);
			StringBuffer buffer = new StringBuffer();
			String line;
			while ((line = reader.readLine()) != null) {
				buffer.append(line);
			}
			JSONArray artlist = new JSONObject(buffer.toString())
					.getJSONArray("article_list");
			JSONObject tmp;
			for (int i = 0; i < artlist.length(); i++) {
				tmp = artlist.getJSONObject(i);
				if (tmp.getString("description").length() != 0) {
					list.add(new NewsStory(tmp.getString("title"), tmp.getString("description"), tmp.getString("date"), tmp.getString("url")));
					publishProgress(new NewsStory(tmp.getString("title"), tmp.getString("description"), tmp.getString("date"), tmp.getString("url")));
				}
			}
		} catch (ConnectException e) {
			conn_fail = true;
			e.printStackTrace();
		} catch (IOException e) {
			conn_fail = true;
			e.printStackTrace();
		} catch (JSONException e) {
			e.printStackTrace();
		}
		return list;
	}
	
	@Override
	protected void onProgressUpdate(NewsStory... ns) {
		System.out.println(ns[0].news_title);
		caller_frag.na.add(ns[0]);
	}

	@Override
	protected void onPreExecute() {
		caller_frag.na.clear();
		caller_frag.setListShown(false);
	}

	@Override
	protected void onPostExecute(ArrayList<NewsStory> result) {
		if(conn_fail) {
			Toast.makeText(mContext, CONNECTION_FAILURE_MSG, Toast.LENGTH_LONG).show();
		} else {
			Toast.makeText(mContext, "DONE!", Toast.LENGTH_LONG).show();
			caller_frag.setListShown(true);
		}
	}
}
