package com.example.snipping;

import android.Manifest;
import android.app.StatusBarManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.drawable.Icon;
import android.media.projection.MediaProjectionManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.View;
import android.widget.TextView;
import android.widget.Toast;
import androidx.activity.EdgeToEdge;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import com.google.android.material.button.MaterialButton;
import com.google.android.material.floatingactionbutton.FloatingActionButton;
import com.google.android.material.progressindicator.LinearProgressIndicator;
import java.util.concurrent.Executors;

public class MainActivity extends AppCompatActivity {

    public static final String EXTRA_LOADING = "EXTRA_LOADING";

    private MediaProjectionManager projectionManager;
    private ActivityResultLauncher<Intent> projectionLauncher;
    private ActivityResultLauncher<String> requestPermissionLauncher;

    private TextView txtResult;
    private MaterialButton btnNewSnip;
    private FloatingActionButton btnAiChat;
    private LinearProgressIndicator loadingBar;
    
    // New detailed views
    private View scoresLayout;
    private TextView txtClaimHeader, txtClaimValue;
    private TextView txtRealityValue, txtConfidenceValue;
    private LinearProgressIndicator progressReality, progressConfidence;
    private TextView txtVerdictHeader, txtVerdictValue;
    private TextView txtExplanationHeader, txtExplanationValue;

    private boolean isStartingService = false;
    private boolean isWaitingForOverlay = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        projectionManager = (MediaProjectionManager) getSystemService(Context.MEDIA_PROJECTION_SERVICE);

        projectionLauncher = registerForActivityResult(
                new ActivityResultContracts.StartActivityForResult(),
                result -> {
                    if (result.getResultCode() == RESULT_OK && result.getData() != null) {
                        startSnippingService(result.getResultCode(), result.getData());
                    } else {
                        Toast.makeText(this, "Screen capture permission denied", Toast.LENGTH_SHORT).show();
                        if (!getIntent().hasExtra("CLAIM")) finish();
                    }
                }
        );

        requestPermissionLauncher = registerForActivityResult(new ActivityResultContracts.RequestPermission(), isGranted -> {
            if (isGranted) {
                checkSetup();
            } else {
                Toast.makeText(this, "Notification permission required", Toast.LENGTH_SHORT).show();
                finish();
            }
        });

