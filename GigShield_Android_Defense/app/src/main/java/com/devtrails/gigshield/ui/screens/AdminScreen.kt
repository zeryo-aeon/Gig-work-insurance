package com.devtrails.gigshield.ui.screens

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.devtrails.gigshield.MainViewModel
import com.devtrails.gigshield.ui.components.GigCard
import com.devtrails.gigshield.ui.theme.Gray500
import com.devtrails.gigshield.ui.theme.SurfaceLighter

@Composable
fun AdminScreen(
    viewModel: MainViewModel,
    onBack: () -> Unit
) {
    val scrollState = rememberScrollState()
    val adminPurple = Color(0xFF9333EA)

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF0A0C10))
    ) {
        // Top Bar
        Surface(
            color = Color(0xFF111318),
            tonalElevation = 4.dp
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(20.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "ADMIN CONSOLE",
                    style = MaterialTheme.typography.labelSmall.copy(fontWeight = FontWeight.Bold),
                    color = adminPurple,
                    modifier = Modifier.weight(1f)
                )

                Button(
                    onClick = onBack,
                    colors = ButtonDefaults.buttonColors(containerColor = SurfaceLighter),
                    shape = RoundedCornerShape(8.dp),
                    modifier = Modifier.height(36.dp),
                    contentPadding = PaddingValues(horizontal = 12.dp)
                ) {
                    Text("RETURN", style = MaterialTheme.typography.labelSmall, color = Color.White)
                }
            }
        }

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(20.dp)
                .verticalScroll(scrollState)
        ) {
            Text(
                text = "XGBoost Analytics",
                style = MaterialTheme.typography.headlineMedium,
                color = Color.White
            )
            Text(
                text = "Select Rider Profile:",
                style = MaterialTheme.typography.labelSmall,
                color = adminPurple,
                modifier = Modifier.padding(top = 4.dp, bottom = 12.dp)
            )

            LazyRow(modifier = Modifier.fillMaxWidth().padding(bottom = 24.dp)) {
                val riders = listOf("RAJU", "PRIYA", "VIKRAM")
                items(riders) { rider ->
                    OutlinedButton(
                        onClick = { viewModel.updateAdminProfile(rider) },
                        modifier = Modifier.padding(end = 8.dp).height(36.dp),
                        border = ButtonDefaults.outlinedButtonBorder.copy(brush = androidx.compose.ui.graphics.SolidColor(adminPurple)),
                        colors = ButtonDefaults.outlinedButtonColors(contentColor = adminPurple),
                        shape = RoundedCornerShape(8.dp),
                        contentPadding = PaddingValues(horizontal = 12.dp)
                    ) {
                        Text(rider, style = MaterialTheme.typography.labelSmall)
                    }
                }
            }

            GigCard(backgroundColor = Color(0xFF111318)) {
                Text(
                    text = "Live Training Weights",
                    style = MaterialTheme.typography.titleSmall,
                    color = Color.White,
                    modifier = Modifier.padding(bottom = 20.dp)
                )

                // XGBoost Bar Chart (Simple implementation)
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(200.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.Bottom
                ) {
                    viewModel.adminBarHeights.forEach { height ->
                        val animatedHeight by animateFloatAsState(
                            targetValue = height,
                            animationSpec = tween(durationMillis = 500)
                        )
                        Box(
                            modifier = Modifier
                                .width(12.dp)
                                .height(animatedHeight.dp)
                                .background(adminPurple, RoundedCornerShape(topStart = 4.dp, topEnd = 4.dp))
                        )
                    }
                }

                Spacer(modifier = Modifier.height(20.dp))

                Text(
                    text = "Historical Convergence Metrics",
                    style = MaterialTheme.typography.labelSmall,
                    color = Gray500,
                    modifier = Modifier.padding(bottom = 4.dp)
                )
                Text(
                    text = viewModel.adminMetrics,
                    style = MaterialTheme.typography.bodyLarge.copy(fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace),
                    color = Color.White
                )
            }
        }
    }
}
