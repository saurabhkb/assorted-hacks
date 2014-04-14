package com.coep.mynews;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.TextView;

public class NewsAdapter extends ArrayAdapter<NewsStory> {
	private Context mContext;
	private LayoutInflater mInflater;

	public NewsAdapter(Context context, int textViewResourceId) {
		super(context, textViewResourceId);
		mContext = context;
		mInflater = (LayoutInflater) mContext.getSystemService(Context.LAYOUT_INFLATER_SERVICE);
	}

	@Override
	public View getView(int position, View v, ViewGroup parent) {
		if(v == null) {
			v = mInflater.inflate(R.layout.newsheadline, null, false);
		}
		NewsStory n = getItem(position);
		TextView ntitle = (TextView) v.findViewById(R.id.news_title);
		TextView nsummary = (TextView) v.findViewById(R.id.news_summary);
		TextView ndate = (TextView) v.findViewById(R.id.news_date);
		TextView nlink = (TextView) v.findViewById(R.id.news_url);
		ntitle.setText(n.news_title);
		nsummary.setText(n.news_summary);
		ndate.setText(n.news_date);
		nlink.setText(n.news_url);
		return v;
	}

}
