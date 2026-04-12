package com.example.snipping;

import okhttp3.MultipartBody;
import retrofit2.Call;
import retrofit2.http.Field;
import retrofit2.http.FormUrlEncoded;
import retrofit2.http.Multipart;
import retrofit2.http.POST;
import retrofit2.http.Part;

public interface SnipApiService {
    @Multipart
    @POST("ai_client")
    Call<ApiModels.SnipApiResponse> analyzeSnip(@Part MultipartBody.Part file);

    @FormUrlEncoded
    @POST("chat")
    Call<ApiModels.ChatResponse> getChatResponse(
        @Field("message") String message,
        @Field("context") String context
    );
}
