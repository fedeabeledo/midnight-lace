package com.midnightlace.app;

import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

public class AllAuctionsActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_all_auctions);

        LinearLayout container = findViewById(R.id.container_subastas);
        ImageView btnMenu = findViewById(R.id.btn_menu);
        ImageView btnNotif = findViewById(R.id.btn_notif);

        btnMenu.setOnClickListener(v ->
                startActivity(new Intent(this, WipActivity.class)));
        btnNotif.setOnClickListener(v ->
                startActivity(new Intent(this, WipActivity.class)));

        int[][] auctions = {
                {R.drawable.subasta_gyaru, R.string.subasta_gyaru, R.string.gyaru_fecha, R.string.gyaru_lugar, R.string.gyaru_piezas, 0},
                {R.drawable.subasta_y2k, R.string.subasta_y2k, R.string.y2k_fecha, R.string.y2k_lugar, R.string.y2k_piezas, 0},
                {R.drawable.subasta_sweet_dreams, R.string.subasta_sweet_dreams, R.string.sweet_dreams_fecha, R.string.sweet_dreams_lugar, R.string.sweet_dreams_piezas, 0},
                {R.drawable.subasta_gothic_night, R.string.subasta_gothic_night, R.string.gothic_night_fecha, R.string.gothic_night_lugar, R.string.gothic_night_piezas, 0},
                {R.drawable.subasta_strawberry_bloom, R.string.subasta_strawberry_bloom, R.string.strawberry_bloom_fecha, R.string.strawberry_bloom_lugar, R.string.strawberry_bloom_piezas, 0},
                {R.drawable.subasta_visual_eclipse, R.string.subasta_visual_eclipse, R.string.visual_eclipse_fecha, R.string.visual_eclipse_lugar, R.string.visual_eclipse_piezas, 0},
                {R.drawable.subasta_ganguro, R.string.subasta_ganguro, R.string.ganguro_fecha, R.string.ganguro_lugar, R.string.ganguro_piezas, 1},
                {R.drawable.subasta_fairy_magic, R.string.subasta_fairy_magic, R.string.fairy_magic_fecha, R.string.fairy_magic_lugar, R.string.fairy_magic_piezas, 2},
        };

        LayoutInflater inflater = LayoutInflater.from(this);

        for (int[] auction : auctions) {
            View card = inflater.inflate(R.layout.item_auction, container, false);

            ImageView imgSubasta = card.findViewById(R.id.img_subasta);
            TextView txtNombre = card.findViewById(R.id.txt_nombre);
            TextView txtFecha = card.findViewById(R.id.txt_fecha);
            TextView txtLugar = card.findViewById(R.id.txt_lugar);
            TextView txtPiezas = card.findViewById(R.id.txt_piezas);
            TextView badgeEstado = card.findViewById(R.id.badge_estado);

            BitmapFactory.Options opts = new BitmapFactory.Options();
            opts.inSampleSize = 2;
            Bitmap bmp = BitmapFactory.decodeResource(getResources(), auction[0], opts);
            imgSubasta.setImageBitmap(bmp);
            imgSubasta.setContentDescription(getString(auction[1]));
            txtNombre.setText(auction[1]);
            txtFecha.setText(auction[2]);
            txtLugar.setText(auction[3]);
            txtPiezas.setText(auction[4]);

            int estado = auction[5];
            switch (estado) {
                case 0:
                    badgeEstado.setText(R.string.estado_en_curso);
                    badgeEstado.setBackgroundResource(R.drawable.badge_en_curso);
                    badgeEstado.setTextColor(getColor(R.color.blanco));
                    break;
                case 1:
                    badgeEstado.setText(R.string.estado_programada);
                    badgeEstado.setBackgroundResource(R.drawable.badge_programada);
                    badgeEstado.setTextColor(getColor(R.color.blanco));
                    break;
                case 2:
                    badgeEstado.setText(R.string.estado_finalizada);
                    badgeEstado.setBackgroundResource(R.drawable.badge_finalizada);
                    badgeEstado.setTextColor(getColor(R.color.blanco));
                    break;
            }

            card.setOnClickListener(v ->
                    startActivity(new Intent(AllAuctionsActivity.this, WipActivity.class)));

            container.addView(card);
        }
    }
}
