import uvicorn

if __name__ == "__main__":
    # 这里的参数和命令行是完全等价的
    uvicorn.run("app.main:app", host="0.0.0.0", port=8897, reload=True)