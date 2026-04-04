package com.devtrails.gigshield.ui.screens

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.devtrails.gigshield.MainViewModel
import com.devtrails.gigshield.ui.components.GigCard
import com.devtrails.gigshield.ui.components.StyledButton
import com.devtrails.gigshield.ui.theme.ElectricOrange
import com.devtrails.gigshield.ui.theme.ErrorVivid
import com.devtrails.gigshield.ui.theme.Gray500
import com.devtrails.gigshield.ui.theme.SuccessEmerald

@Composable
fun GnnScanScreen(
    viewModel: MainViewModel,
    onBack: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        if (viewModel.isGnnScanning || !viewModel.isGnnScanComplete) {
            CircularProgressIndicator(
                modifier = Modifier.size(80.dp),
                color = ElectricOrange,
                strokeWidth = 6.dp
            )
            Spacer(modifier = Modifier.height(32.dp))
        }

        Text(
            text = viewModel.gnnLog,
            style = MaterialTheme.typography.bodyLarge.copy(fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace),
            color = Color.White,
            textAlign = TextAlign.Center
        )

        if (viewModel.isGnnScanComplete) {
            Spacer(modifier = Modifier.height(24.dp))
            GigCard(backgroundColor = Color(0xFF111318)) {
                Text(
                    text = viewModel.gnnResult,
                    style = MaterialTheme.typography.bodyLarge.copy(
                        fontWeight = FontWeight.Bold,
                        color = viewModel.gnnStatusColor
                    ),
                    textAlign = TextAlign.Center,
                    modifier = Modifier.fillMaxWidth()
                )
            }
            Spacer(modifier = Modifier.height(32.dp))
            StyledButton(
                text = "RETURN TO DASHBOARD",
                onClick = onBack,
                containerColor = Color(0xFF181C24)
            )
        }
    }
}

@Composable
fun CameraScreen(
    onCapture: () -> Unit
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black)
    ) {
        // UI overlay for "Camera"
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            Text(
                text = "PHYSICAL PROOF REQUIRED",
                style = MaterialTheme.typography.labelSmall,
                color = Color.White,
                modifier = Modifier.background(Color.Black.copy(alpha = 0.6f), RoundedCornerShape(4.dp)).padding(4.dp)
            )

            // Simulated viewfinder center
            Box(
                modifier = Modifier
                    .size(280.dp)
                    .background(Color.Transparent, RoundedCornerShape(2.dp))
                    .padding(2.dp)
            ) {
                // Bracket simulation (Corners) could be added here
            }

            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = "Position scene (Heavy Rain / Flood) in frame",
                    style = MaterialTheme.typography.bodySmall,
                    color = Color.LightGray,
                    modifier = Modifier.padding(bottom = 16.dp)
                )
                
                StyledButton(
                    text = "📸 CAPTURE & ANALYZE",
                    onClick = onCapture,
                    containerColor = SuccessEmerald
                )
            }
        }
    }
}

@Composable
fun FirmwareLockScreen(
    onRetry: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF0F172A))
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(text = "🛡️", fontSize = 64.sp)
        Text(
            text = "FIRMWARE BREACH",
            style = MaterialTheme.typography.headlineMedium,
            color = ErrorVivid,
            modifier = Modifier.padding(top = 16.dp)
        )
        Text(
            text = "Integrity Scan Failed\n(Developer Mode Active / USB Hooked)",
            style = MaterialTheme.typography.bodyLarge,
            color = Color.White,
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(top = 8.dp, bottom = 24.dp)
        )
        
        Text(
            text = "Security policies forbid hardware access while low-level debugging modes are enabled. Turn off Developer Options in settings to proceed.",
            style = MaterialTheme.typography.bodySmall,
            color = Gray500,
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(bottom = 32.dp)
        )

        StyledButton(
            text = "RE-SCAN INTEGRITY",
            onClick = onRetry,
            containerColor = Color.White,
            contentColor = Color(0xFF0F172A)
        )
    }
}
