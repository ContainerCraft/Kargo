# Network Engineering Documentation with Mermaid - Part 2: Advanced Network Diagramming

## Enterprise Network Diagrams

### Campus Network Layout

```mermaid
flowchart TB
    subgraph Core ["Core Layer"]
        C1["Core Switch 1<br/>N9K-C9336C-FX2"]
        C2["Core Switch 2<br/>N9K-C9336C-FX2"]
        C1 <==> C2
    end

    subgraph Distribution ["Distribution Layer"]
        D1["Dist Switch 1<br/>C9500-48Y4C"]
        D2["Dist Switch 2<br/>C9500-48Y4C"]
        D1 <==> D2
    end

    subgraph Access ["Access Layer"]
        A1["Access Switch 1<br/>C9300-48U"]
        A2["Access Switch 2<br/>C9300-48U"]
        A3["Access Switch 3<br/>C9300-48U"]
        A4["Access Switch 4<br/>C9300-48U"]
    end

    C1 --- D1 & D2
    C2 --- D1 & D2
    D1 --- A1 & A2
    D2 --- A3 & A4
```

### Data Center Topology

```mermaid
flowchart TB
    subgraph DC1 ["Primary Data Center"]
        subgraph Spine ["Spine Layer"]
            S1["Spine 1"]
            S2["Spine 2"]
        end

        subgraph Leaf ["Leaf Layer"]
            L1["Leaf 1"]
            L2["Leaf 2"]
            L3["Leaf 3"]
        end

        subgraph Servers ["Server Farm"]
            SRV1["Web Servers"]
            SRV2["App Servers"]
            SRV3["DB Servers"]
        end

        S1 --- L1 & L2 & L3
        S2 --- L1 & L2 & L3
        L1 --- SRV1
        L2 --- SRV2
        L3 --- SRV3
    end
```

### SD-WAN Architecture

```mermaid
flowchart LR
    subgraph DC ["Data Center"]
        vManage["vManage<br/>Management"]
        vSmart["vSmart<br/>Controller"]
        vBond["vBond<br/>Orchestrator"]
        vEdgeDC["vEdge Router"]
    end

    subgraph Branch1 ["Branch Office 1"]
        vEdge1["vEdge Router"]
        SW1["Branch Switch"]
    end

    subgraph Branch2 ["Branch Office 2"]
        vEdge2["vEdge Router"]
        SW2["Branch Switch"]
    end

    Internet((Internet))
    MPLS((MPLS))

    vManage --- vSmart & vBond
    vEdgeDC --- Internet & MPLS
    vEdge1 --- Internet & MPLS
    vEdge2 --- Internet & MPLS
    vEdge1 --- SW1
    vEdge2 --- SW2
```

## Protocol and Service Flows

### BGP Route Advertisement

```mermaid
sequenceDiagram
    participant AS1 as AS 65001
    participant AS2 as AS 65002
    participant AS3 as AS 65003

    AS1->>AS2: BGP Update (Prefix: 10.0.0.0/8)
    AS2->>AS1: BGP Update ACK
    AS2->>AS3: BGP Update (Prefix: 10.0.0.0/8)
    AS3->>AS2: BGP Update ACK
    Note over AS1,AS3: Route Propagation Complete
```

### High Availability Failover

```mermaid
stateDiagram-v2
    [*] --> Active: System Boot
    Active --> Standby: Failure Detected
    Standby --> Active: Primary Restored
    Active --> [*]: System Shutdown
    Standby --> [*]: System Shutdown

    note right of Active
        - Processing Traffic
        - Primary Control Plane
        - Active HSRP State
    end note

    note left of Standby
        - Monitoring Status
        - Backup Control Plane
        - Standby HSRP State
    end note
```

### Load Balancer Configuration

