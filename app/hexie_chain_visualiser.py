import json
import hashlib
import hmac
from encryption import derive_keys

# Paths to your files
STATE_FILE = "local_hexie_state.json"
CLOUD_FILE = "cloud_index.json"

def xor_bytes(b1, b2):
    return bytes(a ^ b for a, b in zip(b1, b2))

def visualize_chain(keyword):
    # 1. Load Data
    try:
        with open(STATE_FILE, 'r') as f:
            local_state = json.load(f)
        with open(CLOUD_FILE, 'r') as f:
            cloud_index = json.load(f)
    except FileNotFoundError as e:
        print(f"❌ Error: Could not find {e.filename}")
        return

    # 2. Setup Keyword Context
    keyword = keyword.lower().strip()
    if keyword not in local_state:
        print(f"❌ Keyword '{keyword}' not found in local state.")
        return

    kt1, _, kv = derive_keys(keyword)
    current_pi_hex = local_state[keyword]
    stop_signal_hex = (b'1' * 16).hex()
    
    print(f"\n{'='*60}")
    print(f"⛓️  HEXIE + JIANDING CHAIN VISUALIZER: '{keyword}'")
    print(f"{'='*60}")
    print(f"Start Trapdoor (π): {current_pi_hex}")
    print(f"Stop Signal (1^λ):  {stop_signal_hex}")
    print(f"{'-'*60}\n")

    link_count = 0
    current_pi = bytes.fromhex(current_pi_hex)

    while True:
        link_count += 1
        # Calculate the Address (c_w)
        c_w = hashlib.sha256(current_pi).hexdigest()
        
        print(f"LINK #{link_count}")
        print(f"  📍 Address (c_w): {c_w}")

        if c_w not in cloud_index:
            print(f"  ❌ BREAK: Address not found in cloud_index.json!")
            print(f"     Status: Chain Incomplete/Broken.")
            break
        
        entry = cloud_index[c_w]
        c_a = bytes.fromhex(entry['c_a'])
        s3_key = entry['c_id']
        original = entry['original']
        v_stored = entry['v']

        # 3. Integrity Check (Jianding MAC)
        tag_content = c_w.encode() + s3_key.encode()
        v_calculated = hmac.new(kv, tag_content, hashlib.sha256).hexdigest()
        integrity = "✅ OK" if v_calculated == v_stored else "🚨 TAMPERED"

        # 4. Unmask the pointer (c_a) to find the link (r)
        mask = hashlib.sha256(kt1 + current_pi).digest()[:16]
        r = xor_bytes(c_a, mask)
        
        print(f"  📂 File: {original} ({s3_key[:12]}...)")
        print(f"  🛡️  MAC Check: {integrity}")
        print(f"  🔗 Unmasked r: {r.hex()}")

        # 5. Calculate next pi (Walking backward)
        current_pi = xor_bytes(current_pi, r)
        next_pi_hex = current_pi.hex()
        
        print(f"  👣 Next π:    {next_pi_hex}")

        if next_pi_hex == stop_signal_hex:
            print(f"\n🏁 REACHED STOP SIGNAL! Completeness Verified.")
            break
        
        print(f"  {'↓':^30}")

    print(f"\n{'='*60}")
    print(f"Search Results: Found {link_count} valid links.")
    print(f"{'='*60}")

if __name__ == "__main__":
    kw = input("Enter keyword to visualize: ").strip()
    visualize_chain(kw)