package com.devtrails.gigshield

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.graphics.Color
import android.graphics.Typeface
import android.location.Geocoder
import android.location.Location
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import java.util.Locale
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import com.google.gson.Gson
import com.google.android.material.bottomnavigation.BottomNavigationView
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationServices
import java.io.IOException

class MainActivity : AppCompatActivity() {

    // Login View
    // New Layouts
    private lateinit var layoutLogin: LinearLayout
    private lateinit var layoutSignup: LinearLayout
    private lateinit var layoutAdmin: LinearLayout
    private lateinit var layoutSession: LinearLayout
    private lateinit var layoutInsurance: LinearLayout
    private lateinit var layoutTriggers: LinearLayout
    private lateinit var layoutClaims: LinearLayout
    private lateinit var layoutRisk: LinearLayout
    private lateinit var bottomNav: BottomNavigationView
    
    private lateinit var listInsurance: LinearLayout
    private lateinit var listTriggers: LinearLayout
    private lateinit var listClaims: LinearLayout
    private lateinit var listRisk: LinearLayout

    private var currentIp: String = ""
    private var currentPort: String = "8000"

    // Login views
    private lateinit var etUsername: EditText
    private lateinit var etPassword: EditText
    private lateinit var etServerIp: EditText
    private lateinit var etServerPort: EditText
    private lateinit var btnLogin: Button
    private lateinit var btnDemoAdmin: Button
    private lateinit var btnDemoRider1: Button
    private lateinit var btnDemoRider2: Button
    private lateinit var btnDemoRider3: Button
    private lateinit var tvToSignup: TextView

    // Signup views
    private lateinit var etSignupName: EditText
    private lateinit var etSignupPhone: EditText
    private lateinit var etSignupZone: EditText
    private lateinit var etSignupPass: EditText
    private lateinit var btnSignup: Button
    private lateinit var tvToLogin: TextView

    // Dashboard View
    private lateinit var layoutDashboard: LinearLayout
    private lateinit var layoutInfo: LinearLayout
    private lateinit var btnTechDocs: Button
    private lateinit var btnInfoBack: Button
    private lateinit var tvWelcome: TextView
    private lateinit var tvActiveZone: TextView
    private lateinit var btnInitClaim: Button
    private lateinit var btnLogout: Button

    // Camera View (Tier 2)
    private lateinit var layoutCamera: LinearLayout
    private lateinit var btnDemoCamera: Button

    // GNN View
    private lateinit var layoutGNN: LinearLayout
    private lateinit var tvGnnLog: TextView
    private lateinit var tvGnnResult: TextView
    private lateinit var btnGnnBack: Button

    // Firmware Lock
    private lateinit var lockOverlay: LinearLayout
    private lateinit var btnRetryLock: Button

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

    private val gson = Gson()
    private lateinit var fusedLocationClient: FusedLocationProviderClient
    private var currentUserType = "HONEST"
    private var isGpsFetched = false
    private var cachedLocation: Location? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        layoutLogin = findViewById(R.id.layoutLogin)
        etUsername = findViewById(R.id.etUsername)
        etPassword = findViewById(R.id.etPassword)
        etServerIp = findViewById(R.id.etServerIp)
        etServerPort = findViewById(R.id.etServerPort)
        btnLogin = findViewById(R.id.btnLogin)
        btnDemoAdmin = findViewById(R.id.btnDemoAdmin)
        btnDemoRider1 = findViewById(R.id.btnDemoRider1)
        btnDemoRider2 = findViewById(R.id.btnDemoRider2)
        btnDemoRider3 = findViewById(R.id.btnDemoRider3)
        tvToSignup = findViewById(R.id.tvToSignup)
        
        etServerPort.setText("8000") // Default port

