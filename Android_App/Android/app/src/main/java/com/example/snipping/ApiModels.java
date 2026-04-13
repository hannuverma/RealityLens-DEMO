package com.example.snipping;

import com.google.gson.annotations.SerializedName;
import java.util.List;

public class ApiModels {

    public static class SnipApiRequest {
        @SerializedName("file")
        private final String file;

        public SnipApiRequest(String file) {
            this.file = file;
        }

        public String getFile() {
            return file;
        }
    }

    public static class SnipApiResponse {
        @SerializedName("claim")
        private String claim;

        @SerializedName("reality_score")
        private Double realityScore;

        @SerializedName("confidence")
        private Double confidence;

        @SerializedName("verdict")
        private String verdict;

        @SerializedName("explanation")
        private String explanation;

        public String getClaim() { return claim; }
        public Double getRealityScore() { return realityScore; }
        public Double getConfidence() { return confidence; }
        public String getVerdict() { return verdict; }
        public String getExplanation() { return explanation; }
    }

    public static class ChatResponse {
        @SerializedName("response")
        private String response;

        public String getResponse() {
            return response;
        }
    }
}
