package com.devtrails.gigshield

import android.location.Location
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.graphics.Color
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.gson.Gson
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import okhttp3.*
import java.io.IOException

class MainViewModel : ViewModel() {
    // Auth State
    var currentUser by mutableStateOf<String?>(null)
    var currentUserType by mutableStateOf("HONEST")
    var isLoggingIn by mutableStateOf(false)
    
    // Server Config
    var serverIp by mutableStateOf("10.0.2.2")
    var serverPort by mutableStateOf("8000")
    var useLocalhost by mutableStateOf(true)
    var isDarkMode by mutableStateOf(true) // Default to dark for premium feel
    
    // Server Connection Status
    var connectionStatus by mutableStateOf("Offline")
    var isServerReachable by mutableStateOf(false)
    
    // Location State
    var isGpsFetched by mutableStateOf(false)
    var cachedLocation by mutableStateOf<Location?>(null)
    var activeZone by mutableStateOf("Detecting GPS Hardware...")
    
    // KPI Data (Mock/Live)
    var earnings by mutableStateOf("₹4,200")
    var insurancePayout by mutableStateOf("₹340")
    var riskScore by mutableStateOf("68/100")
    var prediction by mutableStateOf("₹550")
    
    // Tab Data
    var insurancePlans by mutableStateOf<List<Map<String, Any>>>(emptyList())
    var insuranceTriggers by mutableStateOf<List<Map<String, Any>>>(emptyList())
    var claimsHistory by mutableStateOf<List<Map<String, Any>>>(emptyList())
    var riskFactors by mutableStateOf<List<Map<String, Any>>>(emptyList())
    var overallRiskLevel by mutableStateOf("")

    // GNN/Security State
    var gnnLog by mutableStateOf("")
    var gnnResult by mutableStateOf("")
    var isGnnScanning by mutableStateOf(false)
    var isGnnScanComplete by mutableStateOf(false)
    var isFirmwareBlocked by mutableStateOf(false)
    var gnnStatusColor by mutableStateOf(Color.White)

    fun startGnnScan(onComplete: (Boolean) -> Unit) {
        isGnnScanning = true
        isGnnScanComplete = false
        gnnLog = "Initializing Firmware integrity scan...\nChecking Developer Modes..."
        
        // Use onComplete logic if needed (placeholder)
        onComplete(true)
    }

    fun setGnnResult(log: String, result: String, color: Color, complete: Boolean = true) {
        gnnLog = log
        gnnResult = result
        gnnStatusColor = color
        isGnnScanComplete = complete
        isGnnScanning = false
    }

    fun resetGnn() {
        gnnLog = ""
        gnnResult = ""
        isGnnScanning = false
        isGnnScanComplete = false
    }

    private val gson = Gson()
    private val cookieJar = object : CookieJar {
        private val cookieStore = HashMap<String, List<Cookie>>()
        override fun saveFromResponse(url: HttpUrl, cookies: List<Cookie>) {
            cookieStore[url.host] = cookies
        }
        override fun loadForRequest(url: HttpUrl): List<Cookie> {
            return cookieStore[url.host] ?: ArrayList()
        }
    }
    private val client = OkHttpClient.Builder()
        .cookieJar(cookieJar)
        .build()

    fun checkServerStatus() {
        val url = "http://$serverIp:$serverPort/api/status"
        val request = Request.Builder().url(url).build()
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                viewModelScope.launch(Dispatchers.Main) {
                    isServerReachable = false
                    connectionStatus = "Offline"
                }
            }

