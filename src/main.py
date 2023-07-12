from server import api, app

app.include_router(api)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, use_colors=True)
