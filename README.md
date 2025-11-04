# OmniLearn Project - Podcast Generation Module

This repository contains the source code for the **Podcast Generation Module**, a core component of the larger **OmniLearn - Smart Multimodal Learning Platform** submitted to the UIT Data Science Challenge 2025.

This module specializes in converting educational text documents into engaging podcast audio files, supporting both **monologue (storytelling)** and **two-person dialogue (interview)** formats, driven by Large Language Models (LLM) and Text-to-Speech (TTS) technology.

***

## Context: Part of the OmniLearn Platform

The Podcast Module is essential for the OmniLearn platform's goal of enabling **multimodal learning**. It allows users to convert complex text topics into an auditory format, catering to diverse learning styles and improving memory retention. It is one of the key content generation modules alongside Video and Storytelling.

***

## Core Technology & Architecture

The podcast generation pipeline is a specialized RAG-based application, transforming retrieved content (Combined Input: Instruction, Query, and Context) into a multi-format output.

**The Podcast Generation Flow**

| Step | Component | Technology Used | Key Functionality |
| :--- | :--- | :--- | :--- |
| **1. Input** | `Combined Input` | RAG Context + `PodcastConfig` | Provides source text and configuration: **Duration**, **Style**, and **Characters** (1 or 2). |
| **2. Script Generation** | `LLM Component` | **Gemini 2.0 Flash** | Converts text into a podcast transcript using **Chunking Logic** (2,000–2,600 tokens) and a **Sliding Window** prompt design to maintain context continuity. |
| **3. Audio Synthesis** | `TTS Component` | **Gemini 2.5 Flash Preview TTS** | Transforms the script into audio. Supports **Single-voice** (Storytelling - e.g., Zephyr) or **Multi-voice** (Interview - e.g., Zephyr/Puck) by mapping `Speaker X:` labels to distinct voices. |
| **4. Post-Processing** | `tts_core` + `pydub` | **`pydub` / FFmpeg** | Merges audio chunks, synchronizes with the transcript, and exports the final output as **`.wav`** (quality) and **`.mp3`** (sharing). |

***

## Project Structure and File Roles

The module is organized using a clear hierarchy, separating core services from high-level business logic.

```plain text
podcast/

├─ models/
│  ├─ storytelling_model.py : StorytellingModel (Characters=1)
│  └─ interview_model.py : InterviewModel (Characters=2)
│
├─ core/
│  ├─ llm_core.py : GeminiLLM + ContentGenerator (LLM services)
│  └─ tts_core.py : TTS (Gemini TTS) and Audio Post-processing (pydub)
│
├─ orchestrator.py : Central router/manager
├─ requirements.txt
└─ main.py : Execution entry point
```
| File | Description | Core Function |
| :--- | :--- | :--- |
| `core/llm_core.py` | Handles **Gemini LLM API** communication, API key management, and implements the **ContentGenerator** with logic for **chunking** and context continuity for long documents. | **Script Generation** |
| `core/tts_core.py` | Handles **Gemini TTS API** calls, **rate limiting**, and implements the audio processing workflow (WAV chunking, merging, MP3 export) using `pydub`. | **Audio Synthesis** |
| `models/storytelling_model.py` | Defines the process for **Monologue** podcasts. Calls `ContentGenerator` with `characters=1` and uses single-voice synthesis. | **Monologue Logic** |
| `models/interview_model.py` | Defines the process for **Dialogue** podcasts. Calls `ContentGenerator` with `characters=2` and uses multi-speaker synthesis. | **Dialogue Logic** |
| `orchestrator.py` | The main router. It initializes the core components and selects the appropriate model (`StorytellingModel` or `InterviewModel`) based on the input `characters` configuration. | **Flow Control** |

***

## Setup and Execution

### 1. Prerequisites

You must install **FFmpeg** on your operating system, as it is required by the `pydub` library for all audio post-processing tasks.

* **Linux (Debian/Ubuntu):** `sudo apt update && sudo apt install ffmpeg`
* **macOS (Homebrew):** `brew install ffmpeg`

### 2. Installation

Install the required Python libraries using the provided `requirements.txt`:

```bash
pip install -r requirements.txt
```
### 3. API Key Configuration

You need a Gemini API Key. Set it as an environment variable:

```bash
# Replace YOUR_API_KEY with your actual Gemini API key
export GEMINI_API_KEY="YOUR_API_KEY"
```

### 4. Running the Module

The `main.py` script requires an input document (`input.txt`) and reads its configuration from environment variables.

#### A. Input File

Create a file named `input.txt` in the root directory with the source text you want to convert.

#### B. Configuration

Control the generation mode using these environment variables (defaults to Monologue mode):

| Variable | Description | Default Value | Example for Dialogue Mode |
| :--- | :--- | :--- | :--- |
| `CFG_DURATION` | Target length (e.g., "5 minutes"). | "ngắn (2-3 phút)" | `"5 phút"` |
| `CFG_STYLE` | Writing style (e.g., "academic," "friendly"). | "học thuật" | `"thân mật dễ hiểu"` |
| `CFG_CHARACTERS` | **1** for Monologue / **2** for Dialogue. | **1** | **`2`** |

#### C. Execute

Run the main script. The output files (`.wav` and `.mp3`) will be saved in the root directory.

**Example Run (Monologue - Default Mode):**

```bash
python main.py
```

**Example Run (Dialogue - Interview Mode):**

```bash
export CFG_CHARACTERS="2"
# Run with two-character configuration
python main.py
```
