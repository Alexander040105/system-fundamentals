# Cisco IP Phone "Configuring CM List" Fix — AJ Topology

## Topology Summary
- **Devices:** ISP Router (CME/TFTP/DHCP), ISP Switch, Amadeo Router, Amadeo Switch, Tagaytay Router, Tagaytay Switch
- **VLANs:** Amadeo Data=10 / Voice=20; Tagaytay Data=30 / Voice=40
- **IP Scheme:**
  - Amadeo Data: `10.1.10.0/24` (GW: `10.1.10.1`)
  - Amadeo Voice: `10.1.20.0/24` (GW: `10.1.20.1`)
  - Tagaytay Data: `10.0.30.0/24` (GW: `10.0.30.1`)
  - Tagaytay Voice: `10.0.40.0/24` (GW: `10.0.40.1`)
  - CME/TFTP: `10.50.99.1/32` (Loopback0 on ISP Router)
- **VoIP Design:** Single CME on ISP Router; remote sites use router-on-a-stick + `ip helper-address` to reach DHCP/TFTP at ISP Router.

---

## Problem Diagnosis

### Critical — Missing `create cnf-files`
**Root Cause:** The ISP Router `telephony-service` block is missing the `create cnf-files` command.

**Evidence:**
```
telephony-service
 max-ephones 20
 max-dn 20
 ip source-address 10.50.99.1 port 2000
 auto assign 1 to 20
```
No `create cnf-files`.

**Why it breaks:** Cisco IP Phones download a per-phone XML file (`SEP<MAC>.cnf.xml`) from the TFTP server to learn the CallManager IP. Without `create cnf-files`, those XML files do not exist. The phone gets Option 150 (`10.50.99.1`), contacts TFTP, finds no file, and hangs on **"Configuring CM List"** forever.

---

## Fix Commands

### 1. Critical Fix — ISP Router
```bash
enable
configure terminal
telephony-service
 create cnf-files
end
write memory
```

**Verification:**
```bash
show telephony-service tftp-bindings
show flash:
```
Expect `SEP<MAC>.cnf.xml` files to appear.

### 2. Major — Trunk Allow List (Amadeo & Tagaytay Switches)
`Fa0/19` on both switches is a trunk but has no explicit allowed VLAN list. Best practice / Packet Tracer reliability:

**Amadeo Switch:**
```bash
enable
configure terminal
interface FastEthernet0/19
 switchport trunk allowed vlan 1,10,20
 switchport trunk native vlan 1
 spanning-tree portfast trunk
end
write memory
```

**Tagaytay Switch:**
```bash
enable
configure terminal
interface FastEthernet0/19
 switchport trunk allowed vlan 1,30,40
 switchport trunk native vlan 1
 spanning-tree portfast trunk
end
write memory
```

### 3. Major — DHCP Option 150 on Data Pools (ISP Router)
If CDP fails, phones may DHCP from the Data VLAN. Add Option 150 to data pools:
```bash
enable
configure terminal
ip dhcp pool AMADEO_DATA
 option 150 ip 10.50.99.1
ip dhcp pool TAGAYTAY_DATA
 option 150 ip 10.50.99.1
end
write memory
```

### 4. Minor — Remove Empty RIP (Amadeo Router)
```bash
no router rip
```

### 5. Minor — Clean Phantom OSPF Networks (ISP Router)
```bash
router ospf 1
 no network 10.50.2.0 0.0.0.255 area 0
 no network 10.50.3.0 0.0.0.255 area 0
```

### 6. Minor — Set Router Hostnames
```bash
! ISP Router
hostname ISP-Router
! Amadeo Router
hostname AmadeoRouter
! Tagaytay Router
hostname TagaytayRouter
```

---

## Step-by-Step Order
1. **ISP Router:** Run Critical Fix (`create cnf-files`).
2. **Amadeo & Tagaytay Switches:** Run Major Fix #1 (trunk allow).
3. **ISP Router:** Run Major Fix #2 (DHCP data pools).
4. Apply Minor Fixes as time permits.

---

## Verification Commands

**ISP Router:**
```bash
show telephony-service all
show telephony-service tftp-bindings
show flash:
show ip dhcp binding
```

**Remote Routers:**
```bash
show ip route ospf
show ip interface brief
```

**Switches:**
```bash
show vlan brief
show interfaces trunk
show mac address-table dynamic
```

**Packet Tracer Phones (GUI):** Check that the phone shows:
- IP in Voice VLAN (`10.1.20.x` or `10.0.40.x`)
- TFTP Server: `10.50.99.1`
- CallManager IP: `10.50.99.1`
