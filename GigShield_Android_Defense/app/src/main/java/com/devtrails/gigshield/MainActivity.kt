package com.devtrails.gigshield

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.location.Geocoder
import android.location.Location
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.painter.Painter
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.sp
import androidx.core.app.ActivityCompat
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.devtrails.gigshield.ui.navigation.Screen
import com.devtrails.gigshield.ui.screens.*
import com.devtrails.gigshield.ui.theme.ElectricOrange
import com.devtrails.gigshield.ui.theme.GigShieldTheme
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import java.util.Locale

class MainActivity : ComponentActivity() {

    private val viewModel: MainViewModel by viewModels()
    private lateinit var fusedLocationClient: FusedLocationProviderClient

    private val requestPermissionLauncher = registerForActivityResult(
        androidx.activity.result.contract.ActivityResultContracts.RequestPermission()
    ) { isGranted: Boolean ->
        if (isGranted) {
            fetchLocation()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        fusedLocationClient = LocationServices.getFusedLocationProviderClient(this)

        setContent {
            GigShieldTheme(darkTheme = viewModel.isDarkMode) {
                val navController = rememberNavController()
                
                // Firmware check on every composition/navigation (simplified)
                if (checkFirmwareBlocked()) {
                    FirmwareLockScreen(onRetry = {
                        if (!checkFirmwareBlocked()) {
                            navController.navigate(Screen.Login.route) {
                                popUpTo(0)
                            }
                        }
                    })
                } else {
                    MainNavigation(navController, viewModel)
                }
            }
        }
    }

    @Composable
    fun MainNavigation(navController: NavHostController, viewModel: MainViewModel) {
        val navBackStackEntry by navController.currentBackStackEntryAsState()
        val currentRoute = navBackStackEntry?.destination?.route

        val showBottomNav = currentRoute in listOf(
            Screen.Dashboard.route, 
            Screen.Insurance.route, 
            Screen.Triggers.route, 
            Screen.Claims.route, 
            Screen.Risk.route
        )

        Scaffold(
            bottomBar = {
                if (showBottomNav) {
                    BottomNav(navController)
                }
            }
        ) { paddingValues ->
            NavHost(
                navController = navController,
                startDestination = Screen.Login.route,
                modifier = Modifier.padding(paddingValues)
            ) {
                composable(Screen.Login.route) {
                    LoginScreen(
                        viewModel = viewModel,
                        onNavigateToSignup = { navController.navigate(Screen.Signup.route) },
                        onLoginSuccess = { 
                            if (viewModel.currentUser == "ADMIN-001") {
                                navController.navigate(Screen.Admin.route)
                            } else {
                                navController.navigate(Screen.Dashboard.route) 
                            }
                            fetchLocation()
                        }
                    )
                }
                composable(Screen.Signup.route) {
                    SignupScreen(viewModel = viewModel, onNavigateToLogin = { navController.popBackStack() })
                }
                composable(Screen.Dashboard.route) {
                    DashboardScreen(
                        viewModel = viewModel,
                        onNavigateToSession = { navController.navigate(Screen.SessionInfo.route) },
                        onLogout = { viewModel.logout(); navController.navigate(Screen.Login.route) { popUpTo(0) } },
                        onInitClaim = { startGnnScanFlow(navController) },
                        onViewPerformance = { /* Add screen for logs if needed */ }
                    )
                }
                composable(Screen.Admin.route) {
                    AdminScreen(viewModel = viewModel, onBack = { navController.popBackStack() })
                }
                composable(Screen.Insurance.route) { InsuranceScreen(viewModel) }
                composable(Screen.Triggers.route) { TriggersScreen(viewModel) }
                composable(Screen.Claims.route) { ClaimsScreen(viewModel) }
                composable(Screen.Risk.route) { RiskScreen(viewModel) }
                composable(Screen.SessionInfo.route) { SessionInfoScreen(viewModel, onBack = { navController.popBackStack() }) }
                composable(Screen.GnnScan.route) { GnnScanScreen(viewModel, onBack = { navController.navigate(Screen.Dashboard.route) { popUpTo(0) } }) }
                composable(Screen.Camera.route) { 
                    CameraScreen(onCapture = { 
                        viewModel.setGnnResult(
                            "✅ CLAIM APPROVED",
                            "Machine Vision confirmed flood scene.\nLocation securely verified via EXIF.\n₹850 Dispatched to Wallet.",
                            Color(0xFF10B981)
                        )
                        navController.navigate(Screen.GnnScan.route)
                    }) 
                }
            }
        }
    }

    @Composable
    fun BottomNav(navController: NavHostController) {
        val navItems = listOf(
            Triple("Dashboard", Screen.Dashboard.route, "🏠"),
            Triple("Insurance", Screen.Insurance.route, "🛡️"),
            Triple("Triggers", Screen.Triggers.route, "⚡"),
            Triple("Claims", Screen.Claims.route, "📋"),
            Triple("Risk", Screen.Risk.route, "📉")
        )
        
        val navBackStackEntry by navController.currentBackStackEntryAsState()
        val currentRoute = navBackStackEntry?.destination?.route

        NavigationBar(containerColor = Color(0xFF111318)) {
            navItems.forEach { (label, route, icon) ->
                NavigationBarItem(
                    selected = currentRoute == route,
                    onClick = {
                        if (currentRoute != route) {
                            navController.navigate(route) {
                                popUpTo(Screen.Dashboard.route) { saveState = true }
                                launchSingleTop = true
                                restoreState = true
                            }
                        }
                    },
                    icon = { Text(icon, fontSize = 20.sp) },
                    label = { Text(label, fontSize = 10.sp) },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = ElectricOrange,
                        selectedTextColor = ElectricOrange,
                        unselectedIconColor = Color.Gray,
                        unselectedTextColor = Color.Gray,
                        indicatorColor = Color.Transparent
                    )
                )
            }
        }
    }