```mermaid
flowchart TB
    subgraph LB ["F5 Load Balancer"]
        VIP["Virtual IP<br/>10.0.1.100"]
        LB1["LTM 1"]
        LB2["LTM 2"]
    end

    subgraph WEB ["Web Server Pool"]
        W1["Web Server 1<br/>10.0.1.11"]
        W2["Web Server 2<br/>10.0.1.12"]
        W3["Web Server 3<br/>10.0.1.13"]
    end

    Client["Client"]
    Client --> VIP
    VIP --> LB1 & LB2
    LB1 --> W1 & W2 & W3
    LB2 --> W1 & W2 & W3
```

## Network Security Implementation

### Security Zones and Policy

```mermaid
flowchart TB
    subgraph Internet_Zone ["Internet Zone"]
        INT["Internet"]
    end

    subgraph DMZ ["DMZ Zone"]
        WEB["Web Servers"]
        MAIL["Mail Servers"]
        DNS["DNS Servers"]
    end

    subgraph Internal ["Internal Zone"]
        subgraph Protected ["Protected Resources"]
            AD["Active Directory"]
            DB["Databases"]
            APP["Applications"]
        end
    end

    INT <--> FW1{"Firewall<br/>Policy Engine"}
    FW1 <--> DMZ
    FW1 <--> Internal
```

### VPN Tunnel Configuration

```mermaid
flowchart LR
    subgraph Site_A ["Site A"]
        RouterA["Router A<br/>ASA 5506-X"]
        NetworkA["10.1.0.0/16"]
    end

    subgraph Site_B ["Site B"]
        RouterB["Router B<br/>ASA 5506-X"]
        NetworkB["10.2.0.0/16"]
    end

    RouterA <==>|"IPsec Tunnel<br/>IKEv2 + AES256"| RouterB
    NetworkA --- RouterA
    RouterB --- NetworkB
```

### Zero Trust Architecture

```mermaid
flowchart TB
    subgraph Access_Layer ["Access Layer"]
        Client["Client Device"]
        NAC["NAC System"]
        MFA["MFA Service"]
    end

    subgraph Security_Services ["Security Services"]
        NGFW["Next-Gen Firewall"]
        IPS["IPS/IDS"]
        CASB["CASB"]
    end

    subgraph Resources ["Protected Resources"]
        Apps["Applications"]
        Data["Data Storage"]
        Services["Cloud Services"]
    end

    Client --> NAC
    NAC --> MFA
    MFA --> NGFW
    NGFW --> IPS
    IPS --> CASB
    CASB --> Apps & Data & Services
```

### DMZ Implementation

```mermaid
flowchart TB
    Internet((Internet))

    subgraph External_FW ["External Firewall"]
        FW1["ASA 1"]
        FW2["ASA 2"]
    end

    subgraph DMZ ["DMZ Segment"]
        direction LR
        WAF["Web Application<br/>Firewall"]
        ReverseProxy["Reverse Proxy"]
        WebServers["Web Servers"]
    end

    subgraph Internal_FW ["Internal Firewall"]
        FW3["ASA 3"]
        FW4["ASA 4"]
    end

    subgraph Internal ["Internal Network"]
        AppServers["Application<br/>Servers"]
        DBServers["Database<br/>Servers"]
    end

    Internet <--> External_FW
    External_FW <--> DMZ
    DMZ <--> Internal_FW
    Internal_FW <--> Internal
```

## Advanced Configuration Examples

### EVPN VXLAN Fabric

```mermaid
flowchart TB
    subgraph Overlay ["EVPN Overlay"]
        direction TB
        Spine1["Spine 1"] <--> Spine2["Spine 2"]

        subgraph Leaf_Layer ["Leaf Layer"]
            Leaf1["Leaf 1<br/>VTEP 1"]
            Leaf2["Leaf 2<br/>VTEP 2"]
            Leaf3["Leaf 3<br/>VTEP 3"]
        end

        Spine1 <--> Leaf1 & Leaf2 & Leaf3
        Spine2 <--> Leaf1 & Leaf2 & Leaf3
    end
```
