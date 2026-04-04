package com.devtrails.gigshield.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.devtrails.gigshield.MainViewModel
import com.devtrails.gigshield.ui.components.GigCard
import com.devtrails.gigshield.ui.components.StyledButton
import com.devtrails.gigshield.ui.theme.*

@Composable
fun DashboardScreen(
    viewModel: MainViewModel,
    onNavigateToSession: () -> Unit,
    onLogout: () -> Unit,
    onInitClaim: () -> Unit,
    onViewPerformance: () -> Unit
) {
    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
    ) {
        // Custom Top App Bar
        Surface(
            color = MaterialTheme.colorScheme.surface,
            tonalElevation = 4.dp
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(20.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "ShieldGig",
                    style = MaterialTheme.typography.titleLarge,
                    color = ElectricOrange,
                    modifier = Modifier.weight(1f)
                )

                Surface(
                    color = SurfaceLighter,
                    shape = RoundedCornerShape(8.dp),
                    modifier = Modifier
                        .padding(end = 12.dp)
                        .clickable { onNavigateToSession() }
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(text = "🛵 Session", style = MaterialTheme.typography.labelSmall, color = Color.White)
                        Spacer(modifier = Modifier.width(8.dp))
                        Box(modifier = Modifier.size(8.dp).background(SuccessEmerald, RoundedCornerShape(4.dp)))
                    }
                }

                Surface(
                    color = SurfaceLighter,
                    shape = RoundedCornerShape(8.dp),
                    modifier = Modifier
                        .padding(end = 12.dp)
                        .clickable { viewModel.isDarkMode = !viewModel.isDarkMode }
                ) {
                    Text(
                        text = if (viewModel.isDarkMode) "🌙" else "☀️",
                        modifier = Modifier.padding(10.dp)
                    )
                }

                Button(
                    onClick = onLogout,
                    colors = ButtonDefaults.buttonColors(containerColor = ErrorVivid),
                    shape = RoundedCornerShape(8.dp),
                    contentPadding = PaddingValues(horizontal = 12.dp, vertical = 8.dp),
                    modifier = Modifier.height(40.dp)
                ) {
                    Text("OUT", style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.Bold)
                }
            }
        }

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 20.dp)
                .verticalScroll(scrollState)
        ) {
            Spacer(modifier = Modifier.height(20.dp))
            
            Text(
                text = "Hello, ${if (viewModel.currentUserType == "HACKER") "Syndicate Rep" else "Worker"}",
                style = MaterialTheme.typography.headlineMedium,
                color = Color.White
            )
            Text(
                text = "Verified GigShield Zone · Live Updates",
                style = MaterialTheme.typography.labelSmall,
                color = Gray500,
                modifier = Modifier.padding(bottom = 20.dp)
            )

            // Alert Banner
            GigCard(backgroundColor = Color(0xFF271414)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(text = "🌧️", fontSize = 24.sp, modifier = Modifier.padding(end = 16.dp))
                    Column {
                        Text(
                            text = "Parametric Trigger Active — Heavy Rain",
                            style = MaterialTheme.typography.titleSmall,
                            color = Color(0xFFFCA5A5)
                        )
                        Text(
                            text = "Payout of ₹340 queued for today.",
                            style = MaterialTheme.typography.labelSmall,
                            color = Gray500
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(20.dp))

            // KPI Grid
            Row(modifier = Modifier.fillMaxWidth()) {
                KPICard(Modifier.weight(1f), "EARNINGS", viewModel.earnings, SuccessEmerald)
                Spacer(modifier = Modifier.width(8.dp))
                KPICard(Modifier.weight(1f), "INSURANCE", viewModel.insurancePayout, InfoSky)
            }
            Spacer(modifier = Modifier.height(8.dp))
            Row(modifier = Modifier.fillMaxWidth()) {
                KPICard(Modifier.weight(1f), "RISK SCORE", viewModel.riskScore, WarningAmber)
                Spacer(modifier = Modifier.width(8.dp))
                KPICard(Modifier.weight(1f), "PREDICTION", viewModel.prediction, InfoSky)
            }

            Spacer(modifier = Modifier.height(24.dp))

            // GPS Status Card
            GigCard(backgroundColor = SurfaceLighter) {
                Text(
                    text = viewModel.activeZone,
                    style = MaterialTheme.typography.labelSmall,
                    color = Color.White,
                    fontFamily = FontFamily.Monospace,
                    modifier = Modifier.padding(bottom = 12.dp)
                )
                HorizontalDivider(color = Gray800, modifier = Modifier.padding(bottom = 12.dp))
                Text(
                    text = "🚨 High Risk Activity Detected (Tier 2 Protocol)",
                    style = MaterialTheme.typography.titleSmall,
                    color = ErrorVivid
                )
            }

            Spacer(modifier = Modifier.height(24.dp))

            StyledButton(
                text = "SYSTEM PERFORMANCE LOGS",
                onClick = onViewPerformance,
                containerColor = SurfaceLighter,
                contentColor = InfoSky,
                height = 50
            )
            Spacer(modifier = Modifier.height(16.dp))
            StyledButton(
                text = "FILE DISRUPTION CLAIM",
                onClick = onInitClaim,
                containerColor = ElectricOrange,
                height = 65
            )
            Spacer(modifier = Modifier.height(40.dp))
        }
    }
}

@Composable
fun KPICard(modifier: Modifier, title: String, value: String, color: Color) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = SurfaceLighter)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(text = title, style = MaterialTheme.typography.labelSmall, color = Gray500)
            Text(text = value, style = MaterialTheme.typography.titleLarge, color = color)
        }
    }
}
