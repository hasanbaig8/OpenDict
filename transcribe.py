import nemo.collections.asr as nemo_asr
import sys
import json
import os
import pickle
import time

def get_model_cache_path():
    """Get the path for the cached model file"""
    cache_dir = os.path.expanduser("~/.opendict_cache")
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, "parakeet_model.pkl")

def load_or_cache_model():
    """Load model from cache or create cache if not exists"""
    cache_path = get_model_cache_path()
    
    if os.path.exists(cache_path):
        print("Loading cached model...", file=sys.stderr)
        try:
            with open(cache_path, 'rb') as f:
                model = pickle.load(f)
            print("Cached model loaded successfully!", file=sys.stderr)
            return model
        except Exception as e:
            print(f"Failed to load cached model: {e}", file=sys.stderr)
            print("Will load fresh model...", file=sys.stderr)
    
    print("Loading fresh model (this may take a moment)...", file=sys.stderr)
    start_time = time.time()
    model = nemo_asr.models.ASRModel.from_pretrained(model_name="nvidia/parakeet-tdt-0.6b-v2")
    load_time = time.time() - start_time
    print(f"Model loaded in {load_time:.2f} seconds", file=sys.stderr)
    
    print("Caching model for future use...", file=sys.stderr)
    try:
        with open(cache_path, 'wb') as f:
            pickle.dump(model, f)
        print("Model cached successfully!", file=sys.stderr)
    except Exception as e:
        print(f"Failed to cache model: {e}", file=sys.stderr)
    
    return model

def transcribe_audio(input_file_path):
    asr_model = load_or_cache_model()
    output = asr_model.transcribe([input_file_path])
    return output[0].text

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: python transcribe.py <input_file_path>"}))
        sys.exit(1)
    
    input_file_path = sys.argv[1]
    try:
        result = transcribe_audio(input_file_path)
        output_data = {"text": result}
        
        # Get the directory of the input file
        input_dir = os.path.dirname(input_file_path)
        output_path = os.path.join(input_dir, "output_text.json")
        
        # Write the result to output_text.json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(json.dumps(output_data))
    except Exception as e:
        print(json.dumps({"error": str(e)}))