package com.example.snipping;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.PorterDuff;
import android.graphics.PorterDuffXfermode;
import android.graphics.RectF;
import android.view.MotionEvent;
import android.view.View;
import androidx.core.content.ContextCompat;

public class SnippingOverlayView extends View {

    private final Paint paint;
    private final Paint transparentPaint;
    private final Paint borderPaint;
    private final RectF rect;
    private float startX, startY;
    private final SnippingService service;

    public SnippingOverlayView(Context context, SnippingService service) {
        super(context);
        this.service = service;

        paint = new Paint();
        paint.setColor(Color.parseColor("#80000000")); // Semi-transparent black

        transparentPaint = new Paint();
        transparentPaint.setColor(Color.TRANSPARENT);
        transparentPaint.setXfermode(new PorterDuffXfermode(PorterDuff.Mode.CLEAR));

        borderPaint = new Paint();
        borderPaint.setColor(ContextCompat.getColor(context, R.color.dark_purple_loading));
        borderPaint.setStyle(Paint.Style.STROKE);
        borderPaint.setStrokeWidth(5f); // 5 pixel border
        borderPaint.setAntiAlias(true);

        rect = new RectF();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        canvas.drawRect(0, 0, getWidth(), getHeight(), paint);
        if (!rect.isEmpty()) {
            canvas.drawRect(rect, transparentPaint);
            canvas.drawRect(rect, borderPaint);
        }
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        float x = event.getX();
        float y = event.getY();

        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                startX = x;
                startY = y;
                rect.set(startX, startY, startX, startY);
                invalidate();
                break;
            case MotionEvent.ACTION_MOVE:
                rect.set(Math.min(startX, x), Math.min(startY, y), Math.max(startX, x), Math.max(startY, y));
                invalidate();
                break;
            case MotionEvent.ACTION_UP:
                if (rect.width() > 10 && rect.height() > 10) {
                    service.onCapture((int) rect.left, (int) rect.top, (int) rect.width(), (int) rect.height());
                }
                break;
        }
        return true;
    }
}
