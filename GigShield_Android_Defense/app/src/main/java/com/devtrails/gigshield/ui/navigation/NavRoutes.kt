package com.devtrails.gigshield.ui.navigation

sealed class Screen(val route: String) {
    object Login : Screen("login")
    object Signup : Screen("signup")
    object Dashboard : Screen("dashboard")
    object Insurance : Screen("insurance")
    object Triggers : Screen("triggers")
    object Claims : Screen("claims")
    object Risk : Screen("risk")
    object Admin : Screen("admin")
    object SessionInfo : Screen("session_info")
    object GnnScan : Screen("gnn_scan")
    object Camera : Screen("camera")
    object FirmwareLock : Screen("firmware_lock")
}
