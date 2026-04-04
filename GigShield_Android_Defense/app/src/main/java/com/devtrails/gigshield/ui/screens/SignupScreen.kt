package com.devtrails.gigshield.ui.screens

import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
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
import com.devtrails.gigshield.ui.theme.Gray500
import com.devtrails.gigshield.ui.theme.Gray800

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SignupScreen(
    viewModel: MainViewModel,
    onNavigateToLogin: () -> Unit
) {
    var name by remember { mutableStateOf("") }
    var phone by remember { mutableStateOf("") }
    var zone by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    val context = LocalContext.current
    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .padding(24.dp)
            .verticalScroll(scrollState),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "Join ShieldGig",
            style = MaterialTheme.typography.displayMedium.copy(fontSize = 32.sp, fontWeight = FontWeight.Bold),
            color = ElectricOrange,
            modifier = Modifier.padding(bottom = 32.dp)
        )

        GigCard(backgroundColor = MaterialTheme.colorScheme.surface) {
            TextField(
                value = name,
                onValueChange = { name = it },
                modifier = Modifier.fillMaxWidth().padding(bottom = 12.dp),
                placeholder = { Text("Full Name") },
                shape = RoundedCornerShape(12.dp),
                colors = TextFieldDefaults.colors(
                    focusedContainerColor = Gray800,
                    unfocusedContainerColor = Gray800,
                    focusedIndicatorColor = Color.Transparent,
                    unfocusedIndicatorColor = Color.Transparent
                )
            )

            TextField(
                value = phone,
                onValueChange = { phone = it },
                modifier = Modifier.fillMaxWidth().padding(bottom = 12.dp),
                placeholder = { Text("Phone Number") },
                shape = RoundedCornerShape(12.dp),
                colors = TextFieldDefaults.colors(
                    focusedContainerColor = Gray800,
                    unfocusedContainerColor = Gray800,
                    focusedIndicatorColor = Color.Transparent,
                    unfocusedIndicatorColor = Color.Transparent
                )
            )

            TextField(
                value = zone,
                onValueChange = { zone = it },
                modifier = Modifier.fillMaxWidth().padding(bottom = 12.dp),
                placeholder = { Text("City / Zone") },
                shape = RoundedCornerShape(12.dp),
                colors = TextFieldDefaults.colors(
                    focusedContainerColor = Gray800,
                    unfocusedContainerColor = Gray800,
                    focusedIndicatorColor = Color.Transparent,
                    unfocusedIndicatorColor = Color.Transparent
                )
            )

            TextField(
                value = password,
                onValueChange = { password = it },
                modifier = Modifier.fillMaxWidth().padding(bottom = 24.dp),
                placeholder = { Text("Create Password") },
                visualTransformation = PasswordVisualTransformation(),
                shape = RoundedCornerShape(12.dp),
                colors = TextFieldDefaults.colors(
                    focusedContainerColor = Gray800,
                    unfocusedContainerColor = Gray800,
                    focusedIndicatorColor = Color.Transparent,
                    unfocusedIndicatorColor = Color.Transparent
                )
            )

            StyledButton(
                text = "SIGN UP & JOIN →",
                onClick = {
                    Toast.makeText(context, "Account Created! Redirecting...", Toast.LENGTH_SHORT).show()
                    onNavigateToLogin()
                }
            )

            Text(
                text = "Already have an account? Sign In",
                style = MaterialTheme.typography.bodySmall.copy(fontWeight = FontWeight.Bold),
                color = Gray500,
                textAlign = TextAlign.Center,
                modifier = Modifier.fillMaxWidth().padding(top = 20.dp).clickable { onNavigateToLogin() }
            )
        }
    }
}
