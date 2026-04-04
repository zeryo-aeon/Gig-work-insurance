package com.devtrails.gigshield.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.devtrails.gigshield.MainViewModel
import com.devtrails.gigshield.ui.components.GigCard
import com.devtrails.gigshield.ui.components.InfoItem
import com.devtrails.gigshield.ui.theme.ElectricOrange
import com.devtrails.gigshield.ui.theme.Gray500
import com.devtrails.gigshield.ui.theme.InfoSky

@Composable
fun TabScreenLayout(title: String, content: @Composable ColumnScope.() -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .padding(20.dp)
    ) {
        Text(
            text = title,
            style = MaterialTheme.typography.headlineMedium,
            color = Color.White,
            modifier = Modifier.padding(bottom = 24.dp)
        )
        content()
    }
}

@Composable
fun InsuranceScreen(viewModel: MainViewModel) {
    LaunchedEffect(Unit) { viewModel.fetchInsurancePlans() }

    TabScreenLayout(title = "Insurance Plans") {
        LazyColumn(verticalArrangement = Arrangement.spacedBy(16.dp)) {
            items(viewModel.insurancePlans) { plan ->
                GigCard {
                    Text(text = "🛡️ ${plan["name"]}", style = MaterialTheme.typography.titleMedium, color = Color.White)
                    Text(text = plan["description"].toString(), style = MaterialTheme.typography.bodySmall, color = Gray500, modifier = Modifier.padding(vertical = 8.dp))
                    Text(text = "Price: ₹${plan["base_price"]}/week", style = MaterialTheme.typography.labelSmall, color = InfoSky, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

@Composable
fun TriggersScreen(viewModel: MainViewModel) {
    LaunchedEffect(Unit) { viewModel.fetchTriggers() }

    TabScreenLayout(title = "Live Triggers") {
        LazyColumn(verticalArrangement = Arrangement.spacedBy(16.dp)) {
            items(viewModel.insuranceTriggers) { trigger ->
                val status = trigger["status"].toString()
                val statusColor = if (status == "triggered") Color(0xFFEF4444) else Color(0xFF10B981)
                
                GigCard {
                    Text(text = "${trigger["icon"]} ${trigger["name"]}", style = MaterialTheme.typography.titleMedium, color = Color.White)
                    Text(text = "Current Value: ${trigger["current_value"]}", style = MaterialTheme.typography.bodySmall, color = Gray500, modifier = Modifier.padding(vertical = 8.dp))
                    Text(text = "Status: ${status.uppercase()} · Payout: ${trigger["payout"]}", style = MaterialTheme.typography.labelSmall, color = statusColor, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

@Composable
fun ClaimsScreen(viewModel: MainViewModel) {
    LaunchedEffect(Unit) { viewModel.fetchClaims() }

    TabScreenLayout(title = "Claims History") {
        LazyColumn(verticalArrangement = Arrangement.spacedBy(16.dp)) {
            items(viewModel.claimsHistory) { claim ->
                GigCard {
                    Text(text = "${claim["icon"]} ${claim["title"]}", style = MaterialTheme.typography.titleMedium, color = Color.White)
                    Text(text = claim["detail"].toString(), style = MaterialTheme.typography.bodySmall, color = Gray500, modifier = Modifier.padding(vertical = 8.dp))
                    Text(text = "Amount: ₹${claim["amount"]} · Status: ${claim["status"]}", style = MaterialTheme.typography.labelSmall, color = Color(0xFFF97316), fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

@Composable
fun RiskScreen(viewModel: MainViewModel) {
    LaunchedEffect(Unit) { viewModel.fetchRiskFactors() }

    TabScreenLayout(title = "Risk Analytics") {
        LazyColumn(verticalArrangement = Arrangement.spacedBy(16.dp)) {
            item {
                GigCard(backgroundColor = Color(0xFF181C24)) {
                    Text(text = "Overall Risk: ${viewModel.riskScore}/100", style = MaterialTheme.typography.titleLarge, color = Color.White)
                    Text(text = "Safety Level: ${viewModel.overallRiskLevel}", style = MaterialTheme.typography.bodySmall, color = Gray500)
                    Text(text = "Scanning 10+ real-time behavioral nodes...", style = MaterialTheme.typography.labelSmall, color = Color.Yellow, modifier = Modifier.padding(top = 8.dp))
                }
            }

            items(viewModel.riskFactors) { factor ->
                val score = factor["score"] as Double
                val factorColor = if (score > 70) Color(0xFFEF4444) else Color.LightGray
                
                GigCard {
                    Text(text = "● ${factor["name"]}", style = MaterialTheme.typography.titleMedium, color = Color.White)
                    Text(text = "Impact Score", style = MaterialTheme.typography.bodySmall, color = Gray500)
                    Text(text = "$score% correlation to incident risk", style = MaterialTheme.typography.labelSmall, color = factorColor, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

@Composable
fun SessionInfoScreen(viewModel: MainViewModel, onBack: () -> Unit) {
    TabScreenLayout(title = "Session Hardware") {
        GigCard {
            InfoItem(title = "Rider Identity", value = viewModel.currentUser ?: "Unknown", icon = "👤")
            InfoItem(title = "Connection Node", value = "${viewModel.serverIp}:${viewModel.serverPort}", icon = "🌐", color = InfoSky)
            InfoItem(title = "Sync Protocol", value = "JWT-SHA256 Over TLS", icon = "🔐")
            InfoItem(title = "Active Location", value = viewModel.activeZone, icon = "📍")
        }
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Button(
            onClick = onBack,
            modifier = Modifier.fillMaxWidth().height(50.dp),
            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF181C24)),
            shape = MaterialTheme.shapes.medium
        ) {
            Text("BACK TO DASHBOARD", style = MaterialTheme.typography.labelSmall, color = Color.White)
        }
    }
}
