import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psutil
import uvicorn

# Note: Ensure these paths match your actual project structure
# from core.security import SecurityLoop
# from services.sensory import SensoryLoop
# from agents.cerebellum import CerebellumLoop

app = FastAPI(title="Aurelius Gateway API")

# GLOBAL CORS: Required for the Mini App to talk to Tailscale
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Reference placeholders for your main loops
# In your master_launcher, you would assign these: 
# gateway_api.security = my_security_loop
security = None 
sensory = None
cerebellum = None

@app.get("/status")
async def get_status():
    # Fallback values if loops aren't injected yet
    identity = "VERIFIED" if (cerebellum and not cerebellum.is_hibernating) else "ABSENT"
    ghost = "ACTIVE" if (cerebellum and cerebellum.is_hibernating) else "INACTIVE"
    vault = "ENCRYPTED" if ghost == "ACTIVE" else "DECRYPTED"
    
    return {
        "identity": identity,
        "ghost_mode": ghost,
        "vault_status": vault,
        "load": f"{psutil.cpu_percent()}%",
    }

@app.post("/action/{cmd}")
async def handle_action(cmd: str):
    try:
        if cmd == "purge":
            if not security:
                raise HTTPException(status_code=503, detail="SecurityLoop offline.")
            # Immediate lockdown sequence (requires zero args)
            asyncio.create_task(security.admin_departure())
            return {"status": "PURGING"}
        
        if cmd == "stealth":
            if not sensory:
                raise HTTPException(status_code=503, detail="SensoryLoop offline.")
            # Deafen microphones
            await sensory.hibernate() if sensory.mic_enabled else await sensory.resume()
            return {"status": "TOGGLED"}

        if cmd == "snapshot":
            if not cerebellum:
                raise HTTPException(status_code=503, detail="CerebellumLoop offline.")
            # Force manual memory encryption
            await cerebellum.hibernate()
            return {"status": "MEMORY_SECURED"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # HOST 0.0.0.0 is critical for Tailscale visibility
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        ssl_keyfile="eatmorevegetables.tailb7c548.ts.net.key", 
        ssl_certfile="eatmorevegetables.tailb7c548.ts.net.crt"
    )
