package com.midnightlace.app;

import android.content.Intent;
import android.os.Bundle;
import android.widget.ImageView;

import androidx.appcompat.app.AppCompatActivity;

public class WipActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_wip);

        ImageView btnMenu = findViewById(R.id.btn_menu);
        ImageView btnNotif = findViewById(R.id.btn_notif);

        btnMenu.setOnClickListener(v -> finish());
        btnNotif.setOnClickListener(v -> finish());
    }
}
