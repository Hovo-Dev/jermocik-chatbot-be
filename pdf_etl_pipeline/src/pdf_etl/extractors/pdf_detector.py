"""PDF document detection and layout analysis using LayoutParser + Detectron2."""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from pdf2image import convert_from_path, pdfinfo_from_path
from PIL import Image
import layoutparser as lp

from ..utils.pdf_utils import has_visual_content


class PDFDetector:
    """Detect and analyze PDF documents for visual content using LayoutParser."""
    
    def __init__(self, logger: logging.Logger, score_thresh: float = 0.2, min_area: int = 5000):
        self.logger = logger
        self.score_thresh = score_thresh
        self.min_area = min_area
        self.model = self._load_layout_model()
    
    def _load_layout_model(self):
        """Load a Detectron2 layout detection model that identifies Figures, Tables, etc."""
        self.logger.info("Loading LayoutParser Detectron2 model...")
        model = lp.models.Detectron2LayoutModel(
            config_path="lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config",
            label_map={
                0: "Text",
                1: "Title", 
                2: "List",
                3: "Table",
                4: "Figure"
            },
            extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", self.score_thresh]
        )
        self.logger.info("LayoutParser model loaded successfully")
        return model
    
    def _pdf_page_to_image(self, pdf_path: Path, page_number: int, dpi: int = 300):
        """Convert a specific page (0-indexed) of a PDF into a PIL Image."""
        pages = convert_from_path(
            pdf_path,
            dpi=dpi,
            first_page=page_number + 1,
            last_page=page_number + 1
        )
        if not pages:
            raise ValueError(f"PDF page {page_number} not found or conversion failed: {pdf_path}")
        return pages[0]
    
    def analyze_pdf(self, pdf_path: Path, dpi: int = 300) -> Dict[str, Any]:
        """Analyze PDF using LayoutParser and return structure with pages containing visual content."""
        self.logger.info(f"Analyzing PDF with LayoutParser: {pdf_path}")
        
        try:
            # Get number of pages
            info = pdfinfo_from_path(pdf_path)
            num_pages = info.get("Pages", None)
            if num_pages is None:
                raise RuntimeError(f"Could not get number of pages for PDF: {pdf_path}")
            
            pdf_data = {
                "pdf_path": str(pdf_path),
                "num_pages": num_pages,
                "pages": []
            }
            
            pages_with_content = 0
            for page_idx in range(num_pages):
                self.logger.info(f"  Processing page {page_idx + 1}/{num_pages} of {pdf_path.name}")
                page_data = self._analyze_page(pdf_path, page_idx, dpi)
                
                # Only include pages with visual content
                if has_visual_content(page_data):
                    pdf_data["pages"].append(page_data)
                    pages_with_content += 1
                else:
                    self.logger.debug(f"    Page {page_idx} has no tables/figures, skipping")
            
            self.logger.info(f"Found {pages_with_content}/{num_pages} pages with visual content")
            return pdf_data
            
        except Exception as e:
            self.logger.error(f"Failed to analyze PDF {pdf_path}: {e}")
            return {
                "pdf_path": str(pdf_path),
                "num_pages": 0,
                "pages": [],
                "error": str(e)
            }
    
    def _analyze_page(self, pdf_path: Path, page_idx: int, dpi: int) -> Dict[str, Any]:
        """Analyze a single page using LayoutParser detection."""
        page_entry = {
            "page_number": page_idx,
            "tables": [],
            "figures": [],
            "texts": []
        }
        
        try:
            # Rasterize page
            page_image = self._pdf_page_to_image(pdf_path, page_idx, dpi=dpi)
        except Exception as e:
            self.logger.error(f"    Error rasterizing page {page_idx}: {e}")
            return page_entry
        
        if page_image.mode != "RGB":
            page_image = page_image.convert("RGB")
        
        # Detect layout using LayoutParser
        layout = self.model.detect(page_image)
        
        for block in layout:
            x1, y1, x2, y2 = block.block.x_1, block.block.y_1, block.block.x_2, block.block.y_2
            width = x2 - x1
            height = y2 - y1
            area = width * height
            
            if area < self.min_area:
                continue
            
            record = {
                "bbox": [int(x1), int(y1), int(x2), int(y2)],
                "type": block.type,
                "score": float(block.score)
            }
            
            if block.type == "Table":
                page_entry["tables"].append(record)
            elif block.type == "Figure":
                page_entry["figures"].append(record)
            # Ignore other types (Text, Title, List)
        
        return page_entry