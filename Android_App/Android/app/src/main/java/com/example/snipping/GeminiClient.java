package com.example.snipping;

import com.google.ai.client.generativeai.GenerativeModel;
import com.google.ai.client.generativeai.java.GenerativeModelFutures;
import com.google.ai.client.generativeai.type.BlockThreshold;
import com.google.ai.client.generativeai.type.Content;
import com.google.ai.client.generativeai.type.GenerateContentResponse;
import com.google.ai.client.generativeai.type.GenerationConfig;
import com.google.ai.client.generativeai.type.HarmCategory;
import com.google.ai.client.generativeai.type.RequestOptions;
import com.google.ai.client.generativeai.type.SafetySetting;
import com.google.common.util.concurrent.ListenableFuture;

import java.util.Collections;

public class GeminiClient {
    // Note: In a production app, you should NOT hardcode your API key.
    // Use a backend or local properties / BuildConfig for security.
    private static final String API_KEY = "AIzaSyAPeXhm-IjTJYEmoFl_OKUs_sjrYQtARAU";
    private final GenerativeModelFutures model;

    public GeminiClient() {
        GenerationConfig.Builder configBuilder = new GenerationConfig.Builder();
        configBuilder.temperature = 0.7f;
        configBuilder.topK = 40;
        configBuilder.topP = 0.95f;
        configBuilder.maxOutputTokens = 1024;

        SafetySetting safetySetting = new SafetySetting(HarmCategory.HARASSMENT, BlockThreshold.MEDIUM_AND_ABOVE);

        // RequestOptions constructor takes (Long timeout, String apiVersion)
        RequestOptions requestOptions = new RequestOptions(null, "v1beta");

        GenerativeModel gm = new GenerativeModel(
                "gemini-2.5-flash-lite",
                API_KEY,
                configBuilder.build(),
                Collections.singletonList(safetySetting),
                requestOptions
        );

        this.model = GenerativeModelFutures.from(gm);
    }

    public ListenableFuture<GenerateContentResponse> getResponse(String prompt) {
        Content content = new Content.Builder()
                .addText(prompt)
                .build();
        return model.generateContent(content);
    }
}
