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

------

### 1. Introduction 

The Internet of Things (IoT) is smart embedded devices that have the ability to transfer data over a network without requiring human or computer interaction. While IoT technologies enable significant innovation across industries, their highly distributed and multi-stakeholder supply chains introduce substantial security risks. Devices often pass through multiple vendors, manufacturers, and integrators, creating numerous opportunities for adversaries to tamper with hardware or firmware. 

The complexity of the IoT supply chain makes it particularly vulnerable to attacks such as firmware modification, counterfeit component insertion, intellectual property theft, and malicious code injection. A practical example is demonstrated in this [Drone Firmware Attack and Defense Case Study](https://www.linkedin.com/pulse/ot-cyber-attack-workshop-case-study-05-drone-firmware-yuancheng-liu-giogc):

 ![](doc/img/s_02.png)

Where an attacker replaced legitimate sensor firmware during transit, ultimately causing system malfunction and device failure during operation.

To address these challenges, ensuring firmware integrity across the entire device lifecycle—from manufacturing to deployment and runtime—is critical. This project presents a proof-of-concept (PoC) system designed to protect IoT firmware integrity by combining secure execution and continuous attestation mechanisms.

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
- **Secure Firmware Provisioning Pipeline** : A manufacturer-side firmware signing client and a service provider�side signature authority server to ensure firmware authenticity during the flashing process.
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