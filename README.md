# OmniLearn Project - Podcast Generation Module

This repository contains the source code for the **Podcast Generation Module**, a core component of the larger **OmniLearn - Smart Multimodal Learning Platform** submitted to the UIT Data Science Challenge 2025.

This module specializes in converting educational text documents into engaging podcast audio files, supporting both **monologue (storytelling)** and **two-person dialogue (interview)** formats, driven by Large Language Models (LLM) and Text-to-Speech (TTS) technology.

***

## Context: Part of the OmniLearn Platform

The Podcast Module is essential for the OmniLearn platform's goal of enabling **multimodal learning**[cite: 227]. [cite_start]It allows users to convert complex text topics into an auditory format, catering to diverse learning styles and improving memory retention[cite: 232, 239]. [cite_start]It is one of the key content generation modules alongside Video and Storytelling[cite: 230].

***

## ⚙️ Core Technology & Architecture

[cite_start]The podcast generation pipeline is a specialized RAG-based application, transforming retrieved context into a multi-format output[cite: 231, 232].

### 1. The Podcast Generation Flow

| Step | Component | Technology Used | Key Functionality |
| :--- | :--- | :--- | :--- |
| **1. Input** | `Combined Input` | RAG Context + `PodcastConfig` | [cite_start]Provides source text and configuration: **Duration**, **Style**, and **Characters** (1 or 2)[cite: 236, 237, 238, 239]. |
| **2. Script Generation** | `LLM Component` | [cite_start]**Gemini 2.0 Flash** [cite: 241, 250] | [cite_start]Converts text into a podcast transcript using **Chunking Logic** (2,000–2,600 tokens) and a **Sliding Window** prompt design to maintain context continuity[cite: 243, 245]. |
| **3. Audio Synthesis** | `TTS Component` | [cite_start]**Gemini 2.5 Flash Preview TTS** [cite: 252] | Transforms the script into audio. [cite_start]Supports **Single-voice** (Storytelling - e.g., Zephyr) or **Multi-voice** (Interview - e.g., Zephyr/Puck) by mapping `Speaker X:` labels to distinct voices[cite: 254, 255, 256]. |
| **4. Post-Processing** | `tts_core` + `pydub` | **`pydub` / FFmpeg** | [cite_start]Merges audio chunks, synchronizes with the transcript, and exports the final output as **`.wav`** (quality) and **`.mp3`** (sharing)[cite: 257, 258, 259, 260]. |

***

## 📂 Project Structure and File Roles

The module is organized using a clear hierarchy, separating core services from high-level business logic.
