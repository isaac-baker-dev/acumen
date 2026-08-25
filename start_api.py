if __name__ == "__main__":
    import uvicorn
    uvicorn.run("acumen.interface.api:app", host="127.0.0.1", port=8000, workers=2)