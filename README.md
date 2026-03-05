# Secure Cloud Storage (SCS) Project

## Overview
[cite_start]The Secure Cloud Storage (SCS) project is a privacy-first storage solution designed to ensure that sensitive data remains confidential even when stored in the public cloud[cite: 1, 9]. [cite_start]Unlike traditional storage, this system performs **Client-Side Encryption**, meaning your files are locked on your local machine before they ever reach the internet[cite: 7, 8]. [cite_start]AWS only ever stores and manages encrypted "ciphertext"[cite: 9].

[cite_start]To enable searching over encrypted data without decrypting it on the server, this project implements **Symmetric Searchable Encryption (SSE)** using the **Hexie** and **Jianding** algorithms[cite: 96, 104].

---

## Core Algorithms

### 1. Hexie: Dynamic Searchable Encryption
[cite_start]Hexie is the base algorithm providing **Forward and Backward Privacy**[cite: 103, 261].
* [cite_start]**Mechanism**: It implements secret sharing to conceal index entries, enabling dynamic updates and lightweight clients[cite: 105, 192].
* [cite_start]**Update Logic**: For each keyword/document pair, the client generates a secret share and XORs it with the previous "last share" stored in the local `DI` (Inverted Index) or `DF` (Forward Index)[cite: 307, 342].
* [cite_start]**Search**: The client generates a trapdoor consisting of a secret key and the last share[cite: 317, 342]. [cite_start]The server uses this to "unravel" the chain of XORed shares stored in the cloud until it reaches the stop signal $1^{\lambda}$[cite: 334, 407].

### 2. Jianding: Verifiable Integrity
[cite_start]Jianding is an extension of Hexie that adds a search result verification mechanism to protect against malicious or faulty cloud providers[cite: 106, 193].
* [cite_start]**Mechanism**: It combines a **Chained MAC** (Message Authentication Code) structure with the secret sharing scheme[cite: 107, 194].
* [cite_start]**Integrity**: Each encrypted entry contains the MAC of the previous entry in the chain[cite: 421, 424].
* [cite_start]**Verification**: The client stores the MAC of the final entry locally[cite: 425]. [cite_start]During decryption, the client verifies the MACs of retrieved ciphertext from last to first to ensure the cloud has not returned empty, incomplete, or inaccurate results[cite: 431, 433].

---

## Repository Structure

### 1. Application Code (`app/`)
* [cite_start]**`app.py`**: Flask UI for the local web application[cite: 25, 26].
* [cite_start]**`aws_client.py`**: Handles `boto3` calls to interact with AWS services like S3[cite: 32, 35].
* **`encryption.py`**: Core AES encryption and decryption utilities[cite: 27, 28].
* [cite_start]**`hexie.py`**: Implementation of the Hexie index logic and secret sharing[cite: 29, 30].
* [cite_start]**`jianding.py`**: Implementation of the Jianding verification and MAC chaining logic[cite: 31, 34].
* **`templates/`**: HTML files for the web interface (`index.html`, `upload.html`, `search.html`)[cite: 36, 40].

### 2. Infrastructure Code (`infrastructure/terraform/`)
* [cite_start]**`main.tf`**: Defines AWS resources including the **S3 Bucket** (`scs-encrypted-files-bucket`) and **EC2 Instance**[cite: 18, 20].
* [cite_start]**`variables.tf`**: Configurable variables for the infrastructure[cite: 21].
* **`outputs.tf`**: Outputs the public URL of the deployed web server[cite: 23].

### 3. GitHub Workflows (`.github/workflows/`)
* [cite_start]**`deploy.yml`**: CI/CD pipeline to automatically deploy infrastructure on push to `main`[cite: 46, 47].
* [cite_start]**`destroy.yml`**: Workflow to manually tear down AWS resources[cite: 48].

---

## Setup and Usage

### Prerequisites
* **Python 3.x**: Installed locally[cite: 51].
* [cite_start]**AWS CLI**: Configured via `aws configure` to provide local credentials[cite: 63, 77].
* [cite_start]**Dependencies**: Install via `pip install -r requirements.txt` (includes `flask`, `boto3`, and `cryptography`)[cite: 55, 59].

### Verification
1. **Hexie Test**: Use `test_upload.py` and `test_download.py` to confirm basic S3 connectivity.
2. **Algorithm Test**: Run the `hexie.py` logic to ensure keywords can be searched after multiple updates. [cite_start]Enable `jianding.py` to verify that any modification of ciphertext on the server is detected[cite: 194, 430].

---

## Future Work
* [cite_start]**Dictionary Sharding**: Implement graph-based dictionary sharding to enhance search efficiency[cite: 108, 196].
* **Compaction**: Implement index reconstruction to physically remove deleted entries and optimize storage[cite: 396, 397].