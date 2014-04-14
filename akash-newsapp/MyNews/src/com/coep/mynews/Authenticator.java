package com.coep.mynews;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.ConnectException;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;

import org.json.JSONException;
import org.json.JSONObject;

import android.app.AlertDialog;
import android.app.ActionBar.Tab;
import android.content.Context;
import android.content.SharedPreferences.Editor;
import android.os.AsyncTask;
import android.util.Log;

public class Authenticator extends AsyncTask<Integer, Integer, Integer> implements Constants {

	Context mContext;
	boolean conn_fail = false;
	public Authenticator(Context c) {
		mContext = c;
	}
	@Override
	protected Integer doInBackground(Integer... params) {
		try {
			int user_id = mContext.getSharedPreferences(PREFS_NAME, 0).getInt("user_id", 0);
			String spec = "http://" + BASE + "/auth/" + user_id;
			System.out.println(spec);
			URL url = new URL(spec);
			HttpURLConnection urlConnection = (HttpURLConnection) url.openConnection();
			BufferedReader reader = new BufferedReader(new InputStreamReader(
					urlConnection.getInputStream()), 1024 * 16);
			StringBuffer buffer = new StringBuffer();
			String line;
			while ((line = reader.readLine()) != null) {
				buffer.append(line);
			}
			JSONObject auth = new JSONObject(buffer.toString());
			Editor e = mContext.getSharedPreferences(PREFS_NAME, 0).edit();
			if((Integer)auth.get("user_id") != user_id) {
				e.putInt("user_id", (Integer)auth.get("user_id"));
			}
			e.putInt("session_id", (Integer)auth.get("session_id"));
			e.apply();
		} catch (ConnectException e) {
			conn_fail = true;
		} catch (IOException e) {
			conn_fail = true;
			e.printStackTrace();
		} catch (JSONException e) {
			e.printStackTrace();
		}
		return null;
	}
	
	@Override
	protected void onPostExecute(Integer result) {
		if(conn_fail) {
		} else {
		}
	}
}