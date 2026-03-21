# 🛡️ GigShield: Android Firmware Defense (Phase 1 Crisis Response)

🚨 **24-HOUR EMERGENCY HACKATHON RESPONSE** 🚨

## What is this app?
This is a **100% Native Kotlin Android Application** built to solve the DEVTrails Phase 1 Crisis. 
When 500 delivery workers organized a GPS-spoofing syndicate to drain the insurance liquidity pool from their couches, we realized that simple Web APIs and standard HTML5 location checks could not stop them. Browsers are sandboxed and blind.

We engineered **GigShield** to natively query the Android Kernel and act as a hardware-level gatekeeper.

## How it stops the Crisis:
1. **Developer Mode Lock (Firmware Defense):** The app checks `Settings.Global` on boot. If it detects rooted/developer settings (the prerequisite for GPS spoofing software), it instantly drops a red "App Locked" overlay and halts the claim process.
2. **Native VPN Triangulation:** We invoke Android's `ConnectivityManager` to detect `NetworkCapabilities.TRANSPORT_VPN`. If the IP address is masked by a tunnel, we flag the claim for fingerprint mismatches.
3. **Graph Neural Network (GNN) Simulation:** The app's backend simulates our "Impossible Teleportation" GNN model. If 500 physical nodes cluster precisely in a flooded zone without trajectory data, the algorithm blocks the AI transaction.
4. **Tier 2 Camera (UX Balance):** Honest workers who just simply lost network in a storm are protected. The app asks for a *Micro-Proof of Presence* (a photo upload) verified asynchronously via EXIF data, rather than auto-denying their claim!

---

## 📥 How to Install & Demo (For Judges)

We highly encourage judges to try hacking this app themselves on a physical phone!

1. **Download the APK File:**  
   ⬇️ **[CLICK HERE TO DOWNLOAD `GigShield-Defense-App.apk`](GigShield-Defense-App.apk)** ⬇️  
   *(Downloads directly from this repository folder)*
2. **Transfer to your Android Phone:** E-mail it to yourself or use Google Drive. 
3. **Install It:** Open the `.apk` on your phone. (If prompted, allow "Install from unknown sources").
4. **Perform the Hack Test:** 
   - Turn on Developer Options in your phone settings.
   - Open the app. Watch the system lock you out instantly!

![Firmware Lock Preview](https://images.unsplash.com/photo-1563206767-5b18f218e8de?auto=format&fit=crop&w=600&q=80) 
*(Example of our Native Lock UI blocking compromised endpoints)*
