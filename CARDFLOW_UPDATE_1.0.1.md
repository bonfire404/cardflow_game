# 🎴 Cardflow Update 1.0.1: The Integrity & Balance Patch

> **Version:** 1.0.1  
> **Status:** Live  
> **Region:** Philippines  

---

## 🛠️ Changelog

### **Visuals & UI Enhancements**
*   **Refined Chip System**: Overhauled in-game chip visuals to prevent table clutter and overflow, ensuring a clean high-stakes environment.
*   **Player Profile Preview**: Redesigned the in-game profile preview for a more modern and readable look.
*   **Mission Modal Upgrade**: Improved the Lobby Mission Modal. Users can now claim rewards, with coins credited instantly to their balance.
*   **Hand Interaction**: Improved card handling during both **Melding** and **Eating** phases for smoother drag-and-drop mechanics.
*   **Result Phase Polish**: Enhanced the points display on the result screen for better clarity on how scores are calculated.

### **Bug Fixes & Stability**
*   **Lobby Navigation**: Fixed an error where the AI Mode would crash or hang when returning to the Lobby.
*   **Initiation Phase**: Resolved an issue in the "Fight or Fold" decision phase where the UI could become unresponsive.
*   **Audio Persistence**: Fixed a bug where game sounds would continue playing even when the game was paused.

### **🛡️ Security & Integrity (Major)**
*   **HMAC-SHA256 Implementation**: Deployed a robust cryptographic signing system for all save data. This prevents manual tampering with Coins, Levels, or Ranks.
*   **Anti-Debug Suite**: Integrated advanced debugger detection to stop reverse engineering and real-time memory manipulation.
*   **Automatic Reset Protocol**: Any detected breach or tampering now triggers an automatic profile reset to protect the ecosystem's integrity.

---

## ⚡ Buffs & Economy Balancing

### **XP Progression Overhaul**
We've significantly increased XP gains to make the journey to Ranked Mode (Level 50) more rewarding and less of a "grind."

| Match Result | Old XP | New XP | % Increase |
| :--- | :--- | :--- | :--- |
| **Normal Win** | 150 | **400** | +166% |
| **Tongits Win** | 200 | **600** | +200% |
| **Match Loss** | 30 | **150** | +400% |

### **AI Difficulty & Aggression**
Bots have been retrained with new behavioral models based on the table's stakes.

| Bet Limit | Difficulty | Playstyle Description |
| :--- | :--- | :--- |
| **100–300** | EASY | Aggressive, drops melds instantly, predictable discards. |
| **600** | MEDIUM | Balanced, holds some melds, basic card counting. |
| **1k–3k** | HARD | Strategic, uses Game Memory, bluffs occasionally. |
| **5k** | **ELITE** (New) | Highly Tactical. Uses advanced opponent modeling; avoids discarding cards you need. |
| **10k+** | **LEGENDARY** | The Grandmasters. Perfect memory, ultra-deceptive holds, and mathematically optimal decisions. |

---

## 🔻 Ranked Mode Adjustments (Nerfs)

To maintain the prestige of the **Immortal** rank, we are increasing the penalties for losses and unsportsmanlike conduct.

| Event | Current Penalty | **Buffed Penalty** | Rationale |
| :--- | :--- | :--- | :--- |
| **Ranked Loss** | -10 RP × Mult | **-30 RP × Mult** | Ensures a ~1:1 win/loss requirement to climb. |
| **Leaving Mid-Game** | -100 RP | **-250 RP** | Leaving now costs 25% of a full rank tier. |
| **Leaver XP Penalty** | -500 XP | **-1,000 XP** | Significant setback to account level progression. |

---

> [!IMPORTANT]
> This update is mandatory. Please ensure your client is updated to **v1.0.1** to continue playing in Ranked matches. Also ensure to delete the older version if encountered data corruption issues.
