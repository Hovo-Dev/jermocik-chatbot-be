#!/usr/bin/env python3
"""
PDF ETL Pipeline - Main Entry Point

Extracts structured data from PDF documents using VLM analysis.
Input: Directory containing PDF files
Output: JSON manifest with tables and chart descriptions
"""

import argparse
import sys
from pathlib import Path

from src.pdf_etl.processors.pipeline import PDFETLPipeline
from config.settings import settings


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract structured data from PDF documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --input ./pdfs --output ./results
  python main.py --input ./pdfs --output ./results --model gpt-4o-mini
  python main.py --help
        """
    )
    
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=settings.DEFAULT_INPUT_DIR,
        help=f"Input directory containing PDF files (default: {settings.DEFAULT_INPUT_DIR})"
    )
    
    parser.add_argument(
        "--output", "-o", 
        type=Path,
        default=settings.DEFAULT_OUTPUT_DIR,
        help=f"Output directory for results (default: {settings.DEFAULT_OUTPUT_DIR})"
    )
    
    
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=settings.VLM_MODEL,
        help=f"VLM model to use (default: {settings.VLM_MODEL})"
    )
    
    parser.add_argument(
        "--dpi",
        type=int,
        default=settings.DPI,
        help=f"Image DPI for page rendering (default: {settings.DPI})"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default=settings.LOG_LEVEL,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help=f"Logging level (default: {settings.LOG_LEVEL})"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Validate settings
    try:
        settings.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    
    # Validate input directory
    if not args.input.exists():
        print(f"Error: Input directory does not exist: {args.input}")
        sys.exit(1)
    
    # Run pipeline
    pipeline = PDFETLPipeline(
        input_dir=args.input,
        output_dir=args.output,
        vlm_model=args.model,
        dpi=args.dpi,
        log_level=args.log_level
    )
    
    try:
        manifest_path = pipeline.run()
        print(f"✅ Pipeline completed successfully!")
        print(f"📄 Manifest: {manifest_path}")
        print(f"📁 Output directory: {args.output}")
        
    except KeyboardInterrupt:
        print("\\n❌ Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()