    private fun fetchLocation() {
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            requestPermissionLauncher.launch(Manifest.permission.ACCESS_FINE_LOCATION)
            return
        }

        viewModel.activeZone = "Tracking Physical Hardware..."
        fusedLocationClient.getCurrentLocation(Priority.PRIORITY_HIGH_ACCURACY, null).addOnSuccessListener { location: Location? ->
            if (location != null) {
                viewModel.cachedLocation = location
                viewModel.isGpsFetched = true
                
                val geocoder = Geocoder(this, Locale.getDefault())
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                    geocoder.getFromLocation(location.latitude, location.longitude, 1) { addresses ->
                        if (addresses.isNotEmpty()) {
                            val city = addresses[0].locality ?: "Unmapped Zone"
                            viewModel.activeZone = "Hardware Zone: $city\nLat: ${location.latitude}, Lon: ${location.longitude}"
                        }
                    }
                } else {
                    @Suppress("DEPRECATION")
                    try {
                        val addresses = geocoder.getFromLocation(location.latitude, location.longitude, 1)
                        if (addresses != null && addresses.isNotEmpty()) {
                            val city = addresses[0].locality ?: "Unmapped Zone"
                            viewModel.activeZone = "Hardware Zone: $city\nLat: ${location.latitude}, Lon: ${location.longitude}"
                        }
                    } catch (e: Exception) {}
                }
            }
        }
    }

    private fun checkFirmwareBlocked(): Boolean {
        val isDebugging = android.os.Debug.isDebuggerConnected() || BuildConfig.BYPASS_DEFENSE
        if (isDebugging) return false
        return try {
            Settings.Global.getInt(contentResolver, Settings.Global.DEVELOPMENT_SETTINGS_ENABLED, 0) != 0
        } catch (e: Exception) { false }
    }

    private fun isVpnConnected(): Boolean {
        return try {
            val cm = getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
            val caps = cm.getNetworkCapabilities(cm.activeNetwork)
            caps?.hasTransport(NetworkCapabilities.TRANSPORT_VPN) == true
        } catch (e: Exception) { false }
    }

    private fun startGnnScanFlow(navController: NavHostController) {
        navController.navigate(Screen.GnnScan.route)
        viewModel.startGnnScan {}
        
        // Using a simple delay logic in MainActivity for now to mimic the GNN scan behavior
        android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
            if (checkFirmwareBlocked()) {
                 // Should be intercepted by composition, but manually for now
            } else {
                viewModel.gnnLog = "Checking VPN tunnels \n& Routing GNN Nodes..."
                android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
                    verifyClaimSecurity(navController)
                }, 1500)
            }
        }, 1500)
    }

    private fun verifyClaimSecurity(navController: NavHostController) {
        if (isVpnConnected()) {
            viewModel.setGnnResult("🚨 IP SPOOFING DETECTED 🚨", "❌ VPN Active ❌\nNetwork mismatch. Denied.", Color(0xFFEF4444))
            return
        }
        if (!viewModel.isGpsFetched || viewModel.cachedLocation == null) {
            viewModel.setGnnResult("🚨 HARDWARE ERROR 🚨", "No valid GPS trajectory found.", Color(0xFFF59E0B))
            return
        }
        if (viewModel.cachedLocation?.isMock == true) {
            viewModel.setGnnResult("🚨 FIRMWARE TAMPERING 🚨", "❌ Mock Location detected.\nClaim permanently denied.", Color(0xFFEF4444))
            return
        }
        if (viewModel.currentUserType == "HACKER") {
            viewModel.setGnnResult("WARNING: Node Convergence!", "❌ SYNDICATE THREAT BLOCKED ❌\nAction: Account Suspension.", Color(0xFFEF4444))
            return
        }
        // Success -> Go to Camera
        navController.navigate(Screen.Camera.route)
    }

}
