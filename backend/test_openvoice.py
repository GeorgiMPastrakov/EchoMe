from gradio_client import Client

client = Client("https://myshell-ai-openvoice.hf.space/--replicas/pe0v7/")
result = client.predict(
    "Test 123!",
    "default",
    "uploaded_audio/recorded.wav",  # full path to a real file
    True,
    fn_index=1
)
print(result)
