# WebAutomater (Scraper V2)

**WebAutomater** is a "Programming by Demonstration" (PBD) web automation platform that allows users to create, modify, and execute web scraping workflows using natural language. It combines a visual interface with an AI-powered backend to make web automation accessible to everyone.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![React](https://img.shields.io/badge/react-18-blue.svg)

## 🚀 Key Features

*   **Visual Recording**: Simply interact with a website to record your workflow steps (clicks, inputs, dropdowns).
*   **AI-Powered Modification**: Use natural language prompts (e.g., "Repeat this 5 times", "Change selector to X") to modify complex workflows instantly.
*   **Smart Execution**: Robust playback engine that handles popups, multiple tabs, and iframes automatically.
*   **Visual Workflow Editor**: Inspect and edit your workflow graph with a drag-and-drop interface (React Flow).
*   **Popup & Frame Support**: Seamlessly records and executes actions across new windows and nested iframes.

## 🛠️ Architecture

### Backend (Python/FastAPI)
*   **FastAPI**: High-performance API server.
*   **Playwright**: Core engine for browser automation (recording and execution).
*   **Ollama (Llama 3.1)**: Local LLM integration for interpreting natural language modification requests.
*   **Context-Aware Recorder**: Injects JavaScript to capture events across main pages and popups.

### Frontend (React/Vite)
*   **React Flow**: Visualization of the workflow graph.
*   **Tailwind CSS**: Modern, responsive UI styling.
*   **Axios**: API communication.

## 📦 Installation

### Prerequisites
*   Python 3.9+
*   Node.js 16+
*   Ollama (running locally with `llama3.1` model)

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Frontend Setup
```bash
cd frontend
npm install
```

## ▶️ Usage

1.  **Start the Backend**:
    ```bash
    cd backend
    uvicorn main:app --reload --port 8002
    ```

2.  **Start the Frontend**:
    ```bash
    cd frontend
    npm run dev
    ```

3.  **Open the App**: Go to `http://localhost:5173` (or the port shown in your terminal).

4.  **Create a Workflow**:
    *   Enter a URL and click **Start Recording**.
    *   Interact with the browser window that appears.
    *   Click **Stop Recording**.
    *   *Alternatively*, use the **+ Add Step** button to build manually.

5.  **Modify with AI**:
    *   Type a command like "Wrap steps 1-3 in a loop 5 times" in the chat.
    *   Watch the graph update automatically.

6.  **Run**: Click **Run Workflow** to execute the automation.

## 🤝 Contributing
Contributions are welcome! Please open an issue or submit a pull request.

## 📄 License
MIT License
