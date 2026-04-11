import asyncio
import sys
sys.path.insert(0, '.')

print("Step 1: Starting", flush=True)

try:
    from app.services.unified_auth import UnifiedAuthService
    print("Step 2: Imported", flush=True)
    
    async def main():
        print("Step 3: Calling verify", flush=True)
        r = await UnifiedAuthService.verify_spapi_credentials('test', 'test', 'test', 'x')
        print(f"Step 4: Result = {r}", flush=True)
    
    asyncio.run(main())
except Exception as e:
    print(f"Error: {e}", flush=True)
    import traceback
    traceback.print_exc()
