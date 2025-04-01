# Network Engineering Documentation with Mermaid - Part 3: Real-World Network Documentation

## Network Documentation Templates

### Physical Network Topology Template

```mermaid
flowchart TB
    subgraph WAN ["WAN Connectivity"]
        ISP1["ISP1 - AT&T<br/>1Gbps"]
        ISP2["ISP2 - Verizon<br/>1Gbps"]
    end

    subgraph DC ["Primary Data Center - DAL01"]
        direction TB
        subgraph Edge ["Edge Layer"]
            RTR1["RTR-DAL01-ED01<br/>ASR1002-X"]
            RTR2["RTR-DAL01-ED02<br/>ASR1002-X"]
        end

        subgraph Core ["Core Layer"]
            COR1["COR-DAL01-01<br/>Nexus 9504"]
            COR2["COR-DAL01-02<br/>Nexus 9504"]
        end

        subgraph Distribution ["Distribution Layer"]
            DST1["DST-DAL01-01<br/>Catalyst 9500"]
            DST2["DST-DAL01-02<br/>Catalyst 9500"]
        end

        subgraph Access ["Access Layer"]
            ACC1["ACC-DAL01-01<br/>Catalyst 9300"]
            ACC2["ACC-DAL01-02<br/>Catalyst 9300"]
            ACC3["ACC-DAL01-03<br/>Catalyst 9300"]
            ACC4["ACC-DAL01-04<br/>Catalyst 9300"]
        end
    end

    ISP1 --- RTR1
    ISP2 --- RTR2
    RTR1 & RTR2 --- COR1 & COR2
    COR1 & COR2 --- DST1 & DST2
    DST1 --- ACC1 & ACC2
    DST2 --- ACC3 & ACC4
```

### Logical Network Layout

```mermaid
flowchart TB
    subgraph Network_Zones ["Network Segmentation"]
        subgraph External ["External Zone - 172.16.0.0/16"]
            DMZ["DMZ Services<br/>VLAN 100"]
            Partners["Partner Access<br/>VLAN 110"]
        end

        subgraph Internal ["Internal Zone - 10.0.0.0/8"]
            Corp["Corporate<br/>VLAN 200-299"]
            Production["Production<br/>VLAN 300-399"]
            Management["Management<br/>VLAN 999"]
        end

        subgraph Restricted ["Restricted Zone - 192.168.0.0/16"]
            Finance["Financial Services<br/>VLAN 400"]
            HR["HR Systems<br/>VLAN 410"]
        end
    end
```

### Service Dependencies Map

```mermaid
flowchart LR
    subgraph Frontend ["Frontend Services"]
        Web["Web Servers<br/>VLAN 100"]
        CDN["CDN Services<br/>VLAN 101"]
    end

    subgraph Application ["Application Layer"]
        API["API Gateway<br/>VLAN 200"]
        Cache["Redis Cache<br/>VLAN 201"]
        Queue["Message Queue<br/>VLAN 202"]
    end

    subgraph Backend ["Backend Services"]
        DB["Database Cluster<br/>VLAN 300"]
        Storage["Storage Array<br/>VLAN 301"]
    end

    Web --> API
    API --> Cache & Queue
    API & Queue --> DB
    DB --> Storage
```

## Case Studies

### Enterprise Campus Network Implementation

```mermaid
flowchart TB
    subgraph Internet_Edge ["Internet Edge"]
        FW1["FW-EDGE-01<br/>Palo Alto 5260"]
        FW2["FW-EDGE-02<br/>Palo Alto 5260"]
    end

    subgraph Campus_Core ["Campus Core"]
        direction LR
        Core1["CORE-01<br/>Nexus 9504"]
        Core2["CORE-02<br/>Nexus 9504"]
        Core1 <==>|"vPC Peer Link"| Core2
    end

    subgraph Building_A ["Building A"]
        DST_A1["DST-A-01"]
        DST_A2["DST-A-02"]
        ACC_A1["ACC-A-01"]
        ACC_A2["ACC-A-02"]
    end

    subgraph Building_B ["Building B"]
        DST_B1["DST-B-01"]
        DST_B2["DST-B-02"]
        ACC_B1["ACC-B-01"]
        ACC_B2["ACC-B-02"]
    end

    FW1 & FW2 --- Core1 & Core2
    Core1 & Core2 --- DST_A1 & DST_A2
    Core1 & Core2 --- DST_B1 & DST_B2
    DST_A1 & DST_A2 --- ACC_A1 & ACC_A2
    DST_B1 & DST_B2 --- ACC_B1 & ACC_B2
```

