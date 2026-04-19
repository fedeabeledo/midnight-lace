package com.midnightlace.app;

import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.text.SpannableString;
import android.text.Spanned;
import android.text.TextPaint;
import android.text.method.LinkMovementMethod;
import android.text.style.ClickableSpan;
import android.text.style.UnderlineSpan;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;

public class LoginActivity extends AppCompatActivity {

    private static final String MOCK_PASSWORD = "123";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);

        EditText inputEmail = findViewById(R.id.input_email);
        EditText inputContrasena = findViewById(R.id.input_contrasena);
        Button btnEnviar = findViewById(R.id.btn_enviar);
        TextView txtRegistrate = findViewById(R.id.txt_registrate);
        TextView txtOlvido = findViewById(R.id.txt_olvido);
        ImageView btnMenu = findViewById(R.id.btn_menu);
        ImageView btnNotif = findViewById(R.id.btn_notif);

        btnEnviar.setOnClickListener(v -> {
            String password = inputContrasena.getText().toString();
            if (MOCK_PASSWORD.equals(password)) {
                startActivity(new Intent(LoginActivity.this, HomeActivity.class));
                finish();
            } else {
                Toast.makeText(this, R.string.credenciales_incorrectas, Toast.LENGTH_SHORT).show();
            }
        });

        String noTenes = getString(R.string.no_tenes_cuenta);
        String registrate = getString(R.string.registrate);
        SpannableString spannable = new SpannableString(noTenes + registrate);
        int start = noTenes.length();
        int end = start + registrate.length();
        spannable.setSpan(new ClickableSpan() {
            @Override
            public void onClick(@NonNull View widget) {
                startActivity(new Intent(LoginActivity.this, WipActivity.class));
            }

            @Override
            public void updateDrawState(@NonNull TextPaint ds) {
                super.updateDrawState(ds);
                ds.setColor(getColor(R.color.rojo_oscuro));
                ds.setUnderlineText(true);
            }
        }, start, end, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        txtRegistrate.setText(spannable);
        txtRegistrate.setMovementMethod(LinkMovementMethod.getInstance());
        txtRegistrate.setHighlightColor(Color.TRANSPARENT);

        txtOlvido.setOnClickListener(v ->
                startActivity(new Intent(LoginActivity.this, WipActivity.class)));

        btnMenu.setOnClickListener(v ->
                startActivity(new Intent(LoginActivity.this, WipActivity.class)));

        btnNotif.setOnClickListener(v ->
                startActivity(new Intent(LoginActivity.this, WipActivity.class)));
    }
}
