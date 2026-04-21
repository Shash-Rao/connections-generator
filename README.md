# Connections Generator

This project is a generator for Connections-style puzzle games, featuring both a Python backend for generating puzzle boards and a React-based web interface for playing and testing the puzzles.

## Prerequisites

Before running this project, ensure you have the following installed on your system:

- **Python 3.8 or higher**: Download from [python.org](https://www.python.org/downloads/).
- **Node.js 16 or higher**: Download from [nodejs.org](https://nodejs.org/). This includes npm.
- **Git** (optional, for cloning if needed): Download from [git-scm.com](https://git-scm.com/).

## Installation

1. **Clone or Extract the Project**:
   - If you received this as a .zip file, extract it to a folder on your computer.
   - Open a terminal/command prompt and navigate to the project directory:
     ```
     cd path/to/connections-generator
     ```

2. **Install Python Dependencies**:
   - Run the following command to install required Python libraries:
     ```
     pip install -r requirements.txt
     ```
   - This will install: `gensim`, `nltk`, `wordfreq`.
   - Note: `nltk` may require additional data downloads. If prompted during runtime, follow the instructions to download necessary corpora.

3. **Install Node.js Dependencies**:
   - Run the following command to install required Node.js packages:
     ```
     npm install
     ```
   - This will install: React, Vite, ESLint, and related development tools.

## Running the Project

### Generating Puzzle Boards (Python Backend)

To generate new puzzle boards using the Python scripts:

1. Navigate to the project directory in your terminal.
2. Run the main generator script:
   ```
   python main.py
   ```
   - This will generate puzzle boards based on the configured generators (semantic, anagram, synonym, etc.).
   - Generated boards are saved to `boards.json` and categories are updated in the `categories/` folder.

You can also run specific generators or modify parameters in the Python files as needed.

### Running the Website (React Frontend)

To start the web interface for playing and testing puzzles:

1. Ensure you are in the project directory.
2. Start the development server:
   ```
   npm run dev
   ```
   - This will start Vite's development server.
   - Open your web browser and go to `http://localhost:5173` (or the URL shown in the terminal).
   - The website allows you to view and interact with generated puzzle boards.

## Project Structure

- `main.py`: Main Python script for generating puzzle boards.
- `board_generation.py`: Logic for creating complete game boards.
- `generators/`: Contains different generator classes (semantic, anagram, synonym, purple-level).
- `scoring/`: Scoring and difficulty assignment modules.
- `utils/`: Utility functions for filtering, embeddings, etc.
- `datasets/`: Data files used for generation (included in the project).
- `categories/`: JSON files containing generated puzzle categories.
- `src/`: React source code for the web interface.
- `public/`: Static assets for the web app.
- `requirements.txt`: Python dependencies.
- `package.json`: Node.js dependencies and scripts.

## Testing the Project

1. **Generate Boards**: Run `python main.py` to create new puzzle data.
2. **View on Website**: Start `npm run dev` and navigate to the local server to see the puzzles in action.
3. **Check Categories**: Look in the `categories/` folder for generated JSON files.
4. **Modify and Test**: Edit generator parameters or add new categories, then regenerate and test.

## Troubleshooting

- If `pip install` fails, try `pip3 install -r requirements.txt` or ensure Python is in your PATH.
- If `npm install` fails, clear npm cache with `npm cache clean --force` and try again.
- For Python import errors, ensure you're running from the project root directory.
- If the website doesn't load, check that port 5173 is available or modify `vite.config.js` if needed.

## Notes

- All datasets and pre-generated content are included in this submission.
- The project uses machine learning models (via gensim) for semantic analysis, so initial runs may take time to load models.
- For production deployment, use `npm run build` to create optimized assets.
