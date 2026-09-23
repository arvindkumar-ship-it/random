from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

from app.config import settings
from app.models.schemas import ClaimInput, VerificationResult
from app.services.pipeline import VerificationPipeline

app = FastAPI(
    title="Claim Verification Engine",
    description="Multimodal AI-based claim verification system",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pipeline
pipeline = VerificationPipeline()


@app.get("/")
async def root():
    return {"message": "Claim Verification Engine API", "version": "1.0.0"}


@app.post("/verify", response_model=VerificationResult)
async def verify_claim(input_data: ClaimInput):
    """
    Verify a claim using multimodal AI
    """
    try:
        input_dict = input_data.model_dump()
        result = await pipeline.verify(input_dict)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
