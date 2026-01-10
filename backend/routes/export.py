from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse,JSONResponse
from utils.database import get_summary_by_id, get_book_by_id
from backend.exporters.export_utils import format_summary_txt,create_temp_file,cleanup_temp_file
from backend.exporters.pdf_exporter import export_summary_pdf
from datetime import datetime
import tempfile
import os

router = APIRouter(prefix="/api/export")

@router.get("/summary/{summary_id}")
async def export_summary(
    summary_id : str,
    format : str = "txt",
    include_original = bool = False

):
    """
    Export summary in specified format
    
    Args:
        summary_id: ID of the summary to export
        format: Export format (txt, pdf, json)
        include_original: Whether to include original text
    """
    try:
        #Get summary data
        summary = get_summary_by_id(summary_id)
        if not summary:
            raise HTTPException(status_code=404,detail="summary not found")
        book = get_book_by_id(summary.get('book_id'))
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        #prepare data
        summary_data = {
            "summary_text":summary.get("summary_text",""),
            "book_info":{
                "title":book.get("title","Unknown"),
                "author":book.get("author","Unknown"),
                "date":datetime.utcnow().strftime('%d %B %Y')
            }
        }

        if include_original:
            summary_data["original_text"] = book.get("raw_text","")

        if format.lower() == "txt":
            content = format_summary_txt(summary_data,include_original)
            temp_path = create_temp_file(content, ".txt")
            return FileResponse(
                temp_path,
                filename=f"summary_{book.get('title','book').replace('',"_")}.txt",
                media_type="text/plain"

            )    
        elif format.lower() == "pdf":
            pdf_data = {
                "title": book.get("title", "Unknown"),
                "author": book.get("author", "Unknown"),
                "date": datetime.utcnow().strftime('%d %B %Y'),
                "summary_text": summary.get("summary_text", ""),
                "original_text": book.get("raw_text", "") if include_original else None
            }
            temp_path = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
            export_summary_pdf(pdf_data, temp_path, include_original)
            
            return FileResponse(
                temp_path,
                filename=f"summary_{book.get('title', 'book').replace(' ', '_')}.pdf",
                media_type="application/pdf"
            )
        elif format.lower() == "json":
            # Return as JSON
            return JSONResponse(content={
                "success": True,
                "data": {
                    "summary": summary_data["summary_text"],
                    "book_info": summary_data["book_info"],
                    "original_text": summary_data.get("original_text", ""),
                    "exported_at": datetime.utcnow().isoformat()
                }
            })
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use txt, pdf, or json")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
@router.get("/clipboard/{summary_id}")
async def get_summary_for_clipboard(summary_id:str):
    try:
        summary = get_book_by_id(summary_id)
        if not summary:
           raise HTTPException(status_code=404,detail="summary not found")
        book = get_book_by_id(summary.get("book_id"))
        
        return JSONResponse(content={
            "success": True,
            "text": summary.get("summary_text", ""),
            "title": book.get("title", "") if book else "Unknown"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")