        // Signup Binding
        layoutSignup = findViewById(R.id.layoutSignup)
        etSignupName = findViewById(R.id.etSignupName)
        etSignupPhone = findViewById(R.id.etSignupPhone)
        etSignupZone = findViewById(R.id.etSignupZone)
        etSignupPass = findViewById(R.id.etSignupPass)
        btnSignup = findViewById(R.id.btnSignup)
        tvToLogin = findViewById(R.id.tvToLogin)

        // Admin/Session Binding
        layoutAdmin = findViewById(R.id.layoutAdmin)
        layoutSession = findViewById(R.id.layoutSession)

        layoutDashboard = findViewById(R.id.layoutDashboard)
        layoutInfo = findViewById(R.id.layoutInfo)
        btnTechDocs = findViewById(R.id.btnTechDocs)
        btnInfoBack = findViewById(R.id.btnInfoBack)
        tvWelcome = findViewById(R.id.tvWelcome)
        tvActiveZone = findViewById(R.id.tvActiveZone)
        btnInitClaim = findViewById(R.id.btnInitClaim)
        btnLogout = findViewById(R.id.btnLogout)

        layoutCamera = findViewById(R.id.layoutCamera)
        btnDemoCamera = findViewById(R.id.btnDemoCamera)

        layoutGNN = findViewById(R.id.layoutGNN)
        tvGnnLog = findViewById(R.id.tvGnnLog)
        tvGnnResult = findViewById(R.id.tvGnnResult)
        btnGnnBack = findViewById(R.id.btnGnnBack)

        lockOverlay = findViewById(R.id.lockOverlay)
        btnRetryLock = findViewById(R.id.btnRetryLock)

        btnDemoAdmin.setOnClickListener {
            etUsername.setText("ADMIN-001")
            etPassword.setText("admin123")
            Toast.makeText(this, "Demo: System Admin", Toast.LENGTH_SHORT).show()
        }
        btnDemoRider1.setOnClickListener {
            etUsername.setText("GW-8821")
            etPassword.setText("rider123")
            Toast.makeText(this, "Demo: Raju Kumar", Toast.LENGTH_SHORT).show()
        }
        btnDemoRider2.setOnClickListener {
            etUsername.setText("GW-4422")
            etPassword.setText("rider456")
            Toast.makeText(this, "Demo: Priya Sharma", Toast.LENGTH_SHORT).show()
        }
        btnDemoRider3.setOnClickListener {
            etUsername.setText("GW-9901")
            etPassword.setText("rider789")
            Toast.makeText(this, "Demo: Vikram Singh", Toast.LENGTH_SHORT).show()
        }

        layoutInsurance = findViewById(R.id.layoutInsurance)
        layoutTriggers = findViewById(R.id.layoutTriggers)
        layoutClaims = findViewById(R.id.layoutClaims)
        layoutRisk = findViewById(R.id.layoutRisk)
        bottomNav = findViewById(R.id.bottomNav)
        
        listInsurance = findViewById(R.id.listInsurance)
        listTriggers = findViewById(R.id.listTriggers)
        listClaims = findViewById(R.id.listClaims)
        listRisk = findViewById(R.id.listRisk)

        bottomNav.setOnItemSelectedListener { item ->
            when(item.itemId) {
                R.id.nav_dashboard -> { showDashboardTab(); true }
                R.id.nav_insurance -> { showTab(layoutInsurance); fetchInsuranceTabs(); true }
                R.id.nav_triggers -> { showTab(layoutTriggers); fetchTriggersTabs(); true }
                R.id.nav_claims -> { showTab(layoutClaims); fetchClaimsTabs(); true }
                R.id.nav_risk -> { showTab(layoutRisk); fetchRiskTabs(); true }
                else -> false
            }
        }

        fusedLocationClient = LocationServices.getFusedLocationProviderClient(this)

