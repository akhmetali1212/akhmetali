import requests

def process_contract(file_path):
    with open(file_path, 'r') as f:
        text = f.read()
    

    if "BIN" not in text:
        print("BIN missing")
    
  
    response = requests.post("https://api.example.com/ocr", data=text)
    
    print("Processed:", text)
