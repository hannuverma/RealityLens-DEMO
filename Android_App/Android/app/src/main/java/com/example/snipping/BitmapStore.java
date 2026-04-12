package com.example.snipping;

import android.content.Context;
import android.graphics.Bitmap;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;

public final class BitmapStore {

    private static final String DIRECTORY = "snips";

    private BitmapStore() {
    }

    public static String save(Context context, Bitmap bitmap) {
        File dir = new File(context.getCacheDir(), DIRECTORY);
        if (!dir.exists() && !dir.mkdirs()) {
            return null;
        }

        File file = new File(dir, "snip_" + System.currentTimeMillis() + ".png");
        try (FileOutputStream out = new FileOutputStream(file)) {
            bitmap.compress(Bitmap.CompressFormat.PNG, 100, out);
            out.flush();
            return file.getAbsolutePath();
        } catch (IOException e) {
            return null;
        }
    }

    public static Bitmap load(String path) {
        return android.graphics.BitmapFactory.decodeFile(path);
    }
}