            override fun onResponse(call: Call, response: Response) {
                val body = response.body?.string()
                viewModelScope.launch(Dispatchers.Main) {
                    if (response.isSuccessful && body != null) {
                        try {
                            val map = gson.fromJson(body, Map::class.java)
                            if (map["status"] == "online") {
                                isServerReachable = true
                                connectionStatus = "Verified: ${map["server"]}"
                            } else {
                                isServerReachable = false
                                connectionStatus = if (serverIp == "10.0.2.2") "Bridge Error" else "Mismatch"
                            }
                        } catch (e: Exception) {
                            isServerReachable = false
                            connectionStatus = "Invalid Node"
                        }
                    } else {
                        isServerReachable = false
                        connectionStatus = "Offline"
                    }
                }
            }
        })
    }

    fun performLogin(riderId: String, pass: String, onSuccess: () -> Unit, onError: (String) -> Unit) {
        if (serverIp.isEmpty()) {
            onError("Please enter Server IP")
            return
        }

        val url = "http://$serverIp:$serverPort/auth/login"
        val formBody = FormBody.Builder()
            .add("rider_id", riderId)
            .add("password", pass)
            .build()

        val request = Request.Builder().url(url).post(formBody).build()
        isLoggingIn = true

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                viewModelScope.launch(Dispatchers.Main) {
                    isLoggingIn = false
                    onError("Connection Failed: ${e.message}")
                }
            }

            override fun onResponse(call: Call, response: Response) {
                val body = response.body?.string()
                viewModelScope.launch(Dispatchers.Main) {
                    isLoggingIn = false
                    if (response.isSuccessful && body != null) {
                        try {
                            val map = gson.fromJson(body, Map::class.java)
                            if (map["success"] == true) {
                                currentUser = riderId
                                currentUserType = if (riderId == "hacker") "HACKER" else "HONEST"
                                onSuccess()
                            } else {
                                onError("Auth Failed: ${map["detail"]}")
                            }
                        } catch (e: Exception) {
                            onError("JSON Parsing Error")
                        }
                    } else {
                        onError("Server Error: ${response.code}")
                    }
                }
            }
        })
    }

    fun fetchInsurancePlans() {
        val url = "http://$serverIp:$serverPort/api/insurance/plans"
        val request = Request.Builder().url(url).build()
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {}
            override fun onResponse(call: Call, response: Response) {
                val body = response.body?.string() ?: return
                viewModelScope.launch(Dispatchers.Main) {
                    try {
                        val json = gson.fromJson(body, Map::class.java)
                        @Suppress("UNCHECKED_CAST")
                        insurancePlans = json["plans"] as? List<Map<String, Any>> ?: emptyList()
                    } catch (e: Exception) {}
                }
            }
        })
    }

    fun fetchTriggers() {
        val url = "http://$serverIp:$serverPort/api/triggers/live"
        val request = Request.Builder().url(url).build()
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {}
            override fun onResponse(call: Call, response: Response) {
                val body = response.body?.string() ?: return
                viewModelScope.launch(Dispatchers.Main) {
                    try {
                        val json = gson.fromJson(body, Map::class.java)
                        @Suppress("UNCHECKED_CAST")
                        insuranceTriggers = json["triggers"] as? List<Map<String, Any>> ?: emptyList()
                    } catch (e: Exception) {}
                }
            }
        })
    }

    fun fetchClaims() {
        val url = "http://$serverIp:$serverPort/api/claims/history"
        val request = Request.Builder().url(url).build()
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {}
            override fun onResponse(call: Call, response: Response) {
                val body = response.body?.string() ?: return
                viewModelScope.launch(Dispatchers.Main) {
                    try {
                        val json = gson.fromJson(body, Map::class.java)
                        @Suppress("UNCHECKED_CAST")
                        claimsHistory = json["claims"] as? List<Map<String, Any>> ?: emptyList()
                    } catch (e: Exception) {}
                }
            }
        })
    }

    fun fetchRiskFactors() {
        val url = "http://$serverIp:$serverPort/api/dashboard/risk-factors"
        val request = Request.Builder().url(url).build()
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {}
            override fun onResponse(call: Call, response: Response) {
                val body = response.body?.string() ?: return
                viewModelScope.launch(Dispatchers.Main) {
                    try {
                        val json = gson.fromJson(body, Map::class.java)
                        riskScore = (json["overall_score"] as? Double)?.toInt()?.toString() ?: "0"
                        overallRiskLevel = json["level"]?.toString() ?: "Unknown"
                        @Suppress("UNCHECKED_CAST")
                        riskFactors = json["factors"] as? List<Map<String, Any>> ?: emptyList()
                    } catch (e: Exception) {}
                }
            }
        })
    }

    // Admin State
    var adminMetrics by mutableStateOf("MAE: 10.2 | R²: 0.96")
    var adminBarHeights by mutableStateOf(listOf(140f, 180f, 130f, 210f, 150f, 190f, 160f, 230f, 170f, 200f))

    fun updateAdminProfile(user: String) {
        val rajuBars = listOf(140f, 180f, 130f, 210f, 150f, 190f, 160f, 230f, 170f, 200f)
        val priyaBars = listOf(200f, 150f, 220f, 130f, 250f, 110f, 240f, 160f, 210f, 190f)
        val vikramBars = listOf(100f, 120f, 110f, 130f, 105f, 125f, 115f, 140f, 120f, 130f)

        when (user) {
            "RAJU" -> {
                adminBarHeights = rajuBars
                adminMetrics = "MAE: 10.2 | R²: 0.96"
            }
            "PRIYA" -> {
                adminBarHeights = priyaBars
                adminMetrics = "MAE: 14.8 | R²: 0.91"
            }
            "VIKRAM" -> {
                adminBarHeights = vikramBars
                adminMetrics = "MAE: 22.1 | R²: 0.82"
            }
        }
    }

    fun logout() {
        currentUser = null
        isGpsFetched = false
    }

    // Helper for adding styled cards in Compose will be done in the screens
}
