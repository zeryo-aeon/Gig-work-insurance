# Phase 2 Deliverables

## Overview
This document outlines the deliverables and features implemented for Phase 2 of the Gig-work-insurance platform.

## Deliverables

### 1. Demo Video
A 2-minute demo video demonstrating the full platform workflow is uploaded to a publicly accessible link.

### 2. Executable Source Code
The provided source code showcases the following core workflows:
- **Registration Process:** Smooth, user-friendly onboarding for gig workers.
- **Insurance Policy Management:** Dashboard to view, manage, and understand active policies.
- **Dynamic Premium Calculation:** AI-driven real-time premium adjustments.
- **Claims Management:** Automated claim initiation and tracking.

## Advanced Features & Implementations

### AI Integration: Dynamic Pricing Models
We implemented Machine Learning models to adjust weekly premiums based on hyper-local risk factors.
- The model actively adjusts costs (e.g., reducing the weekly premium by ₹2 if the worker operates in a zone historically safe from water logging).
- The system dynamically offers increased coverage hours based on predictive weather modeling and risk assessment.

### Automated Triggers
We've built automated triggers utilizing public/mock APIs (such as OpenMeteo and Geoapify) to identify disruptions that lead to a loss of income:
1. **Severe Weather Alerts:** Heavy rainfall or cyclones triggering safety nets.
2. **Environmental Hazards:** Poor air quality (AQI) conditions triggering health-related premium adjustments or downtime claims.
3. **Route/Traffic Disruptions:** Unnavigable zones identified via real-time map analytics.

### Zero-Touch Claim Process
What is the best User Experience for our customers? **Not having to file a claim at all.**
- We have engineered a seamless, zero-touch claim process. 
- When an automated trigger (e.g., severe weather preventing work) fires, the system automatically logs the disruption and deposits the claim amount directly into the worker's account, with absolutely zero filing required from their end.
