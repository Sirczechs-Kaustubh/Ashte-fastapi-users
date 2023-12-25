import uvicorn
import asyncio

if __name__ == "__main__":
    
    uvicorn.run("app.app:app",
                log_level="info")
