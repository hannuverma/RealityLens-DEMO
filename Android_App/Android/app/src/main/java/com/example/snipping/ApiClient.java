package com.example.snipping;

import java.util.concurrent.TimeUnit;
import okhttp3.OkHttpClient;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;

public final class ApiClient {

    private static final String BASE_URL = "https://realitylens-demo.onrender.com/";
    private static volatile SnipApiService service;

    private ApiClient() {
    }

    public static SnipApiService getService() {
        if (service == null) {
            synchronized (ApiClient.class) {
                if (service == null) {
                    // Increased timeouts to 3 minutes to handle AI processing and cold starts
                    OkHttpClient okHttpClient = new OkHttpClient.Builder()
                            .connectTimeout(180, TimeUnit.SECONDS)
                            .readTimeout(180, TimeUnit.SECONDS)
                            .writeTimeout(180, TimeUnit.SECONDS)
                            .build();

                    Retrofit retrofit = new Retrofit.Builder()
                            .baseUrl(BASE_URL)
                            .client(okHttpClient)
                            .addConverterFactory(GsonConverterFactory.create())
                            .build();
                    service = retrofit.create(SnipApiService.class);
                }
            }
        }
        return service;
    }
}
