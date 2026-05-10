import json
import hashlib
import hmac
import os
import paramiko
from encryption import derive_keys
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
TARGET_PATH = os.path.join(PARENT_DIR, "infrastructure", "terraform", "access.pem")

print(BASE_DIR)
# --- CONFIGURATION FROM .ENV ---
EC2_IP = os.getenv("EC2_HOSTNAME") # Using your existing env variable
SSH_KEY = TARGET_PATH # e.g., "my-key.pem"
REMOTE_FILE = "/home/ubuntu/hexie_server/cloud_index.json"
LOCAL_STATE = "local_hexie_state.json"
LOCAL_CLOUD = "cloud_index.json"

def sync_cloud_index():
    """Connects to Ubuntu EC2 and downloads the index automatically."""
    print(f"Connecting to {EC2_IP}...")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Always uses 'ubuntu' and your .pem key
        client.connect(hostname=EC2_IP, username="ubuntu", key_filename=SSH_KEY)
        
        sftp = client.open_sftp()
        sftp.get(REMOTE_FILE, LOCAL_CLOUD)
        sftp.close()
        client.close()
        
        # Format the JSON nicely for you to read locally
        with open(LOCAL_CLOUD, 'r') as f:
            data = json.load(f)
        with open(LOCAL_CLOUD, 'w') as f:
            json.dump(data, f, indent=4)
            
        print("Done! cloud_index.json is now updated and formatted.")
        return True
    except Exception as e:
        print(f"Failed to fetch: {e}")
        return False

def xor_bytes(b1, b2):
    return bytes(a ^ b for a, b in zip(b1, b2))

def visualize(keyword):
    # Auto-sync with EC2 to get cloud_index.json
        if not sync_cloud_index():
            return

        state = json.load(open(LOCAL_STATE))
        cloud = json.load(open(LOCAL_CLOUD))

        kw = keyword.lower().strip()
        if kw not in state:
            print(f"Keyword '{kw}' not found.")
            return

        # 1. INITIAL CONTEXT
        kt1, _, kv = derive_keys(kw)
        curr_pi = bytes.fromhex(state[kw])
        stop_sig_hex = (b'1' * 16).hex() # The '313131...' hex for '111...' bytes

        print(f"\nGenerating Chains for keyword: '{kw}'")
        print(f"Search Key (kt1): {kt1.hex()}")
        print(f"Current π: {curr_pi.hex()}")
        print(f"Stop Signal:  {stop_sig_hex}")
        print(f"{'='*60}\n")

        link_num = 1
        while True:
            # Step A: Derive the Index Address (c_w)
            c_w = hashlib.sha256(curr_pi).hexdigest()
            
            if c_w not in cloud:
                print(f"Error: Link {link_num} broken")
                print(f"at address c_w: {c_w}")
                print(f"[!] Jianding Incomplete Chain ALert \n")
                break
            
            entry = cloud[c_w]
            c_a = bytes.fromhex(entry['c_a'])
            
            # Step B: Jianding Audit (MAC check)
            tag = c_w.encode() + entry['c_id'].encode() + entry['f_hash'].encode()
            v_check = hmac.new(kv, tag, hashlib.sha256).hexdigest()
            status = "VALID" if v_check == entry['v'] else "TAMPERED"

            # Step C: Visual Link Representation
            print(f"LINK #{link_num}")
            print(f"  Address (c_w): {c_w}")
            print(f"  Masked (c_a):  {entry['c_a']}")
            print(f"  S3 Key (c_id): {entry['c_id']}")
            print(f"  File Name:     {entry['original']}")
            print(f"  Integrity:     {status}")

            # Step D: The XOR Hop
            mask = hashlib.sha256(kt1 + curr_pi).digest()[:16]
            r = xor_bytes(c_a, mask)
            curr_pi = xor_bytes(curr_pi, r)
            next_pi_hex = curr_pi.hex()

            print(f"  Random (r):    {r.hex()}")
            print(f"  Next π (prev): {next_pi_hex}")

            # Step E: Stop Condition[cite: 1]
            if next_pi_hex == stop_sig_hex:
                print(f"\n[***] STOP SIGNAL REACHED [***]")
                print(f"Chain complete. Total Links: {link_num}")
                break
            
            print(f"\n      ▼\n")
            link_num += 1

if __name__ == "__main__":
    target = input("Enter keyword: ")
    visualize(target)