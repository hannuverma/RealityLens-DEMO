package com.example.snipping;

import android.content.ContentValues;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.PixelFormat;
import android.hardware.display.DisplayManager;
import android.hardware.display.VirtualDisplay;
import android.media.Image;
import android.media.ImageReader;
import android.media.projection.MediaProjection;
import android.net.Uri;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.provider.MediaStore;
import android.util.DisplayMetrics;
import android.view.WindowManager;

import java.io.OutputStream;
import java.nio.ByteBuffer;

public class CaptureHelper {

    public interface CaptureCallback {
        void onCaptureFinished(Bitmap bitmap);
    }

    public static void captureScreen(Context context, MediaProjection mediaProjection, int x, int y, int width, int height, CaptureCallback callback) {
        if (mediaProjection == null) {
            callback.onCaptureFinished(null);
            return;
        }

        // Fix: Register a dummy callback to satisfy IllegalStateException on some Android versions
        mediaProjection.registerCallback(new MediaProjection.Callback() {
            @Override
            public void onStop() {
                super.onStop();
            }
        }, new Handler(Looper.getMainLooper()));

        WindowManager wm = (WindowManager) context.getSystemService(Context.WINDOW_SERVICE);
        DisplayMetrics metrics = new DisplayMetrics();
        wm.getDefaultDisplay().getRealMetrics(metrics);
        int screenWidth = metrics.widthPixels;
        int screenHeight = metrics.heightPixels;
        int density = metrics.densityDpi;

        ImageReader imageReader = ImageReader.newInstance(screenWidth, screenHeight, PixelFormat.RGBA_8888, 2);
        VirtualDisplay virtualDisplay = mediaProjection.createVirtualDisplay("Snipping",
                screenWidth, screenHeight, density,
                DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
                imageReader.getSurface(), null, null);

        new Handler(Looper.getMainLooper()).postDelayed(() -> {
            Image image = imageReader.acquireLatestImage();
            Bitmap capturedBitmap = null;
            if (image != null) {
                capturedBitmap = processImage(image, x, y, width, height, screenWidth, screenHeight);
                if (capturedBitmap != null) {
                    saveBitmapToGallery(context, capturedBitmap);
                }
                image.close();
            }
            virtualDisplay.release();
            imageReader.close();
            callback.onCaptureFinished(capturedBitmap);
        }, 500);
    }

    private static Bitmap processImage(Image image, int x, int y, int width, int height, int screenWidth, int screenHeight) {
        Image.Plane[] planes = image.getPlanes();
        ByteBuffer buffer = planes[0].getBuffer();
        int pixelStride = planes[0].getPixelStride();
        int rowStride = planes[0].getRowStride();
        int rowPadding = rowStride - pixelStride * screenWidth;

        Bitmap bitmap = Bitmap.createBitmap(screenWidth + rowPadding / pixelStride, screenHeight, Bitmap.Config.ARGB_8888);
        bitmap.copyPixelsFromBuffer(buffer);

        int cropX = Math.max(0, x);
        int cropY = Math.max(0, y);
        int cropWidth = Math.min(width, bitmap.getWidth() - cropX);
        int cropHeight = Math.min(height, bitmap.getHeight() - cropY);

        if (cropWidth <= 0 || cropHeight <= 0) return null;

        return Bitmap.createBitmap(bitmap, cropX, cropY, cropWidth, cropHeight);
    }

    private static void saveBitmapToGallery(Context context, Bitmap bitmap) {
        String filename = "Snippet_" + System.currentTimeMillis() + ".png";
        ContentValues values = new ContentValues();
        values.put(MediaStore.Images.Media.DISPLAY_NAME, filename);
        values.put(MediaStore.Images.Media.MIME_TYPE, "image/png");
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            values.put(MediaStore.Images.Media.RELATIVE_PATH, "Pictures/Snippets");
            values.put(MediaStore.Images.Media.IS_PENDING, 1);
        }

        Uri uri = context.getContentResolver().insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values);
        if (uri != null) {
            try (OutputStream out = context.getContentResolver().openOutputStream(uri)) {
                bitmap.compress(Bitmap.CompressFormat.PNG, 100, out);
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                    values.clear();
                    values.put(MediaStore.Images.Media.IS_PENDING, 0);
                    context.getContentResolver().update(uri, values, null, null);
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }
}
