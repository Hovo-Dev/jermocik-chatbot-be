"""VLM-based content extraction from PDF pages."""

import json
import logging
import os
from typing import Dict, Any

from dotenv import load_dotenv
from openai import OpenAI
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type

from ..utils.pdf_utils import b64_png_bytes


class VLMExtractor:
    """Extract structured content from PDF pages using Vision Language Models."""
    
    def __init__(self, model: str, logger: logging.Logger):
        load_dotenv()
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model = model
        self.logger = logger
    
    @retry(
        wait=wait_random_exponential(multiplier=1, max=60),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def extract_content(self, page_image: bytes, page_text: str) -> Dict[str, Any]:
        """Extract tables and figures from page image."""
        image_data_url = b64_png_bytes(page_image)
        
        instructions = self._build_extraction_prompt()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": instructions},
                        {"type": "text", "text": f"PAGE_TEXT:\\n{page_text.strip()[:15000]}"},
                        {"type": "image_url", "image_url": {"url": image_data_url}},
                    ]
                }],
                response_format={"type": "json_object"}
            )
            self.logger.info("VLM extraction successful")
            
            content = response.choices[0].message.content
            if not content:
                raise RuntimeError("Empty response from VLM")
            
            result = json.loads(content)
            
            # Ensure required keys exist
            result.setdefault("tables", [])
            result.setdefault("figures", [])
            
            return result
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
            return {"tables": [], "figures": [], "page_summary": None}
        except Exception as e:
            self.logger.error(f"VLM extraction failed: {e}")
            return {"tables": [], "figures": [], "page_summary": None}
    
    def _build_extraction_prompt(self) -> str:
        """Build the extraction prompt for the VLM."""
        return """You are an expert financial document analyst.

Task:
• Find ALL tables and charts on this full PDF page image.
• For tables: output JSON with `columns` as a list of objects with 'name' and 'values' fields.
  Normalize numbers (no thousands separators), keep signs; allow units/% as strings if present.
  Use null for empty cells; include `title` and `notes` (footnotes/units) when visible.
• For charts/figures: provide a short `summary` and 3–10 `key_points` with concrete metrics when visible.
• For charts/figures: make sure that the key_points contain all the exact values visible in the chart.
• Use the provided page text as context to disambiguate headers/abbreviations — do not invent data.
• If none present, return empty arrays.

Return JSON in this exact format:
{
  "tables": [{"title": "...", "notes": "...", "columns": [{"name": "col1", "values": [...]}]}],
  "figures": [{"title": "...", "summary": "...", "key_points": [...]}],
  "page_summary": "..."
}"""