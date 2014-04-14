package com.coep.mynews;

public class NewsStory {
	String news_title;
	String news_summary;
	String news_date;
	String news_url;
	
	public NewsStory(String t, String s, String date, String url) {
		news_title = t;
		news_summary = s;
		news_date = date;
		news_url = url;
	}
}
