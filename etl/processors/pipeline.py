"""Main ETL pipeline orchestrator."""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import fitz

from etl.extractors.pdf_detector import PDFDetector
from etl.extractors.vlm_extractor import VLMExtractor
from etl.utils.pdf_utils import discover_pdfs, page_to_png_bytes, extract_page_text, has_visual_content
from etl.utils.file_utils import ensure_dir, save_json
from etl.utils.logging_utils import setup_logger
from rag.rag_engine import RAGEngine
from rag.models import DocumentChunk
from django.conf import settings

class ETLPipeline:
    """Main ETL pipeline for processing PDF documents to structured JSON."""
    
    def __init__(
        self,
        input_dir: Path,
        output_dir: Path,
        vlm_model: str = settings.VLM_MODEL,
        dpi: int = settings.DPI,
        log_level: str = "INFO"
    ):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.vlm_model = vlm_model
        self.dpi = dpi
        
        # Setup logging
        ensure_dir(self.output_dir)
        self.logger = setup_logger("pdf_etl", self.output_dir, log_level)
        
        # Initialize components
        self.pdf_detector = PDFDetector(self.logger)
        self.vlm_extractor = VLMExtractor(vlm_model, self.logger)
        self.rag_engine = RAGEngine()
    
    def run(self) -> Path:
        """Execute the complete ETL pipeline."""
        self.logger.info("Starting PDF ETL Pipeline")
        self.logger.info(f"Input: {self.input_dir}")
        self.logger.info(f"Output: {self.output_dir}")
        
        # Discover PDFs and process them directly
        pdf_files = self._discover_pdfs()
        if not pdf_files:
            self.logger.warning("No PDF files found")
            return self.output_dir / "manifest.json"
        
        manifest = self._process_pdfs_with_detection(pdf_files)
        self.logger.debug(manifest)
        # Save final manifest
        manifest_path = self.output_dir / "manifest.json"
        csv_save_folder = self.output_dir / "csv"
        ensure_dir(csv_save_folder)

        for idx, page in enumerate(manifest.get("pages", [])):
            table_data = page.get("table_data")
            if not table_data:  # Handle None or empty table_data
                continue
                
            for jdx, table in enumerate(table_data):
                try:
                    columns = table.get("columns", [])
                    if not columns:
                        self.logger.warning(f"Skipping table with no columns: page {idx+1}, table {jdx+1}")
                        continue
                    
                    # Create DataFrame from columns
                    df_dict = {}
                    for col in columns:
                        col_name = col.get("name", f"Column_{len(df_dict)}")
                        col_values = col.get("values", [])
                        df_dict[col_name] = col_values
                    
                    df = pd.DataFrame.from_dict(df_dict, orient='index').transpose()
                    
                    # Generate filename with table title
                    table_title = table.get("title", f"table_{jdx+1}")
                    safe_title = "".join(c if c.isalnum() or c in '._-' else '_' for c in table_title)[:50]
                    output_path = csv_save_folder / f"page_{idx+1}_table_{jdx+1}_{safe_title}.csv"
                    
                    df.to_csv(output_path, index=False)
                    self.logger.info(f"Saved table CSV: {output_path} ({len(df)} rows x {len(df.columns)} cols)")
                    
                except Exception as e:
                    self.logger.error(f"Failed to convert table to CSV: page {idx+1}, table {jdx+1}: {e}")

        # Save manifest for debug only
        save_json(manifest, manifest_path)

        self.logger.info(f"Pipeline completed. Manifest: {manifest_path}")

        return manifest_path

    def _discover_pdfs(self) -> List[Path]:
        """Discover all PDF files in input directory."""
        self.logger.info("Discovering PDF files...")
        pdf_files = discover_pdfs(self.input_dir)
        self.logger.info(f"Found {len(pdf_files)} PDF files")
        return pdf_files
    
    def _process_pdfs_with_detection(self, pdf_files: List[Path]) -> Dict[str, Any]:
        """Process PDFs using LayoutParser detection, only VLM process pages with tables/figures."""
        manifest = {"pages": []}
        
        for pdf_path in pdf_files:
            self.logger.info(f"Processing PDF: {pdf_path.name}")
            
            # Analyze PDF structure using LayoutParser
            pdf_analysis = self.pdf_detector.analyze_pdf(pdf_path)
            
            if "error" in pdf_analysis:
                self.logger.warning(f"Skipping PDF with error: {pdf_path}")
                continue

            # Only process pages that were detected to have tables/figures
            try:
                doc = fitz.open(pdf_path)

                for page_entry in pdf_analysis.get("pages", []):
                    page_data = self._process_page_with_vlm(doc, pdf_path, page_entry)

                    # Chart descriptions to ingest document
                    chart_descriptions = page_data['chart_descriptions']

                    chunks = []

                    if chart_descriptions:
                        # The main chart description
                        key_points = chart_descriptions.get('key_points', [])
                        summary = chart_descriptions.get('summary', "")

                        # Join chart descriptions into a single text chunk to consolidate into a single embedding
                        text_chunk = "\n".join(key_points)

                        embedding = self.rag_engine.create_embedding(text_chunk)

                        chunk = DocumentChunk(
                            content=text_chunk,
                            summary=summary,
                            embedding=embedding,
                        )
                        chunks.append(chunk)

                    # Save many chunks into DB
                    DocumentChunk.objects.bulk_create(chunks)

                    if page_data:
                        manifest["pages"].append(page_data)
                
                doc.close()
                
            except Exception as e:
                self.logger.error(f"Failed to process PDF {pdf_path}: {e}")
        
        return manifest
    
    def _process_page_with_vlm(self, doc: fitz.Document, pdf_path: Path, page_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single PDF page that was detected to have tables/figures."""
        page_num = page_entry["page_number"]
        
        self.logger.info(f"    VLM processing page {page_num} (detected: {len(page_entry.get('tables', []))} tables, {len(page_entry.get('figures', []))} figures)")
        
        try:
            # Extract page content
            page_image = page_to_png_bytes(doc, page_num, self.dpi)
            page_text = extract_page_text(doc, page_num)
            
            # VLM extraction
            extracted_content = self.vlm_extractor.extract_content(page_image, page_text)
            
            # Log extracted content
            self._log_extracted_content(page_num, extracted_content)
            
            # Build page data for manifest
            return {
                "path": str(pdf_path),
                "page": page_num,
                "chart_descriptions": self._format_figures(extracted_content.get("figures", [])),
                "table_data": self._format_tables(extracted_content.get("tables", []))
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process page {page_num} of {pdf_path}: {e}")
            return None
    
    
    def _format_figures(self, figures: List[Dict[str, Any]]) -> List[Dict[str, Any]] | None:
        """Format figure data for manifest."""
        if not figures:
            return None
        
        return [
            {
                "title": fig.get("title"),
                "summary": fig.get("summary", ""),
                "key_points": fig.get("key_points", [])
            }
            for fig in figures
        ]
    
    def _format_tables(self, tables: List[Dict[str, Any]]) -> List[Dict[str, Any]] | None:
        """Format table data for manifest."""
        if not tables:
            return None
        
        return [
            {
                "title": table.get("title"),
                "notes": table.get("notes"),
                "columns": table.get("columns", [])
            }
            for table in tables
        ]
    
    def _log_extracted_content(self, page_num: int, content: Dict[str, Any]) -> None:
        """Log extracted content for debugging."""
        tables = content.get("tables", [])
        figures = content.get("figures", [])
        
        self.logger.info(f"Page {page_num}: {len(tables)} table(s), {len(figures)} figure(s)")
        
        if tables:
            self.logger.info("Extracted tables:")
            self.logger.info(json.dumps(tables, indent=2))
        
        if figures:
            for i, fig in enumerate(figures):
                title = fig.get("title", "Untitled")
                summary = fig.get("summary", "")[:100] + "..." if len(fig.get("summary", "")) > 100 else fig.get("summary", "")
                self.logger.info(f"Figure {i}: {title} - {summary}")
