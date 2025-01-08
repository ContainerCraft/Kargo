# Network Engineering Documentation with Mermaid - Part 1: Getting Started with Network Diagrams

## Introduction

Mermaid enables network engineers to create and maintain network documentation directly in code, making it version-control friendly and easily maintainable. Network diagrams stay synchronized with infrastructure changes through simple text updates rather than complex visual editor manipulations.

### Installation

```bash
# NPM installation
npm install -g @mermaid-js/mermaid-cli

# Include in HTML
<script src="https://cdn.jsdelivr.net/npm/mermaid@11.4.0/dist/mermaid.min.js"></script>
```

Initialize Mermaid in your documentation:

```javascript
mermaid.initialize({
  startOnLoad: true,
  theme: 'default',
  flowchart: {
    useMaxWidth: false,
    htmlLabels: true
  }
});
```

## Core Network Diagram Types

### 1. Network Topology Flowcharts

Basic network topology using flowchart syntax:

```mermaid
flowchart LR
    Internet((Internet))
    FW[Firewall]
    R1[Core Router]
    SW1[Distribution Switch]
    AP1[Access Point]

    Internet --- FW
    FW --- R1
    R1 --- SW1
    SW1 --- AP1
```

Adding subnets and VLANs:

```mermaid
flowchart TB
    subgraph DMZ [DMZ Network 172.16.1.0/24]
        WEB[Web Server]
        MAIL[Mail Server]
    end

    subgraph Internal [Internal Network 10.0.0.0/8]
        AD[Active Directory]
        FS[File Server]
    end

    FW{Firewall} --> DMZ
    FW --> Internal
```

### 2. Protocol Interactions

Using sequence diagrams for network protocols:

```mermaid
sequenceDiagram
    participant C as Client
    participant R as Router
    participant D as DHCP Server

    C->>R: DHCP Discover
    R->>D: DHCP Discover
    D->>R: DHCP Offer
    R->>C: DHCP Offer
    C->>R: DHCP Request
    R->>D: DHCP Request
    D->>R: DHCP ACK
    R->>C: DHCP ACK
```

### 3. Device State Diagrams

Network interface states using state diagrams:

```mermaid
stateDiagram-v2
    [*] --> Down
    Down --> Init: Cable Connected
    Init --> Up: Interface Configuration OK
    Up --> Down: Cable Disconnected
    Up --> Error: Link Errors
    Error --> Down: Reset Interface
```

### 4. Packet Analysis

TCP/IP packet structure:

```mermaid
packet-beta
    title TCP/IP Packet Structure
    0-31: "IP Header"
    32-63: "TCP Header"
    64-95: "TCP Options (Optional)"
    96-255: "Data Payload"
```

## Basic Network Components

### Network Device Representation

Standard network device symbols:

```mermaid
flowchart TB
    classDef router fill:#f96,stroke:#333
    classDef switch fill:#69f,stroke:#333
    classDef firewall fill:#f66,stroke:#333

    R1[Router]:::router
    SW1[L3 Switch]:::switch
    FW1[Firewall]:::firewall

    R1 --- FW1
    FW1 --- SW1
```

### Complex Enterprise Example

```mermaid
flowchart TB
    subgraph DC [Data Center]
        FW1[ASA Firewall]
        CR1[Nexus 9000]
        CR2[Nexus 9000]
        DS1[Catalyst 9300]
        DS2[Catalyst 9300]
    end

    subgraph Branch [Branch Office]
        BR1[ISR 4451]
        BSW1[Catalyst 2960]
    end

    Internet((Internet)) --- FW1
    FW1 --- CR1 & CR2
    CR1 --- DS1 & DS2
    CR2 --- DS1 & DS2

    FW1 --- BR1
    BR1 --- BSW1
```

### Network Links and Connections

Different connection types:

```mermaid
flowchart LR
    R1[Router 1] -- 1Gbps Ethernet --- R2[Router 2]
    R1 -. OSPF Adjacency .- R2
    R1 == BGP Session === R2
    R1 -- "10.0.0.0/30" --- R2
```

### VLAN Configuration

```mermaid
flowchart TB
    subgraph VLAN10 [VLAN 10 - Management]
        M1[Management Server]
        M2[NMS]
    end

    subgraph VLAN20 [VLAN 20 - Users]
        U1[User Workstation]
        U2[User Laptop]
    end

    subgraph VLAN30 [VLAN 30 - Servers]
        S1[Application Server]
        S2[Database Server]
    end

    SW1[Core Switch] --- VLAN10
    SW1 --- VLAN20
    SW1 --- VLAN30
```

## Best Practices

1. Use consistent naming conventions
   - Devices: R1, SW1, FW1
   - Networks: NET1, VLAN10, DMZ
   - Interfaces: Gi0/1, Te1/1

2. Include relevant network information
   - IP addresses and subnets
   - Interface designations
   - Protocol information
   - VLAN assignments

3. Maintain diagram hierarchy
   - Top-level overview
   - Detailed subnet views
   - Protocol-specific diagrams

4. Use appropriate diagram types
   - Flowcharts for topology
   - Sequence diagrams for protocols
   - State diagrams for status
   - Packet diagrams for data flow
