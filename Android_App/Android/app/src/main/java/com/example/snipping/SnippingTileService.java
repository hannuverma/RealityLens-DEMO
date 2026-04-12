package com.example.snipping;

import android.app.PendingIntent;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;
import android.service.quicksettings.TileService;

public class SnippingTileService extends TileService {

    public static final String PREFS_NAME = "SnippingPrefs";
    public static final String KEY_TILE_ADDED = "tile_added";

    @Override
    public void onTileAdded() {
        super.onTileAdded();
        setTileAddedStatus(true);
    }

    @Override
    public void onTileRemoved() {
        super.onTileRemoved();
        setTileAddedStatus(false);
    }

    private void setTileAddedStatus(boolean added) {
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        prefs.edit().putBoolean(KEY_TILE_ADDED, added).apply();
    }

    @Override
    public void onClick() {
        super.onClick();
        Intent intent = new Intent(this, MainActivity.class);
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            PendingIntent pendingIntent = PendingIntent.getActivity(this, 0, intent, PendingIntent.FLAG_IMMUTABLE);
            startActivityAndCollapse(pendingIntent);
        } else {
            startActivityAndCollapse(intent);
        }
    }
}
