# ⚡ Energy Flow Maze

A procedural puzzle game built with **Python + Pygame** where players route energy from a source to a destination by rotating and arranging circuit tiles.

---

## 🎮 Gameplay Overview

You control a grid-based circuit system where:

- 🔵 **Battery (Source)** generates energy
- 🟣 **LED (Goal)** lights up when powered
- 🔀 **Wires** must be rotated to form a valid path
- 🔘 **Switches** can enable/disable parts of the circuit
- 🧱 **Resistors** slow down energy flow
- ⚡ **Capacitors** introduce charging delay before allowing flow

Your goal is simple:

> Connect the battery to the LED and successfully transmit energy through the circuit.

---

## 🧩 Core Mechanics

### 🔌 Energy Flow System
Energy travels step-by-step through connected tiles. If the path is broken or blocked, the flow stops.

---

### 🔄 Tile Rotation
- **Left Click:** Rotate tile clockwise
- **Right Click:** Rotate tile counter-clockwise (or toggle switch if present)

---

### ⚙️ Components

| Component | Function |
|----------|----------|
| 🔀 Wires | Create paths for energy flow |
| 🔘 Switch | Can block or allow flow |
| 🧱 Resistor | Slows down energy movement |
| ⚡ Capacitor | Adds charge delay before passing energy |

---

## 🧠 Puzzle System

- Each puzzle is **procedurally generated**
- There is always a **valid path from Battery → LED**
- Additional random wires create complexity and challenge
- Components are placed to modify flow behavior and difficulty

---

## 🎯 Win Condition

The puzzle is solved when:

> Energy successfully reaches the LED and it lights up.

---

## 🕹 Controls

- **Left Click:** Rotate tile clockwise  
- **Right Click:** Rotate tile / toggle switch  
- **START Button:** Begin energy simulation  
- **R Key:** Restart puzzle  
- **ESC:** Exit game  

---

## 🚀 Features

- Procedural puzzle generation
- Real-time energy propagation animation
- Circuit-based logic simulation (resistors + capacitors)
- Interactive switches
- Visual feedback system (glowing energy path)
- Fully replayable puzzles

---

## 🛠 Tech Stack

- Python 3
- Pygame

---

## 📦 Installation

```bash
pip install pygame