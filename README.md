# Secure Cloud Storage (SCS) Project

## Overview
The Secure Cloud Storage (SCS) project is a privacy-first storage solution designed to ensure that sensitive data remains confidential even when stored in the public cloud. Unlike traditional storage, this system performs **Client-Side Encryption**, meaning your files are locked on your local machine before they ever reach the internet. AWS only ever stores and manages encrypted "ciphertext."

To enable searching over encrypted data without decrypting it on the server, this project implements **Symmetric Searchable Encryption (SSE)** using the **Hexie** and **Jianding** algorithms.

---

## Highlights
- **Privacy-First**: Ensures sensitive data remains confidential.
- **Client-Side Encryption**: Files are encrypted locally before upload.
- **Searchable Encryption**: Enables searching over encrypted data.
- **Integrity Verification**: Protects against malicious or faulty cloud providers.

---

## Core Algorithms

### 1. Hexie: Dynamic Searchable Encryption
Hexie is the base algorithm providing **Forward and Backward Privacy**.
- **Mechanism**: Implements secret sharing to conceal index entries, enabling dynamic updates and lightweight clients.
- **Update Logic**: For each keyword/document pair, the client generates a secret share and XORs it with the previous "last share" stored in the local `DI` (Inverted Index) or `DF` (Forward Index).
- **Search**: The client generates a trapdoor consisting of a secret key and the last share. The server uses this to "unravel" the chain of XORed shares stored in the cloud until it reaches the stop signal $1^{\lambda}$.

### 2. Jianding: Verifiable Integrity
Jianding is an extension of Hexie that adds a search result verification mechanism to protect against malicious or faulty cloud providers.
- **Mechanism**: Combines a **Chained MAC** (Message Authentication Code) structure with the secret sharing scheme.
- **Integrity**: Each encrypted entry contains the MAC of the previous entry in the chain.
- **Verification**: The client stores the MAC of the final entry locally. During decryption, the client verifies the MACs of retrieved ciphertext from last to first to ensure the cloud has not returned empty, incomplete, or inaccurate results.

---

## Repository Structure

### 1. Application Code (`app/`)
- **`app.py`**: Flask UI for the local web application.
- **`aws_client.py`**: Handles `boto3` calls to interact with AWS services like S3.
- **`encryption.py`**: Core AES encryption and decryption utilities.
- **`hexie.py`**: Implementation of the Hexie index logic and secret sharing.
- **`jianding.py`**: Implementation of the Jianding verification and MAC chaining logic.
- **`templates/`**: HTML files for the web interface (`index.html`, `upload.html`, `search.html`).

### 2. Infrastructure Code (`infrastructure/terraform/`)
- **`main.tf`**: Defines AWS resources including the **S3 Bucket** (`scs-encrypted-files-bucket`) and **EC2 Instance**.
- **`variables.tf`**: Configurable variables for the infrastructure.
- **`outputs.tf`**: Outputs the public URL of the deployed web server.

### 3. GitHub Workflows (`.github/workflows/`)
- **`deploy.yml`**: CI/CD pipeline to automatically deploy infrastructure on push to `main`.
- **`destroy.yml`**: Workflow to manually tear down AWS resources.

---

## Setup and Usage

### Prerequisites
- **Python 3.x**: Installed locally.