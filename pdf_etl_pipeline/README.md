# PDF ETL Pipeline

A clean, modular ETL pipeline that extracts structured data from PDF documents using Vision Language Models (VLM).

## Features

- **Automatic PDF Discovery**: Scans input directory for PDF files
- **Smart Content Detection**: Identifies pages with tables and charts
- **VLM-Powered Extraction**: Uses GPT-4V to extract structured data
- **Clean JSON Output**: Produces a structured manifest with table data and chart descriptions
- **Modular Architecture**: Cleanly separated utilities, extractors, and processors

## Quick Start

1. **Setup Environment**
   ```bash
   # Create .env file with your API key
   echo "OPENAI_API_KEY=your_key_here" > .env
   
   # Install dependencies
   pip install openai python-dotenv PyMuPDF tenacity pydantic orjson
   ```

2. **Run Pipeline**
   ```bash
   # Basic usage - input from data/input, output to data/output
   python main.py
   
   # Custom directories
   python main.py --input ./my_pdfs --output ./results
   
   # Different model
   python main.py --model gpt-4o-mini
   ```

3. **Check Results**
   - Main output: `data/output/manifest.json`
   - Logs: `data/output/pipeline.log`

## Project Structure

```
pdf_etl_pipeline/
├── src/pdf_etl/
│   ├── extractors/          # Data extraction modules
│   │   ├── pdf_detector.py  # PDF analysis and layout detection
│   │   └── vlm_extractor.py # VLM-based content extraction
│   ├── processors/          # Pipeline orchestration
│   │   └── pipeline.py      # Main ETL pipeline
│   └── utils/               # Utility functions
│       ├── pdf_utils.py     # PDF operations
│       ├── file_utils.py    # File system operations
│       └── logging_utils.py # Logging setup
├── config/
│   └── settings.py          # Configuration management
├── data/
│   ├── input/              # Place PDF files here
│   └── output/             # Pipeline results
└── main.py                 # Entry point
```

## Output Format

The pipeline produces a `manifest.json` with this structure:

```json
{
  "pages": [
    {
      "path": "/path/to/document.pdf",
      "page": 5,
      "chart_descriptions": [
        {
          "title": "Revenue Growth",
          "summary": "Quarterly revenue showing 15% growth...",
          "key_points": ["Q1 up 15%", "Strong cloud growth"]
        }
      ],
      "table_data": [
        {
          "title": "Financial Results",
          "notes": "All figures in millions USD",
          "columns": [
            {"name": "Quarter", "values": ["Q1", "Q2", "Q3"]},
            {"name": "Revenue", "values": [100, 120, 135]}
          ]
        }
      ]
    }
  ]
}
```

## Configuration

Set environment variables in `.env` file:

```bash
OPENAI_API_KEY=your_key_here
VLM_MODEL=gpt-4o
DPI=200
LOG_LEVEL=INFO
```

## Command Line Options

```bash
python main.py --help
```

- `--input` / `-i`: Input directory with PDF files
- `--output` / `-o`: Output directory for results  
- `--model` / `-m`: VLM model (gpt-4o, gpt-4o-mini)
- `--dpi`: Image resolution for page rendering
- `--log-level`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)