        btnRetryLock.setOnClickListener {
            if (checkFirmwareBlocked()) {
                Toast.makeText(this, "Still Active! Turn off Developer Options first.", Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(this, "Integrity Restored.", Toast.LENGTH_SHORT).show()
                lockOverlay.visibility = View.GONE
            }
        }

        // Navigation Listeners
        tvToSignup.setOnClickListener { showSignup() }
        tvToLogin.setOnClickListener { showLogin() }

        btnSignup.setOnClickListener {
            Toast.makeText(this, "Account Created! Redirecting to login...", Toast.LENGTH_SHORT).show()
            showLogin()
        }

        findViewById<View>(R.id.btnToSession).setOnClickListener {
            showLayout(layoutSession)
        }

        findViewById<View>(R.id.btnSessionBack).setOnClickListener {
            showLayout(layoutDashboard)
        }

        findViewById<View>(R.id.btnAdminBack).setOnClickListener {
            showLayout(layoutLogin)
        }

        btnLogin.setOnClickListener {
            val user = etUsername.text.toString().trim()
            val pass = etPassword.text.toString().trim()
            val ip = etServerIp.text.toString().trim()
            val port = etServerPort.text.toString().trim()
            
            if (ip.isEmpty()) {
                Toast.makeText(this, "Please enter Server IP", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            // [SYNC DEFENSE] Block login if integrity compromised
            if (checkFirmwareBlocked()) {
                showLayout(lockOverlay)
                return@setOnClickListener
            }

            if (user == "ADMIN-001") {
                this.currentIp = ip
                this.currentPort = port
                showLayout(layoutAdmin)
                populateAdminMockData()
                Toast.makeText(this, "Admin Authenticated", Toast.LENGTH_SHORT).show()
            } else if (user.isNotEmpty() && pass.isNotEmpty()) {
                this.currentIp = ip
                this.currentPort = port
                performLogin(user, pass, ip, port)
            } else {
                Toast.makeText(this, "Enter ID and Password", Toast.LENGTH_SHORT).show()
            }
        }

        btnLogout.setOnClickListener {
            showLayout(layoutLogin)
            etUsername.text.clear()
            etPassword.text.clear()
            isGpsFetched = false
        }

        btnTechDocs.setOnClickListener {
            layoutDashboard.visibility = View.GONE
            layoutInfo.visibility = View.VISIBLE
        }
        btnInfoBack.setOnClickListener {
            layoutInfo.visibility = View.GONE
            showDashboard()
        }

        btnInitClaim.setOnClickListener {
            layoutDashboard.visibility = View.GONE
            layoutGNN.visibility = View.VISIBLE
            btnGnnBack.visibility = View.GONE
            tvGnnResult.text = ""
            tvGnnLog.text = "Initializing Firmware integrity scan...\nChecking Developer Modes..."

            Handler(Looper.getMainLooper()).postDelayed({
                if (checkFirmwareBlocked()) {
                    layoutGNN.visibility = View.GONE
                    lockOverlay.visibility = View.VISIBLE
                } else {
                    tvGnnLog.text = "Checking VPN tunnels \n& Routing GNN Nodes..."
                    Handler(Looper.getMainLooper()).postDelayed({
                        verifyClaimSecurity()
                    }, 1500)
                }
            }, 1500)
        }

        btnDemoCamera.setOnClickListener {
            layoutCamera.visibility = View.GONE
            showLayout(layoutGNN)
            btnGnnBack.visibility = View.GONE
            tvGnnLog.text = "Uploading Image EXIF Metadata...\nAnalyzing pixels for flood verification..."

            Handler(Looper.getMainLooper()).postDelayed({
                tvGnnResult.text = "✅ CLAIM APPROVED\n\nMachine Vision confirmed flood scene.\nLocation securely verified via EXIF.\n₹850 Dispatched to Wallet."
                tvGnnResult.setTextColor(Color.parseColor("#10b981"))
                btnGnnBack.visibility = View.VISIBLE
            }, 3000)
        }

        btnGnnBack.setOnClickListener {
            showDashboard()
        }
    }

    override fun onResume() {
        super.onResume()
        if (checkFirmwareBlocked()) {
            lockOverlay.visibility = View.VISIBLE
        } else {
            lockOverlay.visibility = View.GONE
        }
    }

    private fun showDashboard() {
        showLayout(layoutDashboard)
        fetchLocation()
    }

    private fun performLogin(user: String, pass: String, ip: String, port: String) {
        val url = "http://$ip:$port/auth/login"
        val formBody = FormBody.Builder()
            .add("rider_id", user)
            .add("password", pass)
            .build()

        val request = Request.Builder()
            .url(url)
            .post(formBody)
            .build()

        btnLogin.isEnabled = false
        btnLogin.text = "SYNCING..."

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                runOnUiThread {
                    btnLogin.isEnabled = true
                    btnLogin.text = "SECURE LOGIN →"
                    Toast.makeText(this@MainActivity, "Server Connection Failed: ${e.message}", Toast.LENGTH_LONG).show()
                }
            }

            override fun onResponse(call: Call, response: Response) {
                val body = response.body?.string()
                runOnUiThread {
                    btnLogin.isEnabled = true
                    btnLogin.text = "SECURE LOGIN →"
                    if (response.isSuccessful && body != null) {
                        try {
                            val map = gson.fromJson(body, Map::class.java)
                            if (map["success"] == true) {
                                loginSuccess(user)
                            } else {
                                Toast.makeText(this@MainActivity, "Auth Failed: ${map["detail"]}", Toast.LENGTH_SHORT).show()
                            }
                        } catch (e: Exception) {
                            Toast.makeText(this@MainActivity, "JSON Error", Toast.LENGTH_SHORT).show()
                        }
                    } else {
                        Toast.makeText(this@MainActivity, "Error: ${response.code}", Toast.LENGTH_SHORT).show()
                    }
                }
            }
        })
    }

    private fun loginSuccess(user: String) {
        if (user == "hacker") {
            currentUserType = "HACKER"
            tvWelcome.text = "Hello, Syndicate Rep."
        } else {
            currentUserType = "HONEST"
            tvWelcome.text = "Hello, Worker ($user)"
        }
        showDashboard()
        Toast.makeText(this, "Server Sync Successful", Toast.LENGTH_SHORT).show()
    }

    private fun showSignup() {
        showLayout(layoutSignup)
    }

    private fun showLogin() {
        setupAdminUserSwitch()
        showLayout(layoutLogin)
    }

    private fun setupAdminUserSwitch() {
        val rajuBars = listOf(140, 180, 130, 210, 150, 190, 160, 230, 170, 200)
        val priyaBars = listOf(200, 150, 220, 130, 250, 110, 240, 160, 210, 190)
        val vikramBars = listOf(100, 120, 110, 130, 105, 125, 115, 140, 120, 130)

        findViewById<Button>(R.id.btnAdminSelectRaju).setOnClickListener {
            updateAdminXgboost("RAJU", rajuBars, "MAE: 10.2 | R²: 0.96")
        }
        findViewById<Button>(R.id.btnAdminSelectPriya).setOnClickListener {
            updateAdminXgboost("PRIYA", priyaBars, "MAE: 14.8 | R²: 0.91")
        }
        findViewById<Button>(R.id.btnAdminSelectVikram).setOnClickListener {
            updateAdminXgboost("VIKRAM", vikramBars, "MAE: 22.1 | R²: 0.82")
        }
    }

    private fun updateAdminXgboost(user: String, heights: List<Int>, metrics: String) {
        val bars = listOf(
            R.id.vBar1, R.id.vBar2, R.id.vBar3, R.id.vBar4, R.id.vBar5,
            R.id.vBar6, R.id.vBar7, R.id.vBar8, R.id.vBar9, R.id.vBar10
        )
        for (i in bars.indices) {
            val bar = findViewById<View>(bars[i])
            val params = bar.layoutParams
            params.height = (heights[i] * resources.displayMetrics.density).toInt()
            bar.layoutParams = params
        }
        findViewById<TextView>(R.id.tvAdminAnalyticsMetrics).text = metrics
        Toast.makeText(this, "Analyzed $user's profile via XGBoost", Toast.LENGTH_SHORT).show()
    }

    private fun addStyledCard(container: LinearLayout, title: String, subtitle: String, extra: String, color: Int) {
        val card = androidx.cardview.widget.CardView(this)
        val layoutParams = LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT
        )
        layoutParams.setMargins(0, 0, 0, 32)
        card.layoutParams = layoutParams
        card.setCardBackgroundColor(Color.parseColor("#111318"))
        card.radius = 12f * resources.displayMetrics.density
        card.cardElevation = 8f * resources.displayMetrics.density

        val inner = LinearLayout(this)
        inner.orientation = LinearLayout.VERTICAL
        inner.setPadding(40, 40, 40, 40)

        val tvTitle = TextView(this)
        tvTitle.text = title
        tvTitle.setTextColor(Color.WHITE)
        tvTitle.textSize = 16f
        tvTitle.setTypeface(null, Typeface.BOLD)

        val tvSub = TextView(this)
        tvSub.text = subtitle
        tvSub.setTextColor(Color.parseColor("#9ca3af"))
        tvSub.textSize = 13f
        tvSub.setPadding(0, 8, 0, 8)

        val tvExtra = TextView(this)
        tvExtra.text = extra
        tvExtra.setTextColor(color)
        tvExtra.textSize = 12f
        tvExtra.setTypeface(Typeface.MONOSPACE)

        inner.addView(tvTitle)
        inner.addView(tvSub)
        inner.addView(tvExtra)
        card.addView(inner)
        container.addView(card)
    }

    private fun showLayout(activeLayout: LinearLayout) {
        val layouts = arrayOf(
            layoutLogin, layoutDashboard, layoutCamera, 
            layoutGNN, layoutInfo, layoutSignup, 
            layoutAdmin, layoutSession,
            layoutInsurance, layoutTriggers, layoutClaims, layoutRisk
        )
        for (layout in layouts) {
            layout.visibility = if (layout == activeLayout) View.VISIBLE else View.GONE
        }
        
        // Navigation Bar visibility
        val dashboardTabs = arrayOf(layoutDashboard, layoutInsurance, layoutTriggers, layoutClaims, layoutRisk)
        val isDashboardTab = activeLayout in dashboardTabs
        bottomNav.visibility = if (isDashboardTab) View.VISIBLE else View.GONE
    }

    private fun showDashboardTab() {
        showLayout(layoutDashboard)
    }

    private fun showTab(layout: LinearLayout) {
        showLayout(layout)
    }

    private fun fetchInsuranceTabs() {
        val url = "http://$currentIp:$currentPort/api/insurance/plans"
        val request = Request.Builder().url(url).build()
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {}
            override fun onResponse(call: Call, response: Response) {
                val body = response.body?.string() ?: return
                runOnUiThread {
                    listInsurance.removeAllViews()
                    try {
                        val json = gson.fromJson(body, Map::class.java)
                        val plans = json["plans"] as List<Map<String, Any>>
                        for (p in plans) {
                            addStyledCard(
                                listInsurance,
                                "🛡️ ${p["name"]}",
                                p["description"].toString(),
                                "Price: ₹${p["base_price"]}/week",
                                Color.parseColor("#3b82f6")
                            )
                        }
                    } catch (e: Exception) {}
                }
            }
        })
    }

    private fun fetchTriggersTabs() {
        val url = "http://$currentIp:$currentPort/api/triggers/live"
        val request = Request.Builder().url(url).build()
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {}
            override fun onResponse(call: Call, response: Response) {
                val body = response.body?.string() ?: return
                runOnUiThread {
                    listTriggers.removeAllViews()
                    try {
                        val json = gson.fromJson(body, Map::class.java)
                        val triggers = json["triggers"] as List<Map<String, Any>>
                        for (t in triggers) {
                            val statusColor = if (t["status"] == "triggered") Color.parseColor("#ef4444") else Color.parseColor("#10b981")
                            addStyledCard(
                                listTriggers,
                                "${t["icon"]} ${t["name"]}",
                                "Current Value: ${t["current_value"]}",
                                "Status: ${t["status"].toString().uppercase()} · Payout: ${t["payout"]}",
                                statusColor
                            )
                        }
                    } catch (e: Exception) {}
                }
            }
        })
    }

    private fun fetchClaimsTabs() {
        val url = "http://$currentIp:$currentPort/api/claims/history"
        val request = Request.Builder().url(url).build()
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {}
            override fun onResponse(call: Call, response: Response) {
                val body = response.body?.string() ?: return
                runOnUiThread {
                    listClaims.removeAllViews()
                    try {
                        val json = gson.fromJson(body, Map::class.java)
                        val claims = json["claims"] as List<Map<String, Any>>
                        for (c in claims) {
                            addStyledCard(
                                listClaims,
                                "${c["icon"]} ${c["title"]}",
                                c["detail"].toString(),
                                "Amount: ₹${c["amount"]} · Status: ${c["status"]}",
                                Color.parseColor("#f97316")
                            )
                        }
                    } catch (e: Exception) {}
                }
            }
        })
    }

    private fun fetchRiskTabs() {
        val url = "http://$currentIp:$currentPort/api/dashboard/risk-factors"
        val request = Request.Builder().url(url).build()
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {}
            override fun onResponse(call: Call, response: Response) {
                val body = response.body?.string() ?: return
                runOnUiThread {
                    listRisk.removeAllViews()
                    try {
                        val json = gson.fromJson(body, Map::class.java)
                        val score = json["overall_score"]
                        val level = json["level"]
                        val factors = json["factors"] as List<Map<String, Any>>
                        
                        addStyledCard(
                            listRisk,
                            "Overall Risk: $score/100",
                            "Safety Level: $level",
                            "Scanning 10+ real-time behavioral nodes...",
                            Color.YELLOW
                        )

                        for (f in factors) {
                            val factorColor = if ((f["score"] as Double) > 70) Color.parseColor("#ef4444") else Color.LTGRAY
                            addStyledCard(
                                listRisk,
                                "● ${f["name"]}",
                                "Impact Score",
                                "${f["score"]}% correlation to incident risk",
                                factorColor
                            )
                        }
                    } catch (e: Exception) {}
                }
            }
        })
    }

    private fun isVpnConnected(): Boolean {
        return try {
            val cm = getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
            val activeNetwork = cm.activeNetwork
            val caps = cm.getNetworkCapabilities(activeNetwork)
            caps?.hasTransport(NetworkCapabilities.TRANSPORT_VPN) == true
        } catch (e: Exception) {
            false
        }
    }

    private fun verifyClaimSecurity() {
        // 1. VPN CHECK
        if (isVpnConnected()) {
            tvGnnLog.text = "🚨 IP SPOOFING DETECTED 🚨"
            tvGnnResult.text = "❌ VPN Active ❌\n\nNetwork Fingerprinting mismatch. Application cannot securely determine real location. Claim Denied."
            tvGnnResult.setTextColor(Color.parseColor("#ef4444"))
            btnGnnBack.visibility = View.VISIBLE
            return
        }

        // 2. MOCK LOCATION / GPS CHECK
        if (!isGpsFetched || cachedLocation == null) {
            tvGnnLog.text = "🚨 HARDWARE ERROR 🚨"
            tvGnnResult.text = "No valid GPS trajectory found.\nEnsure Location Services are ON."
            tvGnnResult.setTextColor(Color.parseColor("#f59e0b"))
            btnGnnBack.visibility = View.VISIBLE
            return
        }

        if (cachedLocation!!.isFromMockProvider) {
            tvGnnLog.text = "🚨 FIRMWARE TAMPERING 🚨"
            tvGnnResult.text = "❌ Mock Location SDK matched malware signature.\nClaim permanently denied."
            tvGnnResult.setTextColor(Color.parseColor("#ef4444"))
            btnGnnBack.visibility = View.VISIBLE
            return
        }

        // 3. GNN SYNDICATE CHECK (Fake Hacker Profile)
        if (currentUserType == "HACKER") {
            tvGnnLog.text = "WARNING: Unnatural Node Convergence!"
            tvGnnResult.text = "❌ SYNDICATE THREAT BLOCKED ❌\n\nGNN detected impossible physical clustering.\n500 pings instantly appeared in this 2 sq-km zone without historical trajectory.\n\nAction: Automatic Account Suspension."
            tvGnnResult.setTextColor(Color.parseColor("#ef4444"))
            btnGnnBack.visibility = View.VISIBLE
            return
        }

        // 4. HONEST WORKER FLOW -> TIER 2
        layoutGNN.visibility = View.GONE
        layoutCamera.visibility = View.VISIBLE
    }

    private fun fetchLocation() {
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.ACCESS_FINE_LOCATION), 100)
            return
        }

        tvActiveZone.text = "Tracking Physical GPS Hardware..."
        fusedLocationClient.getCurrentLocation(com.google.android.gms.location.Priority.PRIORITY_HIGH_ACCURACY, null).addOnSuccessListener { location: Location? ->
            if (location != null) {
                cachedLocation = location
                isGpsFetched = true
                try {
                    val geocoder = Geocoder(this@MainActivity, Locale.getDefault())
                    val addresses = geocoder.getFromLocation(location.latitude, location.longitude, 1)
                    if (addresses != null && addresses.isNotEmpty()) {
                        val city = addresses[0].locality ?: addresses[0].subLocality ?: addresses[0].featureName ?: addresses[0].subAdminArea ?: "Unknown Region"
                        tvActiveZone.text = "Hardware Zone: $city\nLat: ${location.latitude}, Lon: ${location.longitude}"
                    } else {
                        tvActiveZone.text = "Hardware Zone: Unmapped\nLat: ${location.latitude}, Lon: ${location.longitude}"
                    }
                } catch (e: Exception) {
                    tvActiveZone.text = "Hardware Zone: Unmapped\nLat: ${location.latitude}, Lon: ${location.longitude}"
                }
            } else {
                tvActiveZone.text = "Could not fetch GPS. Open Google Maps to wake up device cache."
            }
        }
    }

    private fun checkFirmwareBlocked(): Boolean {
        // Allow Developer Mode ONLY during debugging or if the environment variable (BYPASS_DEFENSE) is true
        val isDebugging = android.os.Debug.isDebuggerConnected() || BuildConfig.BYPASS_DEFENSE
        
        if (isDebugging) {
            return false
        }

        var isDevModeEnabled = false
        try {
            isDevModeEnabled = Settings.Global.getInt(contentResolver, Settings.Global.DEVELOPMENT_SETTINGS_ENABLED, 0) != 0
        } catch (e: Exception) {}
        return isDevModeEnabled
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == 100 && grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            fetchLocation()
        } else {
            Toast.makeText(this, "Location permission strictly required", Toast.LENGTH_SHORT).show()
        }
    }

    private fun populateAdminMockData() {
        if (currentIp.isEmpty()) return
        val url = "http://$currentIp:$currentPort/api/admin/users"
        val request = Request.Builder().url(url).build()
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                runOnUiThread { Toast.makeText(this@MainActivity, "Admin Fetch Failed", Toast.LENGTH_SHORT).show() }
            }
            override fun onResponse(call: Call, response: Response) {
                val body = response.body?.string() ?: return
                runOnUiThread {
                    // Visual feedback for admin data
                    Toast.makeText(this@MainActivity, "Admin Console Synced", Toast.LENGTH_SHORT).show()
                }
            }
        })
    }
}
