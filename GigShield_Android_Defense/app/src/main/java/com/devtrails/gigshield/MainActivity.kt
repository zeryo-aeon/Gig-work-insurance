package com.devtrails.gigshield

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.graphics.Color
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
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationServices
import java.util.Locale

class MainActivity : AppCompatActivity() {

    // Login View
    private lateinit var layoutLogin: LinearLayout
    private lateinit var etUsername: EditText
    private lateinit var etPassword: EditText
    private lateinit var btnLogin: Button

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
        btnLogin = findViewById(R.id.btnLogin)

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

        fusedLocationClient = LocationServices.getFusedLocationProviderClient(this)

        btnRetryLock.setOnClickListener {
            if (checkFirmwareBlocked()) {
                Toast.makeText(this, "Still Active! Turn off Developer Options first.", Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(this, "Integrity Restored.", Toast.LENGTH_SHORT).show()
                lockOverlay.visibility = View.GONE
            }
        }

        

        btnLogin.setOnClickListener {
            val user = etUsername.text.toString().trim()
            val pass = etPassword.text.toString().trim()

            if (pass != "123") {
                Toast.makeText(this, "Invalid Password", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            if (user == "rahul") {
                currentUserType = "HONEST"
                tvWelcome.text = "Hello, Rahul (Tier 2)"
                showDashboard()
            } else if (user == "hacker") {
                currentUserType = "HACKER"
                tvWelcome.text = "Hello, Syndicate Rep."
                showDashboard()
            } else {
                Toast.makeText(this, "Try 'rahul' or 'hacker'", Toast.LENGTH_LONG).show()
            }
        }

        btnLogout.setOnClickListener {
            layoutDashboard.visibility = View.GONE
            layoutLogin.visibility = View.VISIBLE
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
            layoutGNN.visibility = View.VISIBLE
            btnGnnBack.visibility = View.GONE
            tvGnnLog.text = "Uploading Image EXIF Metadata...\nAnalyzing pixels for flood verification..."

            Handler(Looper.getMainLooper()).postDelayed({
                tvGnnResult.text = "✅ CLAIM APPROVED\n\nMachine Vision confirmed flood scene.\nLocation securely verified via EXIF.\n₹850 Dispatched to Wallet."
                tvGnnResult.setTextColor(Color.parseColor("#10b981"))
                btnGnnBack.visibility = View.VISIBLE
            }, 3000)
        }

        btnGnnBack.setOnClickListener {
            layoutGNN.visibility = View.GONE
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
        layoutLogin.visibility = View.GONE
        layoutDashboard.visibility = View.VISIBLE
        fetchLocation()
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
}
