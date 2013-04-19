package com.coep.mynews;

import java.util.HashMap;
import java.util.Map;

public interface Constants {
	//categories
	String BUSINESS = "BUSINESS";
	String SCIENCE = "SCIENCE";
	String SPORT = "SPORT";
	String TECH = "TECH";
	String WORLD = "WORLD";
	String TOP_NEWS = "TOP_NEWS";
	String ENTERTAINMENT = "BUZZ";
	int iBUSINESS = 0;
	int iSPORT = 2;
	int iTECH = 3;
	int iWORLD = 4;
	int iTOP_NEWS = 5;
	int iENTERTAINMENT = 6;
	String categories[] = {BUSINESS, SCIENCE, SPORT, TECH, WORLD, TOP_NEWS, ENTERTAINMENT};
	static final Map<String , Integer> CATEGORY_MAP = new HashMap<String , Integer>() {{
		put(BUSINESS, 0);
		put(SPORT, 2);
		put(TECH, 3);
		put(WORLD, 4); 
		put(TOP_NEWS, 5);
		put(ENTERTAINMENT, 6);
	}};
	//config data
	String BASE = "10.0.2.2:5000";
	public static final String PREFS_NAME = "CONFIG";
	
	//error codes
	int CONNECTION_FAILURE = 1;
	int UNKNOWN_ERROR = 2;
	
	//error messages
	String CONNECTION_FAILURE_MSG = "Could not connect to server!";
	String UNKNOWN_ERROR_MSG = "Something screwed up!";
}