        handleIntent(getIntent());
    }

    @Override
    protected void onResume() {
        super.onResume();
        // If we were waiting for the user to return from granting overlay permission
        if (isWaitingForOverlay) {
            isWaitingForOverlay = false;
            if (checkOverlayPermission()) {
                checkSetup();
            } else {
                Toast.makeText(this, "Overlay permission is required", Toast.LENGTH_SHORT).show();
            }
        }
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        handleIntent(intent);
    }

    private void handleIntent(Intent intent) {
        if (intent.hasExtra("CLAIM") || intent.hasExtra(EXTRA_LOADING) || intent.getBooleanExtra("FORCE_SHOW_UI", false)) {
            showResultUi();
            if (intent.getBooleanExtra(EXTRA_LOADING, false)) {
                showLoading(true);
            } else {
                showLoading(false);
                displayResults(intent);
            }
        } else {
            checkSetup();
        }
    }

    private void showResultUi() {
        if (txtResult != null) return; // Already inflated

        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_main);

        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (v, insets) -> {
            Insets systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, 0);
            return insets;
        });

        txtResult = findViewById(R.id.txtResult);
        btnNewSnip = findViewById(R.id.btnNewSnip);
        btnAiChat = findViewById(R.id.btnAiChat);
        loadingBar = findViewById(R.id.loadingBar);
        
        scoresLayout = findViewById(R.id.scoresLayout);
        txtClaimHeader = findViewById(R.id.txtClaimHeader);
        txtClaimValue = findViewById(R.id.txtClaimValue);
        txtRealityValue = findViewById(R.id.txtRealityValue);
        txtConfidenceValue = findViewById(R.id.txtConfidenceValue);
        progressReality = findViewById(R.id.progressReality);
        progressConfidence = findViewById(R.id.progressConfidence);
        txtVerdictHeader = findViewById(R.id.txtVerdictHeader);
        txtVerdictValue = findViewById(R.id.txtVerdictValue);
        txtExplanationHeader = findViewById(R.id.txtExplanationHeader);
        txtExplanationValue = findViewById(R.id.txtExplanationValue);

        btnNewSnip.setOnClickListener(v -> {
            projectionLauncher.launch(projectionManager.createScreenCaptureIntent());
        });

        btnAiChat.setOnClickListener(v -> {
            Intent intent = new Intent(this, ChatActivity.class);
            if (txtExplanationValue != null && txtExplanationValue.getVisibility() == View.VISIBLE) {
                intent.putExtra("EXPLANATION", txtExplanationValue.getText().toString());
            }
            startActivity(intent);
        });
    }

    private void showLoading(boolean loading) {
        if (loadingBar != null) {
            loadingBar.setVisibility(loading ? View.VISIBLE : View.GONE);
        }
        if (txtResult != null) {
            txtResult.setVisibility(loading ? View.VISIBLE : View.GONE);
            if (loading) txtResult.setText("Uploading and analyzing image...");
        }
        if (btnAiChat != null) {
            btnAiChat.setVisibility(loading ? View.GONE : View.VISIBLE);
        }
        if (!loading) {
            // Hide detailed views until data is filled
            if (scoresLayout != null) scoresLayout.setVisibility(View.GONE);
            if (txtClaimHeader != null) txtClaimHeader.setVisibility(View.GONE);
            if (txtClaimValue != null) txtClaimValue.setVisibility(View.GONE);
            if (txtVerdictHeader != null) txtVerdictHeader.setVisibility(View.GONE);
            if (txtVerdictValue != null) txtVerdictValue.setVisibility(View.GONE);
            if (txtExplanationHeader != null) txtExplanationHeader.setVisibility(View.GONE);
            if (txtExplanationValue != null) txtExplanationValue.setVisibility(View.GONE);
        }
    }

    private void displayResults(Intent intent) {
        String claim = intent.getStringExtra(SnippingService.EXTRA_API_CLAIM);
        String scoreStr = intent.getStringExtra(SnippingService.EXTRA_API_SCORE);
        String confidenceStr = intent.getStringExtra(SnippingService.EXTRA_API_CONFIDENCE);
        String verdict = intent.getStringExtra(SnippingService.EXTRA_API_VERDICT);
        String explanation = intent.getStringExtra(SnippingService.EXTRA_API_EXPLANATION);

        String status = intent.getStringExtra("CLAIM");
        
        if ("SUCCESS".equals(status)) {
            if (txtResult != null) txtResult.setVisibility(View.GONE);
            
            // Populate and Show Claim
            if (txtClaimHeader != null) txtClaimHeader.setVisibility(View.VISIBLE);
            if (txtClaimValue != null) {
                txtClaimValue.setVisibility(View.VISIBLE);
                txtClaimValue.setText(claim);
            }

            // Populate and Show Verdict
            if (txtVerdictHeader != null) txtVerdictHeader.setVisibility(View.VISIBLE);
            if (txtVerdictValue != null) {
                txtVerdictValue.setVisibility(View.VISIBLE);
                txtVerdictValue.setText(verdict);
            }

            // Determine Color based on Verdict
            int color = ContextCompat.getColor(this, R.color.primary_brand); // Default
            if (verdict != null) {
                String v = verdict.toUpperCase();
                if (v.contains("REAL")) {
                    color = ContextCompat.getColor(this, R.color.verdict_real);
                } else if (v.contains("FAKE")) {
                    color = ContextCompat.getColor(this, R.color.verdict_fake);
                } else if (v.contains("SATIRE")) {
                    color = ContextCompat.getColor(this, R.color.verdict_satire);
                } else if (v.contains("UNREADABLE")) {
                    color = ContextCompat.getColor(this, R.color.verdict_unreadable);
                }
            }

            // Apply colors to text
            if (txtVerdictValue != null) txtVerdictValue.setTextColor(color);
            if (txtRealityValue != null) txtRealityValue.setTextColor(color);
            if (txtConfidenceValue != null) txtConfidenceValue.setTextColor(color);

            // Populate and Show Scores
            if (scoresLayout != null) scoresLayout.setVisibility(View.VISIBLE);
            try {
                float realityScore = Float.parseFloat(scoreStr);
                float confidenceScore = Float.parseFloat(confidenceStr);
                
                if (txtRealityValue != null) txtRealityValue.setText(String.format("%.2f", realityScore));
                if (progressReality != null) {
                    progressReality.setProgress((int) (realityScore * 100));
                    progressReality.setIndicatorColor(color);
                }
                
                if (txtConfidenceValue != null) txtConfidenceValue.setText(String.format("%.2f", confidenceScore));
                if (progressConfidence != null) {
                    progressConfidence.setProgress((int) (confidenceScore * 100));
                    progressConfidence.setIndicatorColor(color);
                }
            } catch (Exception e) {
                // Fallback if parsing fails
            }

            // Populate and Show Explanation
            if (txtExplanationHeader != null) txtExplanationHeader.setVisibility(View.VISIBLE);
            if (txtExplanationValue != null) {
                txtExplanationValue.setVisibility(View.VISIBLE);
                txtExplanationValue.setText(explanation);
            }
            
        } else if ("ERROR".equals(status)) {
            if (txtResult != null) {
                txtResult.setVisibility(View.VISIBLE);
                txtResult.setText(claim); // Contains error message
            }
        } else if (status != null && !status.isEmpty()) {
            if (txtResult != null) {
                txtResult.setVisibility(View.VISIBLE);
                txtResult.setText(status);
            }
        }
    }

    private void checkSetup() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                requestPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS);
                return;
            }
        }

        if (!checkOverlayPermission()) {
            requestOverlayPermission();
            return;
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            SharedPreferences prefs = getSharedPreferences(SnippingTileService.PREFS_NAME, MODE_PRIVATE);
            boolean tileAdded = prefs.getBoolean(SnippingTileService.KEY_TILE_ADDED, false);
            if (!tileAdded) {
                showTileAddDialog();
                return;
            }
        }

        projectionLauncher.launch(projectionManager.createScreenCaptureIntent());
    }

    private void showTileAddDialog() {
        new AlertDialog.Builder(this)
                .setTitle("Add Reality Lens to Quick Settings")
                .setMessage("For quick access, would you like to add the Reality Lens to your notification quick settings tiles?")
                .setPositiveButton("Add Now", (dialog, which) -> requestAddTile())
                .setNegativeButton("Maybe Later", (dialog, which) -> {
                    // Skip and just proceed to capture
                    projectionLauncher.launch(projectionManager.createScreenCaptureIntent());
                })
                .setCancelable(false)
                .show();
    }

    private void requestAddTile() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            StatusBarManager statusBarManager = (StatusBarManager) getSystemService(Context.STATUS_BAR_SERVICE);
            ComponentName componentName = new ComponentName(this, SnippingTileService.class);
            Icon icon = Icon.createWithResource(this, R.drawable.reality_lens_icon);
            statusBarManager.requestAddTileService(componentName, "Reality Lens", icon, Executors.newSingleThreadExecutor(), result -> {
                SharedPreferences prefs = getSharedPreferences(SnippingTileService.PREFS_NAME, MODE_PRIVATE);
                prefs.edit().putBoolean(SnippingTileService.KEY_TILE_ADDED, true).apply();
                // After pinning, automatically proceed to launch the screen capture permission
                runOnUiThread(() -> projectionLauncher.launch(projectionManager.createScreenCaptureIntent()));
            });
        }
    }

    private boolean checkOverlayPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            return Settings.canDrawOverlays(this);
        }
        return true;
    }

    private void requestOverlayPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            isWaitingForOverlay = true;
            Intent intent = new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse("package:" + getPackageName()));
            startActivity(intent);
            Toast.makeText(this, "Please grant overlay permission", Toast.LENGTH_SHORT).show();
        }
    }

    private void startSnippingService(int resultCode, Intent data) {
        isStartingService = true;
        Intent serviceIntent = new Intent(this, SnippingService.class);
        serviceIntent.putExtra("RESULT_CODE", resultCode);
        serviceIntent.putExtra("DATA", data);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(serviceIntent);
        } else {
            startService(serviceIntent);
        }
        finish();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (!isStartingService && isFinishing()) {
            stopService(new Intent(this, SnippingService.class));
        }
    }
}
