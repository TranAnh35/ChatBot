from fastapi import APIRouter, UploadFile, File, HTTPException
from services.file.storage import FileStorage
from services.file.async_reader import AsyncFileReader
from services.vector_db.service import VectorDB
from urllib.parse import unquote
from typing import Dict, Any, List

router = APIRouter()
vector_db = VectorDB()
file_storage = FileStorage()
async_file_reader = AsyncFileReader()

@router.post("/upload", response_model=Dict[str, Any])
async def upload_file(file: UploadFile = File(...)):
    """Tải lên một file mới.
    
    Agrs:
        file (UploadFile): File được tải lên từ client.
        
    Returns:
        dict: Thông báo thành công và đường dẫn file nếu thành công,
                      hoặc thông báo lỗi nếu có lỗi xảy ra.
    """
    try:
        file_path = file_storage.save_file(file)
        return {"message": "Tải file lên thành công", "file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi tải file lên: {str(e)}")

@router.get("/files", response_model=Dict[str, List[Dict[str, Any]]])
async def get_files():
    """Lấy danh sách tất cả các file đã tải lên.
    
    Returns:
        dict: Danh sách các file đã tải lên.
    """
    return {"files": file_storage.list_files()}

@router.delete("/delete/{file_name}", response_model=Dict[str, str])
async def delete_uploaded_file(file_name: str):
    """Xóa một file đã tải lên.
    
    Agrs:
        file_name (str): Tên file cần xóa (được mã hóa URL).
        
    Returns:
        dict: Thông báo kết quả xóa file.
    Raises:
        HTTPException: 404 nếu không tìm thấy file.
    """
    decoded_filename = unquote(file_name)
    
    # Xóa file khỏi hệ thống
    if file_storage.delete_file(decoded_filename):
        # Xóa dữ liệu khỏi database
        vector_db.delete_file_from_db(decoded_filename)
        return {"message": "Đã xóa file thành công"}
    raise HTTPException(status_code=404, detail="Không tìm thấy file")

@router.post("/read", response_model=Dict[str, Any])
async def read_file(file: UploadFile = File(...)):
    """Đọc nội dung của file được tải lên.
    
    Agrs:
        file (UploadFile): File cần đọc nội dung.
        
    Returns:
        dict: Chứa tên file và nội dung của file.
        
    Excaption:
        HTTPException: Nếu có lỗi khi đọc file.
    """
    try:
        content = await async_file_reader.read_uploaded_file(file)
        return {"file_name": file.filename, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi đọc file: {str(e)}")