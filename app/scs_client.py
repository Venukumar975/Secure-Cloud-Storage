import os
import sys
import hashlib
import json
import uuid
import re
import requests
from PyPDF2 import PdfReader 
from encryption import encrypt_file, derive_keys
from aws_client import upload_file,verify_s3_upload
from dotenv import load_dotenv
import hmac


load_dotenv()

# --- CONFIGURATION ---
STATE_FILE = "local_hexie_state.json"
EC2_HOSTNAME = os.getenv("EC2_HOSTNAME", "127.0.0.1")
EC2_URL = f"http://{EC2_HOSTNAME}:5000"
BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

def load_json_state(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return json.loads(content) if content else {}
        except:
            return {}
    return {}

def get_clean_keywords(abs_path):
    """Scans filenames and PDF content for searchable tokens."""
    raw_words = []
    file_base = os.path.basename(abs_path)
    
    # 1. Extract from filename (Split by common delimiters)
    # Using lower() here immediately to normalize Upper case 
    raw_words.extend(re.split(r'[-_.\s]', file_base.lower())) # extracts file name like Aadhar.txt -> 'aadhar'
    
    # 2. Extract from PDF content using PyPDF2
    try:
        if abs_path.endswith('.pdf'):
            reader = PdfReader(abs_path)
            for page in reader.pages:
                text = page.extract_text()
                if text: 
                    # Normalize text to lower case and split
                    raw_words.extend(text.lower().split())  # appending keywords or raw words
        elif abs_path.endswith('.txt'):
            with open(abs_path, 'r') as f:
                raw_words.extend(f.read().lower().split())  # appending keywords
    except Exception as e:
        print(f" Content Scan Warning: {e}")

    # Refined stop words - 'txt' is a file extension, usually not a useful keyword
    stop_words = {'the', 'and', 'for', 'this', 'that', 'with', 'from', 'your', 'will', 'pdf', 'enc', 'txt'}
    coding_words = {'import', 'from', 'return', 'def', 'class', 'self', 'void', 'public', 'private'}

    useful = set()
    for word in raw_words:
        # Remove non-alphanumeric characters
        clean_word = re.sub(r'[^a-z0-9]', '', word)
        
        # VALIDATION: Ensure keyword isn't a stop word and meets length requirements
        if clean_word not in stop_words and clean_word not in coding_words:
            if clean_word.isalpha() and len(clean_word) >= 3:
                useful.add(clean_word) # Adding immutable elements ( keywords ) to set
            elif clean_word.isdigit() and len(clean_word) >= 9: # if keyword is a pure integer then only take those of lenght >= 9 like aadhar,
                useful.add(clean_word)
                
    return list(useful) # ('apple','raj') => ['apple','raj']

def run_upload(abs_path):
    if not os.path.exists(abs_path):
        print(f"Error: {abs_path} not found.")
        return

    file_base = os.path.basename(abs_path)  # Original file name
    print(f"\n Starting Hexie Upload: {file_base}")
    
    keywords = get_clean_keywords(abs_path)    # returns a list containing keywords ( filtered )
    if not keywords:     
        print(" No valid keywords found. Upload aborted.")
        return
        
    print(f" Extracted {len(keywords)} tokens: {keywords[:10]}...") # Showing Top 10 keywords in order 

    # Local Encryption
    cloud_id = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest() # This is hash is set to the file as its filename in S3 bucket
    s3_key = f"{cloud_id}.enc"    # S3 key , Here we can ommit .enc too.
    
    print(f" Encrypting locally on Client Side...")
    with open(abs_path, "rb") as f:
        # Note: encrypt_file uses the original filename as context
        ciphertext = encrypt_file(f.read(), file_base)  # encrypting data using file name as keyword_bytes

    temp_enc_path = os.path.join("temp_uploads", s3_key) # temporarily store enc files using their s3 enc key
    os.makedirs("temp_uploads", exist_ok=True)
    with open(temp_enc_path, "wb") as f:
        f.write(ciphertext)

    # # S3 Upload
    # print(f" Uploading to S3 Bucket...")
    # if not upload_file(temp_enc_path, s3_key):
    #     return

    # Hexie Index Update
    state = load_json_state(STATE_FILE)
    print(f" Linking {len(keywords)} keywords to EC2...")
    with open(temp_enc_path, "rb") as f:
       file_content = f.read()
       file_hash = hashlib.sha256(file_content).hexdigest()
    success_count = 0
    for kw in keywords:
        kt1, k2, kv = derive_keys(kw) # Get the verification key & search key using keyword as keyword_byts.
        
        # Algorithm 2: Chain generation
        pi_prev_hex = state.get(kw, (b'1' * 16).hex()) # hex('1') = '31' , therefore initil PI is set to 313131....(31 repeated 16 times)
        pi_prev = bytes.fromhex(pi_prev_hex)
        
        r = os.urandom(16)  # a random 16 byte value to ensure a good digest even if we upload same file
        new_pi = bytes(a ^ b for a, b in zip(pi_prev, r))
        
        c_w = hashlib.sha256(new_pi).hexdigest()      # H(PI)
        mask = hashlib.sha256(kt1 + new_pi).digest()[:16]
        c_a = bytes(a ^ b for a, b in zip(r, mask)).hex()
        
        # Algorithm 3: Generation of Verification Tag (Jianding)
        tag_content = c_w.encode() + s3_key.encode()+file_hash.encode()
        v = hmac.new(kv, tag_content, hashlib.sha256).hexdigest()

        try:
            resp = requests.post(f"{EC2_URL}/update", json={
                "c_w": c_w, 
                "c_a": c_a, 
                "c_id": s3_key, 
                "original": file_base,
                "v":v,
                "f_hash":file_hash  # Send the Jianding seal
            }, timeout=5)  
            
            if resp.status_code == 200:
                state[kw] = new_pi.hex()
                success_count += 1
        except Exception as e:
            print(f" Failed to reach EC2 for keyword '{kw}':Check Internet Connectivity and Ec2 IP")

    if success_count == len(keywords):
        print(f" Success! {success_count}/{len(keywords)} tokens linked in XOR chain.")
         # S3 Upload
        print(f" Uploading to S3 Bucket...")
        if upload_file(temp_enc_path, s3_key):
            
            if verify_s3_upload(BUCKET_NAME, s3_key):
                print(f" [OK] Verified: {s3_key[:8]}####.enc is safely stored in S3.")
            else:
                print(f" [!!] ALERT: Upload claimed success, but file not found in S3.")
        else:
            print(" [!!] Upload failed during transmission.")
            return
    
    # Save finalized local state
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)
    
    if os.path.exists(temp_enc_path):
        os.remove(temp_enc_path)
        
    
    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scs_client.py <abs_path>")
    else:
        run_upload(sys.argv[1])