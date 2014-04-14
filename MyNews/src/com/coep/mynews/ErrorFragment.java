package com.coep.mynews;

import android.app.ListFragment;
import android.content.Context;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;

public class ErrorFragment extends ListFragment implements Constants {
	private int type;
	public static ErrorFragment createErrorFragment(int type) {
		ErrorFragment ef = new ErrorFragment();
		Bundle args = new Bundle();
		args.putInt("type", type);
		ef.setArguments(args);
		return ef;
	}
	
	@Override
	public void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		Bundle args = getArguments();
		if(args != null) {
			type = args.getInt("type");
		} else type = UNKNOWN_ERROR;
	}
	
	@Override
	public void onActivityCreated(Bundle savedInstanceState) {
		super.onActivityCreated(savedInstanceState);
		/*setListShown(true);
		LayoutInflater mInflater = (LayoutInflater) getActivity().getSystemService(Context.LAYOUT_INFLATER_SERVICE);
		if(mInflater == null) return;
		LinearLayout article_list_holder = (LinearLayout)getActivity().findViewById(R.id.articles_list);
		article_list_holder.removeAllViews();
		View error_view = mInflater.inflate(R.layout.error_screen, null, false);
		TextView error_msg = (TextView)error_view.findViewById(R.id.error_message);
		switch(type) {
		case CONNECTION_FAILURE:
			error_msg.setText(CONNECTION_FAILURE_MSG);
			break;
		default:
			error_msg.setText(UNKNOWN_ERROR_MSG);
			break;
		}
		article_list_holder.addView(error_view);*/
	}
}