### Multi-Site Data Center Connectivity

```mermaid
flowchart TB
    subgraph DC1 ["Primary DC - DAL01"]
        Core1["Core Layer"]
        Fabric1["VXLAN Fabric"]
    end

    subgraph DC2 ["Secondary DC - PHX01"]
        Core2["Core Layer"]
        Fabric2["VXLAN Fabric"]
    end

    subgraph DCI ["Data Center Interconnect"]
        direction LR
        DWDM1["DWDM-DAL01"]
        DWDM2["DWDM-PHX01"]
    end

    Core1 --- DWDM1
    Core2 --- DWDM2
    DWDM1 ===|"100G Lambda"| DWDM2
```

### Industrial Network Segmentation

```mermaid
flowchart TB
    subgraph Enterprise ["Enterprise Network"]
        Corp["Corporate Network"]
        IT["IT Systems"]
    end

    subgraph Industrial ["Industrial Zone"]
        direction TB
        FW_IND["Industrial Firewall"]

        subgraph Level3 ["Level 3 - Site Operations"]
            MES["MES"]
            Historian["Historian"]
        end

        subgraph Level2 ["Level 2 - Process Network"]
            HMI["HMI"]
            SCADA["SCADA"]
        end

        subgraph Level1 ["Level 1 - Control Network"]
            PLC["PLCs"]
            RTU["RTUs"]
        end

        subgraph Level0 ["Level 0 - Field Network"]
            Sensors["Sensors"]
            Actuators["Actuators"]
        end
    end

    Corp --- FW_IND
    FW_IND --- Level3
    Level3 --- Level2
    Level2 --- Level1
    Level1 --- Level0
```

## Documentation Standards and Best Practices

### Naming Convention Standards

```mermaid
flowchart LR
    subgraph Naming_Convention ["Device Naming Standard"]
        direction TB
        Format["FORMAT:<br/>TYPE-SITE-ROLE-NUM"]

        Examples["EXAMPLES:<br/>RTR-DAL01-CORE-01<br/>SW-PHX02-ACC-04<br/>FW-NYC03-DMZ-02"]
    end
```

### Version Control Integration

```mermaid
flowchart LR
    subgraph Version_Control ["Documentation Workflow"]
        direction TB
        Edit["Local Edit"]
        Review["Peer Review"]
        Merge["Merge to Main"]
        Deploy["Auto Deploy"]
    end

    Edit --> Review
    Review --> Merge
    Merge --> Deploy
```

### Documentation Style Guidelines

1. Diagram Hierarchy
   - L1: Network Overview
   - L2: Site-Specific Details
   - L3: Component Details

2. Color Coding Standards
   ```mermaid
   flowchart LR
       classDef production fill:#e6ffe6,stroke:#006600
       classDef staging fill:#e6f3ff,stroke:#0066cc
       classDef development fill:#ffe6e6,stroke:#cc0000

       P[Production]:::production
       S[Staging]:::staging
       D[Development]:::development
   ```

3. Link Type Representation
   ```mermaid
   flowchart LR
       A[Device A] === B[Device B]
       C[Device C] --- D[Device D]
       E[Device E] -.- F[Device F]

       Note["=== High Speed Link<br/>--- Standard Link<br/>-.- Backup Link"]
   ```

4. Required Documentation Elements
   - Device Information
   - IP Addressing
   - VLAN Assignments
   - Physical Connections
   - Logical Topology
   - Security Zones
   - Change History
