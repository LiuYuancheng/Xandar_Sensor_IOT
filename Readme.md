# IoT Supply Chain Protection Case Study : Use Shadow-Box-For-Arm and PATT for Firmware Integrity Assurance

**Project Design Purpose** : This article will introduce a proof-of-concept (POC) case study on securing the IoT firmware supply chain by combining a Trusted Execution Environment (TEE) with physics-based runtime attestation. This experiment demonstrates how to use the [shadow-box-for-arm](https://github.com/kkamagui/shadow-box-for-arm) to establish a lightweight TEE on ARM-based IoT devices, and how integrating the [PATT: Physics-based Attestation of Control Systems](https://repository.sutd.edu.sg/esploro/outputs/conferenceProceeding/PAtt-Physics-based-Attestation-of-Control-Systems/9911651509846) in the IoT firmware to provide continuous firmware integrity assurance.

This article is organized into four key components:

- **IoT Radar Device with PATT Integration** : Introduction of the design of a people-detection IoT radar IoT device and the integration of the PATT algorithm to model and verify the IoT executing firmware. 
- **TEE Deployment Using Shadow-Box-For-Arm** : Implementation of a Trusted Execution Environment to securely isolate sensitive assets of the IoT device, including firmware logic and the PATT attestation mechanism.
- **Secure Firmware Provisioning During Manufacturing** : Design of protection mechanisms during the initial firmware flashing stage to ensure authenticity and prevent unauthorized modification within the supply chain.
- **Runtime IoT Firmware Attestation** : Continuous integrity verification of the deployed firmware using PATT, enabling detection of anomalies or malicious tampering during device operation.

This case study is a Proof of Concept for IOT Supply Chain Protection, in real production environment, the feature will be more complex.

```python
# Author:      Yuancheng Liu
# Created:     2020/06/29
# Version:     v_0.0.2
# Copyright:   Copyright (c) 2020 Liu Yuancheng
# License:     MIT License
```

**Table of Contents**

[TOC]

- [IoT Supply Chain Protection Case Study : Use Shadow-Box-For-Arm and PATT for Firmware Integrity Assurance](#iot-supply-chain-protection-case-study---use-shadow-box-for-arm-and-patt-for-firmware-integrity-assurance)
    + [1. Introduction](#1-introduction)
    + [2. Project Overview](#2-project-overview)
    + [3. System Workflow](#3-system-workflow)
      - [3.1 Firmware Flashing Attestation Workflow](#31-firmware-flashing-attestation-workflow)
      - [3.2  IoT Device Real-Time Attestation](#32--iot-device-real-time-attestation)
    + [4. Design of the Xandar IoT Device](#4-design-of-the-xandar-iot-device)
      - [4.1 Sensor Data Visualization UI](#41-sensor-data-visualization-ui)
      - [4.2 Top-View Area Monitoring UI](#42-top-view-area-monitoring-ui)
      - [4.3 Top-View Area Monitoring Dashboard](#43-top-view-area-monitoring-dashboard)
      - [4.4 Security Integration Considerations](#44-security-integration-considerations)
    + [5. Design of the IoT TrustZone](#5-design-of-the-iot-trustzone)
      - [5.1 Additional steps setup shadow-box](#51-additional-steps-setup-shadow-box)
    + [6. Device Manufacturer Initial Firmware Flashing](#6-device-manufacturer-initial-firmware-flashing)
      - [6.1 System Architecture](#61-system-architecture)
      - [6.2 Firmware Flashing Workflow](#62-firmware-flashing-workflow)
    + [7. Real-Time Firmware Authorization](#7-real-time-firmware-authorization)
      - [7.1 System Architecture](#71-system-architecture)
      - [7.2 Authorization Workflow](#72-authorization-workflow)
    + [8. Conclusion and Reference](#8-conclusion-and-reference)
      - [8.1 Conclusion](#81-conclusion)
      - [8.2 Reference Link](#82-reference-link)



------

### 1. Introduction 

The Internet of Things (IoT) is smart embedded devices that have the ability to transfer data over a network without requiring human or computer interaction. While IoT technologies enable significant innovation across industries, their highly distributed and multi-stakeholder supply chains introduce substantial security risks. Devices often pass through multiple vendors, manufacturers, and integrators, creating numerous opportunities for adversaries to tamper with hardware or firmware. 

The complexity of the IoT supply chain makes it particularly vulnerable to attacks such as firmware modification, counterfeit component insertion, intellectual property theft, and malicious code injection. A practical example is demonstrated in this [Drone Firmware Attack and Defense Case Study](https://www.linkedin.com/pulse/ot-cyber-attack-workshop-case-study-05-drone-firmware-yuancheng-liu-giogc):

 ![](doc/img/s_02.png)

Where an attacker replaced legitimate sensor firmware during transit, ultimately causing system malfunction and device failure during operation.

To address these challenges, ensuring firmware integrity across the entire device lifecycleâ€”from manufacturing to deployment and runtimeâ€”is critical. This project presents a proof-of-concept (PoC) system designed to protect IoT firmware integrity by combining secure execution and continuous attestation mechanisms.

The goal of this project is to design and validate an end-to-end protection pipeline that safeguards IoT firmware across both manufacturing and operational phases. By combining secure execution with behavior-based attestation, the proposed approach addresses limitations of traditional static verification methods and enhances resilience against supply chain tampering and runtime compromise. 



------

### 2. Project Overview

In an IoT supply chain, malicious activities can occur at any stage, including firmware development, flashing, distribution, and deployment. Therefore, a robust protection mechanism must ensure both firmware authenticity at provisioning time and integrity verification during runtime.

This project proposes an end-to-end firmware protection framework that spans from initial firmware flashing to real-time device operation. The system integrates hardware-based isolation with physics-based attestation to detect both static and dynamic threats. The project structure diagram is shown below: 

![](doc/img/s_03.png)

The overall system architecture includes the following key components:

- **Xandar IoT Device Platform** : A reconfigurable IoT testbed built using a [Xandar People Detection Radar](https://xkcorp.com/) sensor integrated with a Raspberry Pi-3B, supporting multiple files firmware execution and configurations.
- **IoT Runtime Attestation via PATT** : Integration of Physics-based Attestation of Control Systems (PATT) client, which validates firmware integrity by correlating software execution with expected physical behavior.
- **IoT Trusted Execution Environment (TEE)** : Deployment of a secure execution environment on Raspberry Pi using shadow-box-for-arm to protect radar sensor data fetching code and attestation logic from tampering.
- **Secure Firmware Provisioning Pipeline** : A manufacturer-side firmware signing client and a service provider–side signature authority server to ensure firmware authenticity during the flashing process.
- **Cloud-Based Verification Infrastructure** : An IoT verification server that performs device authentication and integrity validation by coordinating with the signature authority and processing attestation results.



------

### 3. System Workflow

The system enforces firmware integrity through two main workflows: 

- (1) secure firmware flashing during manufacturing 
- (2) real-time attestation during device operation.

#### 3.1 Firmware Flashing Attestation Workflow

The Firmware flashing attestation work flow is shown in the below diagram: 

```mermaid
sequenceDiagram
    participant Manufacturer_[Client_A] 
    participant Signature_Authority_Server
    Manufacturer_[Client_A] ->> Signature_Authority_Server:1. Login with A's credentials
    Signature_Authority_Server ->> Signature_Authority_Server:2. Server authentication, if pass send A challenge, r, for PATT
    Signature_Authority_Server ->> Manufacturer_[Client_A]:3. PATT challenge + r
    Manufacturer_[Client_A] ->> Manufacturer_[Client_A]: 4. Attest the firmware by PATT with r locally in flash machine
    Manufacturer_[Client_A] ->> Manufacturer_[Client_A]:5. Sign firware and generate the sign(M)
    Manufacturer_[Client_A] ->> Signature_Authority_Server: 6. Upload IoT server with M and sign(M)
    Signature_Authority_Server ->> Signature_Authority_Server:7. Verify timestamp, PATT checksum and Sign(m) then update database
    Signature_Authority_Server ->> Signature_Authority_Server:8. Server generate Sign(S) = Sign[M, Sign(M)]
    Signature_Authority_Server ->> Manufacturer_[Client_A]:9. Return Sign(S) to manufacturer
    Manufacturer_[Client_A] ->> Manufacturer_[Client_A]:10. flash firmware + Sign(S)
```

```
Update message : M = ID + version + sensor type + flashing timestamp
Signature : Sign(M) = M + MD5(firmware)
```

During the manufacturing phase, firmware authenticity and integrity are verified before deployment to the IoT device. The process involves a challenge-response mechanism combined with cryptographic signing:

- The manufacturer client authenticates with the signature authority server.
- The server issues a challenge value (*r*) for attestation.
- The firmware is locally verified using the PATT algorithm and signed.
- The signed firmware and metadata (*M*) are uploaded to the server.
- The server validates the submission and generates a secondary signature (*Sign(S)*) to certify the firmware.
- The certified firmware is then securely flashed onto the IoT device.

#### 3.2  IoT Device Real-Time Attestation

The IoT device real time attestation is  shown in the below diagram: 

```mermaid
sequenceDiagram
    participant IoT_Device
    participant IoT_Monitor_Hub
    participant Signature_Authority_Server
    IoT_Device ->> IoT_Monitor_Hub: 1.Report to IoT Hub
    IoT_Monitor_Hub ->> IoT_Device: 2.Hub PATT verification request 
    IoT_Device ->> IoT_Monitor_Hub: 3.Reply reg0 = M + Sign(S)
    IoT_Monitor_Hub ->> IoT_Monitor_Hub: 4.IoT_Monitor_Hub verify reg0
    IoT_Monitor_Hub ->> Signature_Authority_Server: 5. IoT_Device registration reuqest
    Signature_Authority_Server ->> IoT_Monitor_Hub: 6. Server verification request, r
    IoT_Monitor_Hub ->> IoT_Device: 7. Server verification request, r
    IoT_Device ->> IoT_Device: 8. IoT_Device run PATT with r to calculate firmware checksum N
    IoT_Device ->> IoT_Monitor_Hub: 9 reply reg1 = M+N
    IoT_Monitor_Hub ->> Signature_Authority_Server: 10. reply reg1 = M+N
    Signature_Authority_Server ->> Signature_Authority_Server: 11. Server verification reg1 and check data base record
    Signature_Authority_Server ->> Signature_Authority_Server: 12. Update database and sensor suthentication result
    Signature_Authority_Server ->> IoT_Monitor_Hub: 13. IoT device registeration state
    IoT_Monitor_Hub ->> IoT_Monitor_Hub: 14. Start receive the IoT device data stream if step 13 success
```

After deployment, the system continuously verifies firmware integrity through runtime attestation:

- The IoT device registers with the monitoring hub and responds to attestation requests.
- The monitoring hub validates stored firmware metadata and communicates with the signature authority server.
- A new challenge (*r*) is issued to the device.
- The device executes the PATT algorithm to compute a runtime checksum (*N*).
- The result is verified against server-side records to confirm firmware integrity.
- Upon successful verification, the device is authorized to transmit operational data.

This runtime verification mechanism enables detection of firmware tampering, unauthorized modifications, or anomalous behavior during operation.



------

### 4. Design of the Xandar IoT Device 

The IoT device is built around a Xandar Kardian people detection radar sensor and a Raspberry Pi-3B to supports real-time sensing and visualization, and also integrates securely with the proposed firmware protection pipeline, including Trusted Execution Environment (TEE) isolation and physics-based attestation. The connection between use a CAT5-USB cable as shown below: 

![](doc/img/s_04.png)

The the Raspberry Pi use its wifi module to connect to the internet. A custom application, referred to as **Xandar Sensor App**, is implemented on the device to collect, process, and visualize sensor data, then connect the the IoT hub server. The application is designed to support both single-sensor and multi-sensor configurations.

#### 4.1 Sensor Data Visualization UI 

This module provides real-time and historical visualization of sensor outputs as shown below:

![](doc/img/s_05.png)

It displays:

- Current detected people count
- Average people count over time
- Normalized people count (post-processed value for stability and accuracy)

Additional features include:

- Display of sensor metadata such as sensor ID, connection interface, and data sequence index
- A pause/resume mechanism to allow inspection of live data streams
- A detailed parameter panel exposing up to 36 sensor-specific parameters for in-depth analysis
- Multi-sensor switching via tab-based navigation

This dashboard plays a critical role in validating both sensor behavior and the consistency of firmware execution, which is later leveraged by the attestation mechanism.

#### 4.2 Top-View Area Monitoring UI

This module provides a spatial visualization of the monitored indoor environment as shown below:

![](doc/img/s_06.png)

- A **top-view map** displaying sensor placement and coverage
- Real-time visualization of **people density distribution** across the area
- Sensor connectivity status and live data feedback

This view helps correlate physical observations with sensor outputs, which is particularly important for validating the assumptions used in the **PATT (Physics-based Attestation)** model.

#### 4.3 Top-View Area Monitoring Dashboard

This module provides a spatial visualization of the monitored indoor environment as shown below:

![](doc/img/s_07.png)

- A **top-view map** displaying sensor placement and coverage
- Real-time visualization of **people density distribution** across the area
- Sensor connectivity status and live data feedback

This view helps correlate physical observations with sensor outputs, which is particularly important for validating the assumptions used in the **PATT (Physics-based Attestation)** model.

#### 4.4 Security Integration Considerations

The IoT device is designed with security as a core requirement:

- Sensitive components, including the PATT algorithm and firmware verification logic, are protected within a Trusted Execution Environment using Shadow-Box-For-Arm
- Firmware integrity is verified both during flashing and at runtime
- Sensor data used for attestation is safeguarded against tampering

By combining sensing, visualization, and security mechanisms within a single platform, this IoT device serves as a practical and extensible testbed for evaluating supply chain protection strategies.



------

### 5. Design of the IoT TrustZone 

The TEE is used to securely store and execute critical components, including the device’s unique identity and PATT attestation credentials.I use the project Trust-Zone/Env (OPTEE) on Raspberry PI I developed : https://github.com/LiuYuancheng/Raspberry_PI_OPTEE and the https://github.com/kkamagui/shadow-box-for-arm project to implement the Trusted Execution Environment to protect the Unique ID and PATT credential files. the work flow is shown below: 

![](doc/img/s_08.png)

#### 5.1 Additional steps setup shadow-box

The Shadow-Box environment is deployed by following the “Build Shadow-Box for ARM and Make Secure Pi with Raspberry Pi 3” procedure from the official repository. However, several additional adjustments are required to ensure proper functionality on a Raspberry Pi 3 Model B.

**5.1.1 Root Filesystem and Boot Image Synchronization**

During the step *“**3.5.1** Copy OP-TEE OS with Shadow-Box for ARM and New Linux Kernel to Raspbian OS”*, it is critical to ensure that the required image files are correctly copied into both the `boot` and `boot1` directories as shown below:

![](doc/img/s_09.png)

In addition, the root filesystem must be extracted into the `boot1` directory using:

```
sudo gunzip -cd $HOME/shadow-box/gen_rootfs/filesystem.cpio.gz | sudo cpio -iudmv "boot1/*"
```

Also verify that the kernel module directory: `/rootfs/lib/modules/4.6.3-17586g76cacae` exists on the Raspberry Pi SD card. This specific kernel version is required for compatibility with Shadow-Box as shown below:

![](doc/img/s_10.png)

**5.1.2 shadow_box_client Binary Validation**

During activation (step: 3.6.5. Activate Shadow-Box for ARM and  Start Secure Pi), running:

```
sudo shadow_box_client -g
```

may produce no output if the client binary is incorrectly deployed.

To troubleshoot:

- Check `/bin/shadow_box_client` file size
- If the size is abnormally small (e.g., ~1KB), the binary is corrupted or empty

Fix step as shown below:

![](doc/img/s_11.png)

- Rebuild the binary from the Shadow-Box project directory:

  ```
  shadow-box/optee_examples_shadow_box_client/host
  ```

- Run `make` if the executable is missing

- Copy the rebuilt binary to the Raspberry Pi:

  ```
  /bin/shadow_box_client
  ```

After copying, sign the binary using:

```
sudo ./img_sign.sh /bin/shadow_box_client
```

![](doc/img/s_12.png)

**5.1.3 Kernel Version Verification**

Before enabling Shadow-Box protection:

![](doc/img/s_13.png)

```
sudo shadow_box_client -s
```

Ensure that the system is running the correct kernel version:

```
sudo uname -r
```

The output must match:

```
4.6.3-17586g76cacae
```

Any mismatch (e.g., newer kernels like 4.17+) may cause Shadow-Box to fail.

**5.1.4 Execution Path Requirement**

When executing Shadow-Box client in section 3.6.6. Check Your Secure Pi Remotely  commands such as:

![](doc/img/s_14.png)

```
sudo shadow_box_client -l
```

it is necessary to first navigate to the Shadow-Box project directory:

```
cd $HOME/shadow-box-for-arm
```

Failing to do so may result in execution errors due to missing relative paths or dependencies.



------

### 6. Device Manufacturer Initial Firmware Flashing

During the manufacturing phase, when the IoT device firmware is flashed into the device’s ROM, a **firmware signing and registration mechanism** is introduced to ensure authenticity and prevent unauthorized device cloning.

Each firmware instance is bound to a **unique cryptographic signature**, generated at flashing time. This mechanism ensures that even if an attacker obtains a firmware image, flashing tool, or unused hardware, they cannot produce a valid device that can authenticate with the backend system.

#### 6.1 System Architecture

The firmware flashing and verification system consists of two main components:

**Firmware Flashing Client** -- A client application running on the manufacturer’s workstation. It is responsible for:

- Authenticating with the server
- Generating firmware attestation data
- Flashing firmware and signatures into the IoT device

**Firmware Verification Server** -- A backend service deployed on the IoT service provider side. It is responsible for:

- Verifying firmware integrity and client authenticity
- Generating server-side signatures
- Recording device registration data in a secure database

#### 6.2 Firmware Flashing Workflow

The firmware provisioning process consists of three main steps:

**6.2.1 Step 1: System Initialization and Client Authentication**

The manufacturer must authenticate using valid credentials (username and password) before accessing the firmware flashing functionality. Unauthorized users are denied access. The program execution flow is shown in the Figure below:

![](doc/img/s_15.png)

Once authentication is successful:

- The server generates and sends a **random SWATT challenge string** to the client
- The client enables firmware selection and preparation for attestation

This challenge-response mechanism ensures freshness and prevents replay attacks.

**6.2.2 Step 2: Client Signature Generation and Server Certification**

The program execution flow is shown in the Figure below: 

![](doc/img/s_16.png)

After selecting the firmware:

1. **SWATT-Based Integrity Measurement**
    The client computes a firmware checksum using the SWATT algorithm based on the received challenge string.
    The server independently performs the same computation for verification.

2. **Client-Side Signature Generation**
    The client constructs a metadata message:

   ```
   M = IoT_ID + Signer_ID + SWATT_value + Timestamp + Device_Type + Firmware_Version
   ```

   This message is signed using the client’s private SSL key to generate:

   ```
   Sign_client(M)
   ```

3. **Server Verification and Signature Issuance**
    The client sends *(M, Sign_client(M))* to the server.
    The server performs:

   - SWATT value verification
   - Client signature validation

   Upon successful verification, the server generates a **server signature**:

   ```
   Sign_server(S) = Sign[M + Sign_client(M)]
   ```

4. **Firmware Flashing**
    The firmware, along with the server signature *Sign_server(S)*, is flashed into the IoT device’s ROM.

5. Database Registration

   The server stores the following records:

   - Device metadata (M)
   - Client signature
   - Server signature

This step establishes a **trusted binding between the firmware, device identity, and manufacturer**.

**6.2.3 Step 3: IoT Device Verification During Operation**

When the IoT device connects to the backend system:

- It retrieves the stored **server signature** and associated metadata from ROM
- It sends this information to the IoT server as part of its registration request

The server then:

- Validates the received data against its database records
- Confirms the authenticity and integrity of the firmware

Only devices with valid, verifiable signatures are allowed to connect and transmit data. Any mismatch results in rejection, effectively preventing:

- Unauthorized firmware modification
- Device cloning or spoofing
- Use of unregistered or tampered devices

>  Firmware Flashing Sign program code : https://github.com/LiuYuancheng/Xandar_Sensor_IOT/tree/master/firmwSign



------

### 7. Real-Time Firmware Authorization

To ensure continuous integrity of executable files and firmware during device operation, this project implements a **real-time firmware authorization mechanism** based on a Trusted Execution Environment (TEE). The solution leverages OP-TEE (developed by Linaro), which enables secure execution alongside a non-secure Linux operating system on ARM platforms.

All sensitive operations—such as checksum computation, cryptographic processing, and key handling—are executed within the **Secure World**, preventing tampering from potentially compromised application layers.

#### 7.1 System Architecture

The real-time authorization system is composed of three main components:

**Trust-Application (Secure World – Raspberry Pi)** -- Runs inside the TEE and is responsible for:

- AES-256 key management
- Encryption and decryption operations
- SWATT-based file integrity measurement

**Trust-Client (Normal World – Raspberry Pi)** -- Acts as a bridge between the system and the TEE:

- Loads configuration parameters
- Communicates with the Trust-Application via OP-TEE
- Retrieves target files for verification
- Handles TCP communication with the backend server

**Trust-Server (Backend System)** -- Provides centralized verification and record management:

- Generates session keys and attestation challenges
- Performs independent integrity verification
- Stores and retrieves reference data from a database

#### 7.2 Authorization Workflow

The system performs real-time integrity authorization in four stages:

**7.2.1 Step 1: System Initialization**

During initialization the the Trust-Client loads configuration parameters from a local file, including:

- Server IP and port
- Target file or executable to verify
- Firmware version
- SWATT challenge length and iteration count

The client starts the **TEE supplicant service** to interface with the OP-TEE driver, the program execution flow is shown : 

![](doc/img/s_17.png)

- A secure session is established between the Trust-Client (Normal World) and the Trust-Application (Secure World)
- A TCP connection is established with the Trust-Server

This step prepares both secure and non-secure components for coordinated operation.

**7.2.2 Step 2: AES-256 Session Key Exchange**

To secure communication, The program execution flow is shown:

![](doc/img/s_18.png)

1. The Trust-Application selects a pre-provisioned AES-256 key (*Key A*) from its secure key store and sends the corresponding key ID to the server.
2. The Trust-Server retrieves the same key (*Key A*) from its database using the device ID and key ID.
3. The server generates a random **session key (Key B)** for this session.
4. Key B is encrypted using Key A and transmitted to the client.
5. The Trust-Application decrypts and securely stores Key B for subsequent communication.

Next:

- The server generates a random SWATT challenge string
- The challenge is encrypted using Key B and sent to the Trust-Application

This ensures both **confidentiality** and **freshness** of the attestation process.

**7.2.3 Step 3: File Integrity Authorization**

Once the session key and challenge are established, the program execution flow is shown: 

![](doc/img/s_19.png)

- The Trust-Client loads the target file from the local file system
- The Trust-Server retrieves the corresponding reference file or baseline data

Then:

- The Trust-Application computes the file’s integrity measurement using SWATT based on the received challenge
- The Trust-Server independently performs the same computation

The Trust-Application:

- Encrypts the computed checksum using Key B
- Sends the result to the Trust-Server

The server compares the received value with its own result to determine whether the file has been modified.

**7.2.4 Step 4: Authorization Result Feedback**

After verification, the program execution flow is shown: 

![](doc/img/s_20.png)

- The Trust-Server encrypts the authorization result along with the expected SWATT value using Key B
- The response is sent back to the Trust-Client

The Trust-Application:

- Decrypts the response
- Verifies that the returned SWATT value matches its locally computed result (ensuring response integrity)

If authorization is successful, the Trust-Client collects runtime metadata of the verified process, including:

- Process ID (PID)
- Execution user
- File descriptors
- Memory usage and offsets
- Node/system information
- Linked library files

This metadata is forwarded to the Trust-Server for monitoring and auditing, if authorization **fails**:

- The Trust-Client removes or blocks execution of the compromised file
- The event can be logged or trigger further security actions



------

### 8. Conclusion and Reference 

#### 8.1 Conclusion 

This case study presented a proof-of-concept implementation for securing IoT firmware throughout the supply chain and device lifecycle by combining hardware-assisted isolation with physics-based runtime attestation. By integrating **Shadow-Box-for-ARM** as a lightweight Trusted Execution Environment and **PATT** for continuous integrity verification, the proposed system addresses critical vulnerabilities at both manufacturing provisioning and operational stages.

The experimental deployment on a Xandar people-detection radar device with Raspberry Pi-3B demonstrated several key contributions: (1) secure firmware flashing with cryptographic binding between device identity and firmware image; (2) TEE-protected sensitive assets including attestation logic and unique credentials; and (3) real-time integrity verification enabling detection of tampering or unauthorized modifications during device operation.

While this implementation serves as a functional PoC on ARM-based IoT hardware, practical production deployment would require additional considerations including scalability to large device fleets, key management infrastructure, performance optimization for resource-constrained devices, and robustness against advanced physical attacks. Nevertheless, the demonstrated approach offers a viable direction for enhancing IoT supply chain resilience, showing that even modest ARM platforms can support meaningful firmware integrity guarantees when combining TEE isolation with behavior-based attestation mechanisms.

#### 8.2 Reference Link

- https://github.com/kkamagui/shadow-box-for-arm
- https://repository.sutd.edu.sg/esploro/outputs/conferenceProceeding/PAtt-Physics-based-Attestation-of-Control-Systems/9911651509846
- https://www.linkedin.com/pulse/ot-cyber-security-workshop-case-study-01-build-trust-zone-liu-h3chc/?trackingId=X%2FbjtY0uCv0L4JWW2qGckw%3D%3D
- https://www.linkedin.com/pulse/people-detection-radar-iot-yuancheng-liu-yovdc/?trackingId=u18yFQdOGjT%2FN6vn353Qeg%3D%3D
- https://github.com/LiuYuancheng/Xandar_Sensor_IOT
- https://github.com/LiuYuancheng/Xandar_PPL_Sensor_IOT_Web
- https://github.com/LiuYuancheng/Xandar_Sensor_App



------

> Last edit by LiuYuancheng(liu_yuan_cheng@hotmail.com) at 02/05/2026, if you have any problem please free to message me.