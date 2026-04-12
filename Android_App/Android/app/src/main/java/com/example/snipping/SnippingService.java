package com.example.snipping;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.graphics.Bitmap;
import android.graphics.PixelFormat;
import android.media.projection.MediaProjection;
import android.media.projection.MediaProjectionManager;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.util.Base64;
import android.view.ContextThemeWrapper;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import android.widget.Toast;

import androidx.annotation.Nullable;
import androidx.core.app.NotificationCompat;
import androidx.core.content.ContextCompat;

import com.google.android.material.progressindicator.LinearProgressIndicator;

import java.io.ByteArrayOutputStream;
import java.io.IOException;

import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.RequestBody;
import okhttp3.ResponseBody;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class SnippingService extends Service {

    public static final String ACTION_SNIP_CAPTURED = "com.example.snipping.ACTION_SNIP_CAPTURED";
    public static final String EXTRA_SNIP_BITMAP_PATH = "EXTRA_SNIP_BITMAP_PATH";
    public static final String ACTION_SNIP_API_RESULT = "com.example.snipping.ACTION_SNIP_API_RESULT";
    public static final String EXTRA_API_CLAIM = "EXTRA_API_CLAIM";
    public static final String EXTRA_API_SCORE = "EXTRA_API_SCORE";
    public static final String EXTRA_API_VERDICT = "EXTRA_API_VERDICT";
    public static final String EXTRA_API_CONFIDENCE = "EXTRA_API_CONFIDENCE";
    public static final String EXTRA_API_EXPLANATION = "EXTRA_API_EXPLANATION";
    public static final String EXTRA_START_CAPTURE = "EXTRA_START_CAPTURE";

    private static final String CHANNEL_ID = "SnippingChannel";
    private static final String RESULT_CHANNEL_ID = "ResultChannel";
    private WindowManager windowManager;
    private MediaProjection mediaProjection;
    private MediaProjectionManager projectionManager;
    private View overlayView;
    private LinearProgressIndicator overlayLoadingBar;
    private int resultCode;
    private Intent data;
    private boolean isCapturing = false;

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannels();
        windowManager = (WindowManager) getSystemService(WINDOW_SERVICE);
        projectionManager = (MediaProjectionManager) getSystemService(MEDIA_PROJECTION_SERVICE);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && intent.hasExtra("RESULT_CODE")) {
            resultCode = intent.getIntExtra("RESULT_CODE", 0);
            data = intent.getParcelableExtra("DATA");

            // Fix SecurityException: startForeground FIRST
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                startForeground(1, getNotification(), ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION);
            } else {
                startForeground(1, getNotification());
            }

            if (mediaProjection != null) {
                mediaProjection.stop();
            }
            mediaProjection = projectionManager.getMediaProjection(resultCode, data);
            isCapturing = true;
            showOverlay();
        } else {
            startForeground(1, getNotification());
        }
        
        return START_STICKY;
    }

    private void showOverlay() {
        WindowManager.LayoutParams params = new WindowManager.LayoutParams(
                WindowManager.LayoutParams.MATCH_PARENT,
                WindowManager.LayoutParams.MATCH_PARENT,
                Build.VERSION.SDK_INT >= Build.VERSION_CODES.O ?
                        WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY :
                        WindowManager.LayoutParams.TYPE_PHONE,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE | WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
                PixelFormat.TRANSLUCENT);

        overlayView = new SnippingOverlayView(this, this);
        windowManager.addView(overlayView, params);
    }

    private void showOverlayLoadingBar() {
        if (overlayLoadingBar != null) return;

        WindowManager.LayoutParams params = new WindowManager.LayoutParams(
                WindowManager.LayoutParams.MATCH_PARENT,
                WindowManager.LayoutParams.WRAP_CONTENT,
                Build.VERSION.SDK_INT >= Build.VERSION_CODES.O ?
                        WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY :
                        WindowManager.LayoutParams.TYPE_PHONE,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE | WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE | WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
                PixelFormat.TRANSLUCENT);
        params.gravity = Gravity.TOP;

        // Fix IllegalArgumentException: wrap context in Material theme
        ContextThemeWrapper themedContext = new ContextThemeWrapper(this, R.style.Theme_Snipping);
        overlayLoadingBar = new LinearProgressIndicator(themedContext);
        overlayLoadingBar.setIndeterminate(true);
        // Set color to dark purple
        overlayLoadingBar.setIndicatorColor(ContextCompat.getColor(this, R.color.dark_purple_loading));
        overlayLoadingBar.setTrackColor(0x33FFFFFF);

        windowManager.addView(overlayLoadingBar, params);
    }

    private void removeOverlayLoadingBar() {
        if (overlayLoadingBar != null) {
            windowManager.removeView(overlayLoadingBar);
            overlayLoadingBar = null;
        }
    }

    public void onCapture(int x, int y, int width, int height) {
        if (overlayView != null) {
            windowManager.removeView(overlayView);
            overlayView = null;
        }
        isCapturing = false;
        
        // Ensure service is still in foreground
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(1, getNotification(), ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION);
        } else {
            startForeground(1, getNotification());
        }

        CaptureHelper.captureScreen(this, mediaProjection, x, y, width, height, bitmap -> {
            if (bitmap != null) {
                uploadToApi(bitmap);
            }
        });
    }

    private void uploadToApi(Bitmap bitmap) {
        new Handler(Looper.getMainLooper()).post(() -> {
            Toast.makeText(this, "The image has been sent to the server, please wait for the results.", Toast.LENGTH_LONG).show();
        });

        showOverlayLoadingBar();

        Bitmap resizedBitmap = scaleBitmap(bitmap, 1024);
        byte[] imageBytes = bitmapToJpegBytes(resizedBitmap);
        
        RequestBody requestFile = RequestBody.create(MediaType.parse("image/jpeg"), imageBytes);
        MultipartBody.Part filePart = MultipartBody.Part.createFormData("file", "image.jpg", requestFile);

        ApiClient.getService().analyzeSnip(filePart).enqueue(new Callback<ApiModels.SnipApiResponse>() {
            @Override
            public void onResponse(Call<ApiModels.SnipApiResponse> call, Response<ApiModels.SnipApiResponse> response) {
                removeOverlayLoadingBar();
                
                Intent resultIntent = new Intent(SnippingService.this, MainActivity.class);
                resultIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
                
                if (response.isSuccessful() && response.body() != null) {
                    ApiModels.SnipApiResponse body = response.body();
                    resultIntent.putExtra(EXTRA_API_CLAIM, body.getClaim());
                    resultIntent.putExtra(EXTRA_API_SCORE, String.valueOf(body.getRealityScore()));
                    resultIntent.putExtra(EXTRA_API_CONFIDENCE, String.valueOf(body.getConfidence()));
                    resultIntent.putExtra(EXTRA_API_VERDICT, body.getVerdict());
                    resultIntent.putExtra(EXTRA_API_EXPLANATION, body.getExplanation());
                    resultIntent.putExtra("CLAIM", "SUCCESS");
                    
                    String contentText = String.format("The results have been generated. Reality Score: %.2f, Confidence: %.2f", 
                            body.getRealityScore(), body.getConfidence());
                    showResultNotification(resultIntent, contentText);
                } else {
                    String errorMsg = "API Error " + response.code();
                    try {
                        if (response.errorBody() != null) {
                            errorMsg += ": " + response.errorBody().string();
                        }
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                    resultIntent.putExtra(EXTRA_API_CLAIM, errorMsg);
                    resultIntent.putExtra("CLAIM", "ERROR");
                    showResultNotification(resultIntent, "Error generating results");
                }
            }

            @Override
            public void onFailure(Call<ApiModels.SnipApiResponse> call, Throwable t) {
                removeOverlayLoadingBar();
                Intent resultIntent = new Intent(SnippingService.this, MainActivity.class);
                resultIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
                resultIntent.putExtra(EXTRA_API_CLAIM, "Network Failure: " + t.getMessage());
                resultIntent.putExtra("CLAIM", "ERROR");
                showResultNotification(resultIntent, "Result generation failed");
            }
        });
    }

    private void showResultNotification(Intent resultIntent, String message) {
        PendingIntent pendingIntent = PendingIntent.getActivity(this, 2, resultIntent, 
                PendingIntent.FLAG_UPDATE_CURRENT | (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M ? PendingIntent.FLAG_IMMUTABLE : 0));

        Notification notification = new NotificationCompat.Builder(this, RESULT_CHANNEL_ID)
                .setSmallIcon(R.drawable.reality_lens_icon)
                .setContentTitle("Reality Lens")
                .setContentText(message)
                .setStyle(new NotificationCompat.BigTextStyle().bigText(message))
                .setAutoCancel(true)
                .setContentIntent(pendingIntent)
                .setPriority(NotificationCompat.PRIORITY_HIGH)
                .build();

        NotificationManager manager = getSystemService(NotificationManager.class);
        manager.notify(2, notification);
    }

    private Bitmap scaleBitmap(Bitmap bm, int maxWidth) {
        int width = bm.getWidth();
        int height = bm.getHeight();

        if (width <= maxWidth) return bm;

        float aspectRatio = (float) width / (float) height;
        int newWidth = maxWidth;
        int newHeight = Math.round(maxWidth / aspectRatio);

        return Bitmap.createScaledBitmap(bm, newWidth, newHeight, true);
    }

    private byte[] bitmapToJpegBytes(Bitmap bitmap) {
        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
        bitmap.compress(Bitmap.CompressFormat.JPEG, 80, outputStream);
        return outputStream.toByteArray();
    }

    private void createNotificationChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationManager manager = getSystemService(NotificationManager.class);
            
            NotificationChannel serviceChannel = new NotificationChannel(
                    CHANNEL_ID,
                    "Snipping Service Channel",
                    NotificationManager.IMPORTANCE_LOW
            );
            manager.createNotificationChannel(serviceChannel);

            NotificationChannel resultChannel = new NotificationChannel(
                    RESULT_CHANNEL_ID,
                    "Verification Results",
                    NotificationManager.IMPORTANCE_HIGH
            );
            manager.createNotificationChannel(resultChannel);
        }
    }

    private Notification getNotification() {
        Intent snipIntent = new Intent(this, MainActivity.class);
        snipIntent.putExtra(EXTRA_START_CAPTURE, true);
        snipIntent.putExtra("FORCE_SHOW_UI", false);
        snipIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        
        PendingIntent snipPendingIntent = PendingIntent.getActivity(this, 1, snipIntent, 
                PendingIntent.FLAG_UPDATE_CURRENT | (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M ? PendingIntent.FLAG_IMMUTABLE : 0));

        NotificationCompat.Builder builder = new NotificationCompat.Builder(this, CHANNEL_ID)
                .setContentTitle("Reality Lens")
                .setContentText(isCapturing ? "Snipping in progress..." : "Ready to snip")
                .setSmallIcon(R.drawable.reality_lens_icon)
                .setOngoing(true)
                .setContentIntent(snipPendingIntent);

        if (!isCapturing) {
            builder.addAction(R.drawable.reality_lens_icon, "Snip Now", snipPendingIntent);
        }

        return builder.build();
    }

    @Nullable
    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        removeOverlayLoadingBar();
        if (mediaProjection != null) {
            mediaProjection.stop();
        }
    }
}
