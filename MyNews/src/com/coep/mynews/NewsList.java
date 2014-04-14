package com.coep.mynews;

import android.app.ActionBar;
import android.app.ActionBar.Tab;
import android.app.Activity;
import android.app.Fragment;
import android.app.FragmentTransaction;
import android.os.Bundle;

public class NewsList extends Activity implements Constants {
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		final ActionBar bar = getActionBar();
		bar.setNavigationMode(ActionBar.NAVIGATION_MODE_TABS);
		bar.setDisplayOptions(0, ActionBar.DISPLAY_SHOW_TITLE);
		bar.addTab(bar.newTab().setText("Top News").setTabListener(new TabListener()).setTag(Integer.valueOf(iTOP_NEWS)));
		bar.addTab(bar.newTab().setText("Business").setTabListener(new TabListener()).setTag(Integer.valueOf(iBUSINESS)));
		bar.addTab(bar.newTab().setText("Sport").setTabListener(new TabListener()).setTag(Integer.valueOf(iSPORT)));
		bar.addTab(bar.newTab().setText("Technology").setTabListener(new TabListener()).setTag(Integer.valueOf(iTECH)));
		bar.addTab(bar.newTab().setText("World").setTabListener(new TabListener()).setTag(Integer.valueOf(iWORLD)));
	
		setContentView(R.layout.activity_newslist);
		
	}
	
	@Override
	protected void onStart() {
		super.onStart();
		//invalidate old or non existent session_id, regenerate new one
	}
	
	public class TabListener implements android.app.ActionBar.TabListener {

		@Override
		public void onTabReselected(Tab tab, FragmentTransaction ft) {
			
		}

		@Override
		public void onTabSelected(Tab tab, FragmentTransaction ft) {
			int type = (Integer) tab.getTag();
			ft.replace(R.id.fragment_content, NewsListFragment.createNewsListFragment(type));
		}

		@Override
		public void onTabUnselected(Tab tab, FragmentTransaction ft) {
		}

	}

	
}
