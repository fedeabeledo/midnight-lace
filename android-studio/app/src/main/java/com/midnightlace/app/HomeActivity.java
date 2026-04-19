package com.midnightlace.app;

import android.content.Intent;
import android.graphics.Typeface;
import android.os.Build;
import android.os.Bundle;
import android.text.SpannableString;
import android.text.Spanned;
import android.text.style.RelativeSizeSpan;
import android.text.style.StyleSpan;
import android.text.style.TypefaceSpan;
import android.text.style.UnderlineSpan;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.res.ResourcesCompat;

import java.util.Objects;

public class HomeActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_home);

        Button btnVerTodas = findViewById(R.id.btn_ver_todas);
        TextView txtSubastaLabel = findViewById(R.id.txt_subasta_label);
        ImageView btnMenu = findViewById(R.id.btn_menu);
        ImageView btnNotif = findViewById(R.id.btn_notif);

        String subasta = getString(R.string.subasta_destacada);
        String destacada = getString(R.string.destacada_italic);
        SpannableString spannable = new SpannableString(subasta + destacada);
        spannable.setSpan(new TypefaceSpan("serif"),
                0, subasta.length(),
                Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            spannable.setSpan(new TypefaceSpan(Objects.requireNonNull(ResourcesCompat.getFont(this, R.font.great_vibes))),
                    subasta.length(), subasta.length() + destacada.length(),
                    Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        }
        spannable.setSpan(new StyleSpan(Typeface.BOLD),
                0, subasta.length(),
                Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        spannable.setSpan(new RelativeSizeSpan(1.3f),
                subasta.length(), subasta.length() + destacada.length(),
                Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        spannable.setSpan(new UnderlineSpan(),
                subasta.length(), subasta.length() + destacada.length(),
                Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);

        txtSubastaLabel.setText(spannable);

        txtSubastaLabel.setText(spannable);

        btnVerTodas.setOnClickListener(v ->
                startActivity(new Intent(HomeActivity.this, AllAuctionsActivity.class)));

        btnMenu.setOnClickListener(v ->
                startActivity(new Intent(HomeActivity.this, WipActivity.class)));

        btnNotif.setOnClickListener(v ->
                startActivity(new Intent(HomeActivity.this, WipActivity.class)));
    }
}
