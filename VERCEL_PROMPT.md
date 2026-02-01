# Prompt for Vercel v0 (Generative UI)

**Goal:** Create a futuristic, dark-mode Security Operations Center (SOC) dashboard UI with a "Cyberpunk/Sci-Fi" aesthetic using Next.js, Tailwind CSS, and Framer Motion.

**Copy and paste the following into [v0.dev](https://v0.dev/):**

```text
Create a futuristic, dark-mode Security Operations Center (SOC) dashboard UI with a "Cyberpunk/Sci-Fi" aesthetic. 

The design should be built with Next.js, Tailwind CSS, and Framer Motion for animations.

**Visual Style:**
- Background: Deep black (#050505) with a subtle animated grid pattern or particle network effect.
- Color Palette: Neon Cyan (#00f3ff) for primary elements, Neon Red (#ff003c) for critical alerts, Neon Purple (#bc13fe) as secondary accent.
- Typography: Use 'Inter' mixed with a monospaced font like 'JetBrains Mono' for data values.
- Components: Glassmorphism cards with thin, glowing borders and sharp corners (not rounded).

**Layout Requirements:**
1. **Header**: 
   - Left: "AI-SOC PLATFORM" logo in bold metallic text.
   - Right: A pulsing "LIVE MONITORING" badge (green dot).
   - User profile dropdown ("Admin").

2. **Top Metrics Row (4 Cards)**:
   - Each card should have a glowing hover effect.
   - Metrics: "Total Events" (blue), "Critical Threats" (red, pulsing), "Auto-Blocked" (purple), "System Health" (green gauge).

3. **Main Content Grid (2 Columns)**:
   - **Left Column (2/3 width)**: 
     - "Global Threat Map": A dotted world map (using a library like react-simple-maps or similar visual style) highlighting attack sources with expanding ripple rings.
     - "Real-time Traffic": An area chart showing network traffic spikes over the last hour.
   - **Right Column (1/3 width)**:
     - "Live Threat Feed": A scrolling list of recent alerts. high-severity items should have a red border left.
     - Items show: Timestamp, Attack Type (e.g., "DDoS Attempt"), Source IP, and Action Taken ("BLOCKED").

4. **Sidebar Navigation**:
   - Icons for: Dashboard, Threat Intel, Analysis, Settings.
   - Active state should have a neon glow bar on the left.

**Interactivity:**
- Add smooth entry animations (fade-in + slide-up) for all cards on load using Framer Motion.
- Buttons should have a "glitch" effect on hover.
- Graphs should be interactive (tooltips on hover).

**Tech Context:** 
This is for a cybersecurity portfolio project. Make it look professional yet highly advanced, like a movie UI interface.
```
