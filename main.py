from fastapi import FastAPI
from routes.consultation import router as consultation_router
from routes.demo_audio import router as demo_router
from routes.guide import router as guide_router
from routes.story import router as story_router
from routes.support import router as support_router
from routes.company_info import router as company_info_router
# Initialize FastAPI with metadata
app = FastAPI(title="Music Instrument Sales AI API")

# Include routers for each functionality
app.include_router(consultation_router, prefix="/consultation")
app.include_router(demo_router, prefix="/demo")
app.include_router(guide_router, prefix="/guide")
app.include_router(story_router, prefix="/story")
app.include_router(support_router, prefix="/support")
app.include_router(company_info_router, prefix="/company-info")
@app.get("/")
async def root():
    return {"message": "AI Chatbot for Music Instruments Sales API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=4)  # 4 workers for concurrency