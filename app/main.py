from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from .storage import init_db, insert_upload, create_job, update_job_status, get_job, get_upload
from .schemas import UploadResponse, EvaluateResponse, JobResult
from .config import config
from .rag import index_namespace
from .evaluator import evaluate_cv, evaluate_project, overall_summary
from .parser import extract_job_desc_from_pdf
import os, json

app = FastAPI(title="CV Evaluator", version="1.0.0")
conn = init_db(config.db_path)

def load_seed():
    jd_text = extract_job_desc_from_pdf("data/jobdesc.pdf")
    jd_chunks = [(f"jd_{i}", chunk) for i, chunk in enumerate(jd_text.split("\n\n")) if chunk.strip()]
    index_namespace(conn, "job:cv", jd_chunks)

    with open("data/rubric.yaml", "r") as f:
        rubric = f.read().strip()
    rubric_chunks = [(f"rubric_{i}", chunk) for i, chunk in enumerate(rubric.split("\n\n")) if chunk.strip()]
    index_namespace(conn, "rubric:cv", rubric_chunks)
    index_namespace(conn, "rubric:project", rubric_chunks)

load_seed()

@app.post("/upload", response_model=UploadResponse)
async def upload_files(cv: UploadFile = File(...), project: UploadFile = File(...)):
    if cv.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        raise HTTPException(status_code=400, detail="CV must be a PDF or DOCX file.")
    if project.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        raise HTTPException(status_code=400, detail="Project must be a PDF or DOCX file.")
    
    cv_data = await cv.read()
    project_data = await project.read()
    
    from .parser import normalize_pair
    cv_filename = cv.filename if cv.filename is not None else "cv_file"
    project_filename = project.filename if project.filename is not None else "project_file"
    cv_text, project_text = normalize_pair((cv_filename, cv_data), (project_filename, project_data))
    
    if not cv_text:
        raise HTTPException(status_code=400, detail="Failed to extract text from CV.")
    if not project_text:
        raise HTTPException(status_code=400, detail="Failed to extract text from Project.")
    
    upload_id = insert_upload(conn, cv_text, project_text)
    
    return UploadResponse(upload_id=upload_id)

@app.post("/evaluate", response_model=EvaluateResponse)
def evaluate(body: dict, bg: BackgroundTasks):
    upload_id = int(body.get("upload_id", 0))
    if upload_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid upload_id.")
    
    job_id = create_job(conn, upload_id)
    bg.add_task(run_pipeline, job_id)
    return EvaluateResponse(id=job_id, status="queued")

def run_pipeline(job_id: int):
    try:
        update_job_status(conn, job_id, "processing")
        job = get_job(conn, job_id)
        if not job:
            update_job_status(conn, job_id, "failed", error="Job not found."); return
        upload = get_upload(conn, job[1])
        if not upload:
            update_job_status(conn, job_id, "failed", error="Upload not found."); return
        
        _, cv_text, project_text = upload
        cv_part = evaluate_cv(conn, cv_text, extract_job_desc_from_pdf("data/jobdesc.pdf"))
        project_part = evaluate_project(conn, project_text, open("data/rubric.yaml").read())
    
        summary = overall_summary(cv_part, project_part)
        
        result = {
            "cv_match_rate": cv_part["percentage"],
            "cv_feedback": cv_part["feedback"],
            "project_score": project_part["percentage"],
            "project_feedback": project_part["feedback"],
            "overall_summary": summary
        }
        
        update_job_status(conn, job_id, "completed", result=result)
    except Exception as e:
        update_job_status(conn, job_id, "failed", error=str(e))

@app.get("/result/{job_id}", response_model=JobResult, response_model_exclude_none=True)
def get_result(job_id: int):
    job = get_job(conn, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    
    id, _, status, result_json, error = job
    if status in ("queued", "processing"):
        return JobResult(id=id, status=status, result=None)
    if status == "failed":
        raise HTTPException(status_code=500, detail=f"Job failed: {error}")
    return JobResult(id=id, status=status, result=json.loads(result_json))
