package com.coep.mynews;

import java.util.ArrayList;
import java.util.concurrent.ExecutionException;

import android.app.ListFragment;
import android.content.Intent;
import android.os.AsyncTask;
import android.os.Bundle;
import android.view.View;
import android.widget.ListView;

public class NewsListFragment extends ListFragment implements Constants {
	private int type;
	NewsAdapter na;
	public static NewsListFragment createNewsListFragment(int type) {
		NewsListFragment nf = new NewsListFragment();
		Bundle args = new Bundle();
		args.putInt("type", type);
		nf.setArguments(args);
		return nf;
	}
	
	@Override
	public void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		na = new NewsAdapter(getActivity(), R.layout.newsheadline);
		Bundle args = getArguments();
		if(args != null) {
			type = args.getInt("type");
		} else type = iTOP_NEWS;	//default
		setListAdapter(na);
	}
	
	@Override
	public void onActivityCreated(Bundle savedInstanceState) {
		System.out.println("called this type:" + type);
		super.onActivityCreated(savedInstanceState);
		AsyncTask<Integer, Integer, ArrayList<NewsStory>> async = new FeedRetriever(getActivity(), this).execute(type);
		try {
			na.addAll(async.get());
		} catch (InterruptedException e) {
			e.printStackTrace();
		} catch (ExecutionException e) {
			e.printStackTrace();
		}
	}
	
	@Override
	public void onListItemClick(ListView l, View v, int position, long id) {
		super.onListItemClick(l, v, position, id);
		NewsStory ns = (NewsStory)getListView().getItemAtPosition(position);
		new LinkClickNotifier(getActivity(), NewsListFragment.this).execute("" + type, ns.news_title, ns.news_summary);
		Intent webIntent = new Intent(getActivity(), WebViewActivity.class);
		webIntent.putExtra("URL", ns.news_url);
		startActivity(webIntent);
	}
}
