"""AWS Lambda Handler for Docling Document Processing & Extraction.

Runs inside an isolated AWS Lambda Container Function with 4GB-10GB RAM allocated.
Processes PDF, DOCX, Images, PPTX, and returns semantic Markdown + Chunks.
"""

import json
import base64
import os
import tempfile
from typing import Dict, Any

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling_core.transforms.chunker import HierarchicalChunker


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda invocation entrypoint."""
    try:
        # 1. Parse incoming payload
        payload = event
        if isinstance(event, dict) and "body" in event and isinstance(event["body"], str):
            try:
                payload = json.loads(event["body"])
            except Exception:
                payload = event

        file_b64 = payload.get("file_base64")
        if not file_b64:
            return {
                "statusCode": 400,
                "body": json.dumps({"status": "error", "message": "Missing 'file_base64' in payload."})
            }

        filename = payload.get("filename", "document.pdf")
        ext = os.path.splitext(filename)[1].lower() or ".pdf"

        # 2. Write file bytes to Lambda /tmp scratch storage
        file_bytes = base64.b64decode(file_b64)
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext, dir="/tmp") as tmp_file:
            tmp_file.write(file_bytes)
            tmp_path = tmp_file.name

        try:
            # 3. Configure Docling DocumentConverter
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = payload.get("do_ocr", False)
            pipeline_options.do_table_structure = True

            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )

            result = converter.convert(tmp_path)
            doc = result.document
            markdown_text = doc.export_to_markdown()

            # 4. Generate Hierarchical Chunks
            chunker = HierarchicalChunker(max_tokens=512, overlap_tokens=50)
            raw_chunks = list(chunker.chunk(doc))

            chunks = []
            for chunk in raw_chunks:
                heading = ""
                if hasattr(chunk, "heading") and chunk.heading:
                    heading = chunk.heading
                elif hasattr(chunk, "meta") and hasattr(chunk.meta, "headings") and chunk.meta.headings:
                    heading = " > ".join(chunk.meta.headings)

                page = getattr(chunk, "page_no", None)

                chunks.append({
                    "text": chunk.text,
                    "meta": {
                        "heading": heading or "General",
                        "page": page
                    }
                })

            response_data = {
                "status": "success",
                "markdown": markdown_text,
                "chunk_count": len(chunks),
                "chunks": chunks
            }

            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(response_data)
            }

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"status": "error", "message": str(e)})
        }
