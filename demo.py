

import argparse
import os
import base64
from gradio_client import Client


def parse_args():
    parser = argparse.ArgumentParser(
        description="Demo for calling the OpenVoice Gradio API via gradio_client"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="https://myshell-ai-openvoice.hf.space",  # Public Space URL
        help="Base URL of the Gradio Space endpoint (no /--replicas path)"
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default="Howdy!",
        help="Text prompt to send to the model"
    )
    parser.add_argument(
        "--style",
        type=str,
        default="default,default",
        help="Voice style to use (comma-separated, e.g. 'default,default')"
    )
    parser.add_argument(
        "--audio",
        type=str,
        default="https://github.com/gradio-app/gradio/raw/main/test/test_files/audio_sample.wav",
        help="Path or public URL to reference audio file"
    )
    parser.add_argument(
        "--agree",
        action="store_true",
        help="Agree to the terms of service checkbox"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    # Initialize client with public Space URL
    client = Client(args.api_url)

    # Call predict (fn_index=1)
    result = client.predict(
        args.prompt,
        args.style,
        args.audio,
        args.agree,
        fn_index=1
    )

    # Decode and save if data URI
    if isinstance(result, str) and result.startswith("data:audio"):
        header, b64data = result.split(',', 1)
        audio_data = base64.b64decode(b64data)
        output_path = os.path.join(os.getcwd(), "output.wav")
        with open(output_path, "wb") as f:
            f.write(audio_data)
        print(f"Audio saved to {output_path}")
    else:
        print("Result:", result)


if __name__ == "__main__":
    main()
