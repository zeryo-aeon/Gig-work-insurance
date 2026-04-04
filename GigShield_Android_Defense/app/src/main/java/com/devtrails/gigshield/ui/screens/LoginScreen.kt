package com.devtrails.gigshield.ui.screens

import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.devtrails.gigshield.MainViewModel
import com.devtrails.gigshield.ui.components.GigCard
import com.devtrails.gigshield.ui.components.StyledButton
import com.devtrails.gigshield.ui.theme.ElectricOrange
import com.devtrails.gigshield.ui.theme.Gray400
import com.devtrails.gigshield.ui.theme.Gray500
import com.devtrails.gigshield.ui.theme.Gray800

data class DemoAccount(val emoji: String, val name: String, val id: String, val pass: String, val color: Color = ElectricOrange)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LoginScreen(
    viewModel: MainViewModel,
    onNavigateToSignup: () -> Unit,
    onLoginSuccess: () -> Unit
) {
    var username by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    val context = LocalContext.current
    val scrollState = rememberScrollState()

    val demoAccounts = listOf(
        DemoAccount("👑", "ADMIN", "ADMIN-001", "admin123", Color(0xFF9333EA)),
        DemoAccount("🛵", "RAJU", "GW-8821", "rider123"),
        DemoAccount("🛵", "PRIYA", "GW-4422", "rider456"),
        DemoAccount("🛵", "VIKRAM", "GW-9901", "rider789")
    )

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .padding(24.dp)
            .verticalScroll(scrollState),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        // Hero Section
        LaunchedEffect(viewModel.serverIp, viewModel.serverPort) {
            viewModel.checkServerStatus()
        }

        Text(
            text = "ShieldGig",
            style = MaterialTheme.typography.displayLarge,
            color = ElectricOrange,
            modifier = Modifier.padding(bottom = 4.dp)
        )
        Text(
            text = "// Parametric Insurance v2.0",
            style = MaterialTheme.typography.labelSmall,
            color = Gray500,
            modifier = Modifier.padding(bottom = 32.dp)
        )

        // Login Card
        GigCard(backgroundColor = MaterialTheme.colorScheme.surface) {
            Text(
                text = "Rider Sign In",
                style = MaterialTheme.typography.titleLarge,
                modifier = Modifier.padding(bottom = 4.dp)
            )
            Text(
                text = "Enter credentials & server IP",
                style = MaterialTheme.typography.labelSmall,
                color = Gray500,
                modifier = Modifier.padding(bottom = 20.dp)
            )

            // Inputs
            TextField(
                value = username,
                onValueChange = { username = it },
                modifier = Modifier.fillMaxWidth().padding(bottom = 12.dp),
                placeholder = { Text("Rider ID (e.g. rahul)") },
                shape = RoundedCornerShape(12.dp),
                colors = TextFieldDefaults.colors(
                    focusedContainerColor = Gray800,
                    unfocusedContainerColor = Gray800,
                    focusedIndicatorColor = Color.Transparent,
                    unfocusedIndicatorColor = Color.Transparent,
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White
                )
            )

            TextField(
                value = password,
                onValueChange = { password = it },
                modifier = Modifier.fillMaxWidth().padding(bottom = 20.dp),
                placeholder = { Text("Password") },
                visualTransformation = PasswordVisualTransformation(),
                shape = RoundedCornerShape(12.dp),
                colors = TextFieldDefaults.colors(
                    focusedContainerColor = Gray800,
                    unfocusedContainerColor = Gray800,
                    focusedIndicatorColor = Color.Transparent,
                    unfocusedIndicatorColor = Color.Transparent,
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White
                )
            )

            HorizontalDivider(color = Gray800, thickness = 1.dp, modifier = Modifier.padding(bottom = 16.dp))

            // Connection Settings
            Row(
                modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "CONNECTION SETTINGS",
                    style = MaterialTheme.typography.labelSmall,
                    color = Gray400,
                    modifier = Modifier.weight(1f)
                )
                
                // Connection Indicator
                Box(
                    modifier = Modifier
                        .size(8.dp)
                        .background(
                            if (viewModel.isServerReachable) Color(0xFF10B981) else Color(0xFFEF4444),
                            shape = androidx.compose.foundation.shape.CircleShape
                        )
                )
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    text = viewModel.connectionStatus,
                    style = MaterialTheme.typography.labelSmall,
                    color = if (viewModel.isServerReachable) Color(0xFF10B981) else Gray500
                )
            }

            Row(
                modifier = Modifier.fillMaxWidth().padding(bottom = 12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Use Localhost Bridge (10.0.2.2)",
                    style = MaterialTheme.typography.bodySmall,
                    color = Gray400,
                    modifier = Modifier.weight(1f)
                )
                Switch(
                    checked = viewModel.useLocalhost,
                    onCheckedChange = { 
                        viewModel.useLocalhost = it
                        if (it) viewModel.serverIp = "10.0.2.2"
                    },
                    colors = SwitchDefaults.colors(checkedThumbColor = ElectricOrange)
                )
            }

            Row(modifier = Modifier.fillMaxWidth()) {
                TextField(
                    value = viewModel.serverIp,
                    onValueChange = { 
                        viewModel.serverIp = it
                        viewModel.useLocalhost = (it == "10.0.2.2")
                    },
                    modifier = Modifier.weight(3f).padding(end = 8.dp),
                    placeholder = { Text("Server IP") },
                    shape = RoundedCornerShape(12.dp),
                    colors = TextFieldDefaults.colors(
                        focusedContainerColor = Gray800,
                        unfocusedContainerColor = Gray800,
                        focusedIndicatorColor = Color.Transparent,
                        unfocusedIndicatorColor = Color.Transparent
                    )
                )
                TextField(
                    value = viewModel.serverPort,
                    onValueChange = { viewModel.serverPort = it },
                    modifier = Modifier.weight(1f),
                    placeholder = { Text("8000") },
                    shape = RoundedCornerShape(12.dp),
                    colors = TextFieldDefaults.colors(
                        focusedContainerColor = Gray800,
                        unfocusedContainerColor = Gray800,
                        focusedIndicatorColor = Color.Transparent,
                        unfocusedIndicatorColor = Color.Transparent
                    )
                )
            }

            // Demo Accounts
            Text(
                text = "SWIPE FOR DEMO ACCOUNTS:",
                style = MaterialTheme.typography.labelSmall,
                color = Gray500,
                modifier = Modifier.padding(top = 16.dp, bottom = 8.dp)
            )

            LazyRow(modifier = Modifier.fillMaxWidth().padding(bottom = 24.dp)) {
                items(demoAccounts) { demo ->
                    AssistChip(
                        onClick = {
                            username = demo.id
                            password = demo.pass
                            Toast.makeText(context, "Demo: ${demo.name}", Toast.LENGTH_SHORT).show()
                        },
                        label = { Text("${demo.emoji} ${demo.name}") },
                        modifier = Modifier.padding(end = 8.dp),
                        colors = AssistChipDefaults.assistChipColors(labelColor = demo.color)
                    )
                }
            }

            // Login Button
            StyledButton(
                text = if (viewModel.isLoggingIn) "SYNCING..." else "SECURE LOGIN →",
                onClick = {
                    if (viewModel.isFirmwareBlocked) {
                        // Handled by Navigation or Overlay
                    } else {
                        viewModel.performLogin(
                            username, password,
                            onSuccess = { onLoginSuccess() },
                            onError = { Toast.makeText(context, it, Toast.LENGTH_SHORT).show() }
                        )
                    }
                }
            )

            Text(
                text = "Don't have an ID? Create Pilot Account",
                style = MaterialTheme.typography.bodySmall.copy(fontWeight = FontWeight.Bold),
                color = ElectricOrange,
                textAlign = TextAlign.Center,
                modifier = Modifier.fillMaxWidth().padding(top = 20.dp).clickable { onNavigateToSignup() }
            )
        }

        Text(
            text = "🔐 Secured with JWT · Fingerprint Verified",
            style = MaterialTheme.typography.labelSmall,
            color = Gray500,
            modifier = Modifier.padding(top = 20.dp)
        )
    }
}
