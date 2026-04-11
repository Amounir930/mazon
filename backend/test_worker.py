"""Test browser_worker"""
import asyncio
import multiprocessing

async def main():
    from app.services.browser_worker import browser_login, get_browser_worker
    get_browser_worker().start()
    
    print("Starting test...")
    result = await browser_login(
        email="test@example.com",
        password="test123", 
        country_code="eg"
    )
    print(f"Result: {result}")
    get_browser_worker().stop()

if __name__ == '__main__':
    asyncio.run(main())
    print("DONE")
