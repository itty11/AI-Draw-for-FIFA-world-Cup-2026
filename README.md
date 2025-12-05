# 🏆 Draw AI for FIFA World Cup 2026 Draw System

![alt text](image-1.png)

This project is an AI-powered system designed to execute a compliant, randomized draw for the 2026 FIFA World Cup (48 teams, 12 groups). It uses a **Constraint Satisfaction Problem (CSP)** solver, implemented via a **backtracking search algorithm**, to ensure all complex FIFA rules and competitive balance constraints are met.

## ✨ Features

* **AI-Powered Draw Engine:** Utilizes a highly efficient backtracking algorithm (`draw_algorithm.py`) to solve the draw puzzle, ensuring a valid result that adheres to all FIFA rules. 

[Image of a backtracking search algorithm flow chart]

* **Comprehensive Constraint Management:** Enforces official rules, including confederation separation limits (except for UEFA), minimum/maximum UEFA teams per group, host pre-allocation (MEX → A, CAN → B, USA → D), and pathway separation for top-ranked teams (e.g., ESP/ARG).
* **Streamlit Web Interface (`app.py`):** Provides an interactive, user-friendly interface to run the draw, view results, and export the official groups list as a PDF.
* **Data-Driven Configuration:** All teams, pots, rules, and placeholder data are managed in easily readable JSON files.

## 📁 Project Structure

| File/Directory | Description |
| :--- | :--- |
| `app.py` | **Main Application File.** Contains the Streamlit UI, the `DrawEngine` optimization logic, and the PDF generation utility. |
| `draw_algorithm.py` | **Core AI Engine.** Implements the fundamental `DrawEngine` class and the recursive backtracking logic (`assign_pot`). |
| `data/` | Directory containing all configuration and input data. |
| `data/pots.json` | Defines the 4 pots (1-4) with 12 teams each, including playoff placeholders. |
| `data/confirmed_teams.json` | Details for all 48 teams (name, ID, confederation, host status, ranking, pot). |
| `data/confederation_rules.json` | The central configuration for all official FIFA rules and constraints, including host assignments and pathway separations. |
| `data/groups.json` | Defines the initial 12 empty groups (A-L) with host pre-assignments. |
| `data/names.json` | A mapping of 3-letter team IDs to full country names. |
| `data/flags.json` | URLs for flag images used in the Streamlit interface. |
| `data/qualifiers.json` | Contains details about the playoff paths (UEFA and Inter-Confederation). |
| `assets/` | Contains project assets, primarily the logo image. |

## 🛠️ Installation and Setup

This project requires Python and Streamlit.

### Prerequisites

* Python 3.8+
* The `streamlit`, `fpdf`, and `Pillow` libraries.

### Setup Steps

1.  **Clone the Repository:**
    ```bash
    git clone [your-repo-link]
    cd AI-Powered-Draw-System
    ```

2.  **Install Dependencies:**
    ```bash
    pip install streamlit fpdf Pillow
    ```

3.  **Run the Application:**
    ```bash
    streamlit run app.py
    ```
    The application will open in your default web browser (usually at `http://localhost:8501`).

---

## 🚀 Future Possibilities and Upgrades

![alt text](image.png)

To transition this project into a cutting-edge, fully integrated AI system, the following four major upgrades are proposed:

### 1. Core AI Engine Upgrade: Transition to Generative AI (Gen AI)

* **Shift from Search to Generation:** Replace the current deterministic Backtracking Search with a **Reinforcement Learning (RL) Agent** (e.g., Deep Q-Network - DQN).
* **Benefit:** The RL agent would be trained on vast datasets of valid/invalid draw sequences to learn the *optimal policy* for generating a valid draw sequence, resulting in faster and more flexible solution generation compared to brute-force searching.

### 2. Architectural Upgrade: Implementation of Agentic AI

* **Multi-Agent System:** Develop a multi-agent framework where specialized AI agents collaborate:
    * **Planning Agent:** Generates a strategic draw plan based on rules (`confederation_rules.json`).
    * **Execution Agent:** Interfaces with the new Gen AI Draw Model to run the draw.
    * **Reflection Agent:** Analyzes failed attempts and provides root-cause feedback to the Planning Agent for self-correction and strategy refinement.

### 3. Deployment & User Experience Upgrades

* **Embedded App Design:** Migrate from the Streamlit web app to a **native application** with an optimized backend (e.g., FastAPI) to support self-contained, low-latency deployment on dedicated hardware for the live event.
* **Real-Time Visualization:** Implement dynamic visualization where teams are drawn one by one, with **real-time constraint highlighting** (e.g., groups temporarily turning red to indicate ineligibility) to provide full transparency into the AI's decision-making process.

### 4. Data & Integration Upgrades

* **Automated Data Pipeline:** Implement a system to automatically ingest and update critical data, such as the latest **FIFA Men's World Ranking** and **qualification statuses** (e.g., from external APIs), ensuring `pots.json` and `confirmed_teams.json` are always current without manual intervention.
* **API Integration:** Create external APIs for the final draw results, allowing easy, real-time integration with downstream systems like official broadcasting graphics and match scheduling software.


# Deployment

https://ai-draw-for-fifa-world-cup-2026-5tthrjt7lufkz9pqbixhsz.streamlit.app/
