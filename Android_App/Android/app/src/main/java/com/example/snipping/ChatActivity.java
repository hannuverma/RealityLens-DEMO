package com.example.snipping;

import android.os.Bundle;
import android.util.Log;
import android.widget.Toast;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import com.google.ai.client.generativeai.type.GenerateContentResponse;
import com.google.android.material.floatingactionbutton.FloatingActionButton;
import com.google.android.material.textfield.TextInputEditText;
import com.google.common.util.concurrent.FutureCallback;
import com.google.common.util.concurrent.Futures;
import com.google.common.util.concurrent.ListenableFuture;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Executors;

public class ChatActivity extends AppCompatActivity {

    private static final String TAG = "ChatActivity";
    private ChatAdapter adapter;
    private final List<ChatMessage> messages = new ArrayList<>();
    private String contextExplanation = "";
    private GeminiClient geminiClient;
    private RecyclerView recyclerView;
    private boolean isWaitingForResponse = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_chat);

        contextExplanation = getIntent().getStringExtra("EXPLANATION");
        if (contextExplanation == null) contextExplanation = "";

        recyclerView = findViewById(R.id.chatRecyclerView);
        TextInputEditText edtMessage = findViewById(R.id.edtMessage);
        FloatingActionButton btnSend = findViewById(R.id.btnSend);
        
        androidx.appcompat.widget.Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        if (getSupportActionBar() != null) {
            getSupportActionBar().setDisplayHomeAsUpEnabled(true);
            getSupportActionBar().setTitle("Gemini Assistant");
        }
        toolbar.setNavigationOnClickListener(v -> finish());

        adapter = new ChatAdapter(messages);
        recyclerView.setLayoutManager(new LinearLayoutManager(this));
        recyclerView.setAdapter(adapter);

        geminiClient = new GeminiClient();

        // Initial welcome message
        addMessage("Hello! I'm your Gemini-powered Assistant. I've reviewed the verification results. How can I help you understand them better?", false);

        btnSend.setOnClickListener(v -> {
            if (isWaitingForResponse) {
                Toast.makeText(this, "Please wait for a response...", Toast.LENGTH_SHORT).show();
                return;
            }
            if (edtMessage.getText() == null) return;
            String text = edtMessage.getText().toString().trim();
            if (!text.isEmpty()) {
                addMessage(text, true);
                edtMessage.setText("");
                getGeminiResponse(text);
            }
        });
    }

    private void addMessage(String text, boolean isUser) {
        messages.add(new ChatMessage(text, isUser));
        adapter.notifyItemInserted(messages.size() - 1);
        recyclerView.smoothScrollToPosition(messages.size() - 1);
    }

    private void removeLastMessage() {
        if (!messages.isEmpty()) {
            int position = messages.size() - 1;
            messages.remove(position);
            adapter.notifyItemRemoved(position);
        }
    }

    private void getGeminiResponse(String userQuery) {
        isWaitingForResponse = true;
        
        // Show "Thinking..." message
        addMessage("Thinking...", false);
        
        String combinedPrompt = "You are a helpful AI assistant for the 'Reality Lens' app. " +
                "The following is an analysis of a captured image snippet: " + contextExplanation + 
                "\n\nHere is the conversation history:\n" + buildHistory() +
                "\nUser Question: " + userQuery +
                "\nPlease provide a clear and helpful response based on the analysis context.";

        ListenableFuture<GenerateContentResponse> future = geminiClient.getResponse(combinedPrompt);
        
        Futures.addCallback(future, new FutureCallback<GenerateContentResponse>() {
            @Override
            public void onSuccess(GenerateContentResponse result) {
                runOnUiThread(() -> {
                    isWaitingForResponse = false;
                    // Remove "Thinking..." message before adding the real response
                    removeLastMessage();
                    
                    String text = result.getText();
                    if (text != null && !text.isEmpty()) {
                        addMessage(text, false);
                    } else {
                        addMessage("Gemini returned an empty response.", false);
                    }
                });
            }

            @Override
            public void onFailure(@NonNull Throwable t) {
                runOnUiThread(() -> {
                    isWaitingForResponse = false;
                    // Remove "Thinking..." message on error too
                    removeLastMessage();
                    
                    addMessage("Error connecting to Gemini: " + t.getMessage(), false);
                    Log.e(TAG, "Gemini API Failure", t);
                });
            }
        }, Executors.newSingleThreadExecutor());
    }

    private String buildHistory() {
        StringBuilder history = new StringBuilder();
        // Skip initial welcome message at index 0 and exclude "Thinking..."
        for (int i = 1; i < messages.size(); i++) {
            ChatMessage msg = messages.get(i);
            // Don't include "Thinking..." in the history sent to the AI
            if (msg.getMessage().equals("Thinking...") && !msg.isUser()) continue;

            history.append(msg.isUser() ? "User: " : "Assistant: ")
                   .append(msg.getMessage())
                   .append("\n");
        }
        return history.toString();
    }
}
