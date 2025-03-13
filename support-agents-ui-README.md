# Support Case Handling System - Streamlit UI

This project provides a web-based user interface for the Support Case Handling Agent System using Streamlit. It allows users to submit support cases and visualize the interaction between different specialized agents.

## Features

- **Interactive Web Interface**: Submit support cases through a user-friendly web interface
- **Agent Interaction Visualization**: See how different agents (Support Engineer, Service Engineer, Product Engineer) interact to solve your case
- **Ticket Tracking**: View any tickets created during the case handling process
- **Real-time Processing**: Watch as your case is processed in real-time

## System Architecture

The system consists of two main components:

1. **Support Agents Module** (`support_agents.py`): Contains the core functionality of the agent system
2. **Streamlit UI** (`support-agents-ui.py`): Provides the web interface for interacting with the agent system

## Prerequisites

- Python 3.8 or higher
- OpenAI Agents SDK
- Streamlit
- Graphviz (both the Python package and the system-level software)

## Installation

1. Install the system-level Graphviz software:
   - On macOS: `brew install graphviz`
   - On Ubuntu/Debian: `sudo apt-get install graphviz`
   - On Windows: Download and install from [Graphviz's official website](https://graphviz.org/download/)

2. Install the required Python dependencies using the provided requirements.txt file:

```bash
pip install -r requirements.txt
```

2. Make sure you have the following files in your project directory:
   - `support_agents.py`
   - `support-agents-ui.py`

## Usage

1. Run the Streamlit application:

```bash
streamlit run support-agents-ui.py
```

2. Open your web browser and navigate to the URL displayed in the terminal (typically http://localhost:8501)

3. Use the interface to:
   - Select a product from the dropdown menu
   - Enter your case description in the text area
   - Click "Submit Case" to process your request
   - View the response, agent interaction flow, and any created tickets

## How It Works

1. **User Input**: You select a product and describe your issue
2. **Case Processing**: The system creates a unique case ID and processes your request
3. **Agent Interaction**: 
   - The Support Engineer agent initially handles your case
   - If needed, it consults with specialized agents (Service Engineer or Product Development Engineer)
   - The Product Engineer determines if issues are bugs, documentation problems, or user errors
4. **Result Display**:
   - The final solution is displayed
   - A visualization shows the interaction between agents
   - Any created tickets (bug reports or documentation requests) are shown

## Example Use Cases

- **API Connection Issues**: Problems connecting to the API Gateway
- **Data Synchronization Errors**: Issues with the Data Synchronizer
- **UI Problems**: Issues with the Web Dashboard interface

## Troubleshooting

- If you encounter import errors, ensure that both `support_agents.py` and `support-agents-ui.py` are in the same directory
- If the graph visualization doesn't appear, make sure Graphviz is properly installed
- If the application seems slow, be patient as the agent processing may take some time depending on the complexity of the case

## Customization

You can customize the system by:
- Adding more products to the knowledge base in `support_agents.py`
- Modifying the agent instructions to handle different types of cases
- Extending the UI with additional Streamlit components
