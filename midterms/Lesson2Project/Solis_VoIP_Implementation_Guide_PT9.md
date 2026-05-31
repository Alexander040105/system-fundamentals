# Cisco Packet Tracer 9.0 Multi-Site VoIP Deployment Guide

## 1. Executive Summary
This guide adds Cisco CME-based VoIP between TAGS (Router1) and AMA (Router2) without disrupting the existing data network. It uses Cisco 2811 routers with CME, keeps Server0/Server1 as DHCP providers, avoids Voice VLAN due to Packet Tracer limitations, and configures Packet Tracer–validated dial peers for inter-site calls.

## 2. Existing Network Analysis
- TAGS LAN: 192.168.1.0/24, gateway 192.168.1.1 (Router1)
- AMA LAN: 192.168.2.0/24, gateway 192.168.2.1 (Router2)
- WAN: Router1 <-> Router0 (ISP) and Router2 <-> Router0, plus direct Router1 <-> Router2 link
- Server0 (TAGS): 192.168.1.10, DHCP service active
- Server1 (AMA): 15.6.9.10 listed, but AMA gateway is 192.168.2.1 (do not change existing addressing)
- Multiple static devices already exist on both LANs; these must remain operational

## 3. Recommended Architecture
- Use CME directly on Router1 and Router2 (Cisco 2811).
- Keep Server0 and Server1 as the only DHCP servers for their LANs.
- Add Option 150 (TFTP) to Server DHCP pools to allow phones to discover CME.
- Avoid Voice VLAN; keep phones on VLAN 1 with existing data devices.

## 4. Design Decisions and Justifications
- **DHCP ownership stays on servers**: Prevents DHCP conflicts and preserves the existing environment. Router DHCP is disabled to avoid conflicts.
- **No Voice VLAN**: Packet Tracer 2811 subinterfaces fail to retain IPs when the parent interface is in the same subnet. This blocks DHCP and CME registration. VLAN 1 is the stable, PT-safe option.
- **Dial peers kept minimal**: Packet Tracer does not support `codec`, `no vad`, or `description` in this IOS build; only `destination-pattern` and `session target` are used.

## 5. Hardware Requirements
- Router1 (TAGS): Cisco 2811 + NM-1FE-TX
- Router2 (AMA): Cisco 2811 + NM-1FE-TX
- Router0 (ISP): Router-PT-Empty (unchanged)
- Switch1: TAGS access switch (unchanged)
- AMA Switch: Cisco 2960-24TT (unchanged)
- Cisco IP Phones: 7960

## 6. Physical Topology
- Router1 Fa0/0 -> Switch1 (TAGS LAN)
- Router1 Fa0/1 -> Router0 (WAN)
- Router1 Fa1/0 -> Router2 Fa1/0 (direct WAN)
- Router2 Fa0/0 -> AMA Switch (AMA LAN)
- Router2 Fa0/1 -> Router0 (WAN)

## 7. Module Installation (NM-1FE-TX)
1. Click Router1 -> Physical tab -> Power off.
2. Insert NM-1FE-TX into empty slot.
3. Power on.
4. Repeat for Router2.

## 8. Router Replacement Procedure
1. Save the current configuration notes.
2. Replace Router1 and Router2 with Cisco 2811.
3. Reconnect all existing cables.
4. Apply the base IP configuration below.

## 9. TAGS Router Configuration
```
enable
configure terminal
hostname Router1

interface FastEthernet0/0
 description LAN_TO_SWITCH1
 ip address 192.168.1.1 255.255.255.0
 no shutdown
exit

interface FastEthernet0/1
 description WAN_TO_ISP
 ip address 10.1.1.254 255.0.0.0
 no shutdown
exit

interface FastEthernet1/0
 description WAN_TO_ROUTER2
 ip address 172.16.0.1 255.255.255.252
 no shutdown
exit

ip route 0.0.0.0 0.0.0.0 10.1.1.1
ip route 192.168.2.0 255.255.255.0 172.16.0.2 10

end
write memory
```

## 10. AMA Router Configuration
```
enable
configure terminal
hostname Router2

interface FastEthernet0/0
 description LAN_TO_AMA_SWITCH
 ip address 192.168.2.1 255.255.255.0
 no shutdown
exit

interface FastEthernet0/1
 description WAN_TO_ISP
 ip address 10.1.1.253 255.0.0.0
 no shutdown
exit

interface FastEthernet1/0
 description WAN_TO_ROUTER1
 ip address 172.16.0.2 255.255.255.252
 no shutdown
exit

ip route 0.0.0.0 0.0.0.0 10.1.1.1
ip route 192.168.1.0 255.255.255.0 172.16.0.1 10

end
write memory
```

## 11. DHCP Architecture
**Decision:** Server0 and Server1 remain the only DHCP providers. Routers do not run DHCP.

### Server0 (TAGS) DHCP
- Services -> DHCP -> Service: On
- Use the existing `serverPool` (do not remove)
- Set **Default Gateway**: 192.168.1.1
- Set **DNS Server**: 15.6.9.10 (keep as existing)
- Set **TFTP Server**: 192.168.1.1 (Option 150)

### Server1 (AMA) DHCP
- Services -> DHCP -> Service: On
- Use the existing `serverPool` (do not remove)
- Set **Default Gateway**: 192.168.2.1
- Set **DNS Server**: 15.6.9.10 (keep as existing)
- Set **TFTP Server**: 192.168.2.1 (Option 150)

### Router DHCP Status Check
```
show running-config | section dhcp
```
Expected: no `ip dhcp pool` entries on Router1 or Router2.

## 12. CME Configuration
### Router1 (TAGS)
```
enable
configure terminal

telephony-service
 max-ephones 10
 max-dn 20
 ip source-address 192.168.1.1 port 2000
 auto assign 1 to 20
 create cnf-files
exit

ephone-dn 1
 number 1001
exit

ephone-dn 2
 number 1002
exit

ephone-dn 3
 number 1003
exit

ephone-dn 4
 number 1004
exit

end
write memory
```

### Router2 (AMA)
```
enable
configure terminal

telephony-service
 max-ephones 10
 max-dn 20
 ip source-address 192.168.2.1 port 2000
 auto assign 1 to 20
 create cnf-files
exit

ephone-dn 1
 number 2001
exit

ephone-dn 2
 number 2002
exit

ephone-dn 3
 number 2003
exit

ephone-dn 4
 number 2004
exit

end
write memory
```

## 13. Dial Peer Configuration
### Router1 (to AMA)
```
enable
configure terminal

dial-peer voice 200 voip
 destination-pattern 2...
 session target ipv4:172.16.0.2
exit

end
write memory
```

### Router2 (to TAGS)
```
enable
configure terminal

dial-peer voice 100 voip
 destination-pattern 1...
 session target ipv4:172.16.0.1
exit

end
write memory
```

## 14. Switch Configuration
### TAGS Switch (Switch1)
Use VLAN 1 only. Do not configure voice VLAN.
```
enable
configure terminal

interface FastEthernet0/16
 description TAGS_IP_PHONE_1
 switchport mode access
 switchport access vlan 1
 spanning-tree portfast
exit

interface FastEthernet0/17
 description TAGS_IP_PHONE_2
 switchport mode access
 switchport access vlan 1
 spanning-tree portfast
exit

interface FastEthernet0/18
 description TAGS_IP_PHONE_3
 switchport mode access
 switchport access vlan 1
 spanning-tree portfast
exit

interface FastEthernet0/19
 description UPLINK_TO_ROUTER1
 switchport mode access
 switchport access vlan 1
exit

end
write memory
```

### AMA Switch (2960)
```
enable
configure terminal

interface FastEthernet0/17
 description AMA_IP_PHONE_1
 switchport mode access
 switchport access vlan 1
 spanning-tree portfast
exit

interface FastEthernet0/18
 description AMA_IP_PHONE_2
 switchport mode access
 switchport access vlan 1
 spanning-tree portfast
exit

interface FastEthernet0/19
 description AMA_IP_PHONE_3
 switchport mode access
 switchport access vlan 1
 spanning-tree portfast
exit

interface FastEthernet0/20
 description UPLINK_TO_ROUTER2
 switchport mode access
 switchport access vlan 1
exit

end
write memory
```

## 15. Phone Registration Procedure
1. Power on all IP Phones.
2. Wait for DHCP to complete (phones should obtain 192.168.1.x or 192.168.2.x).
3. On the switch, find each phone MAC:
   ```
   show mac address-table
   ```
4. On each router, bind MACs to ephones:

### Router1 (TAGS)
```
configure terminal

ephone 1
 mac-address XXXX.XXXX.XXXX
 type 7960
 button 1:1
exit

ephone 2
 mac-address XXXX.XXXX.XXXX
 type 7960
 button 1:2
exit

ephone 3
 mac-address XXXX.XXXX.XXXX
 type 7960
 button 1:3
exit

ephone 4
 mac-address XXXX.XXXX.XXXX
 type 7960
 button 1:4
exit

end
write memory
```

### Router2 (AMA)
```
configure terminal

ephone 1
 mac-address XXXX.XXXX.XXXX
 type 7960
 button 1:1
exit

ephone 2
 mac-address XXXX.XXXX.XXXX
 type 7960
 button 1:2
exit

ephone 3
 mac-address XXXX.XXXX.XXXX
 type 7960
 button 1:3
exit

ephone 4
 mac-address XXXX.XXXX.XXXX
 type 7960
 button 1:4
exit

end
write memory
```

## 16. Verification Commands
```
show ip interface brief
show ip route
ping 172.16.0.2
ping 192.168.2.1
show running-config | section telephony
show running-config | section ephone
show ephone registered
show running-config | section dial-peer
show ip dhcp binding
show mac address-table
```

## 17. Troubleshooting Guide
- **Phones stuck on Configuring IP**: Verify Server DHCP is ON and has TFTP Server set to router IP.
- **No DHCP leases on router**: Expected, since DHCP is server-based. Check server lease table instead.
- **Need to configure ephone mac address**: Set `mac-address` before `button` in each ephone.
- **Dial peer commands rejected**: Remove unsupported lines (`codec`, `no vad`, `description`).
- **Voice VLAN breaks DHCP**: Remove voice VLAN and keep access VLAN 1.
- **Phone MAC changes after delete/re-add**: Re-run `show mac address-table` and update ephone MACs.

## 18. Packet Tracer 9.0 Caveats
- Cisco 7960 Config tab lacks IP/TFTP fields; DHCP + Option 150 is required.
- Router subinterfaces may not retain IPs if parent interface is in same subnet.
- `show dial-peer voice summary` not supported.
- Dial-peer `description`, `codec g711ulaw`, `no vad` often unsupported.
- `clear ip dhcp binding *` unsupported; remove/recreate pools if needed.
- Clock warning on `create cnf-files` is harmless.

## 19. End-to-End Testing Procedure
1. Verify both routers can ping each other over 172.16.0.0/30.
2. Confirm phones have IPs from Server DHCP.
3. Confirm `show ephone registered` on both routers.
4. From TAGS phone 1001, dial 2001.
5. From AMA phone 2001, dial 1001.
6. Validate two-way audio for both directions.

## 20. Expected Successful Results
- All phones receive DHCP addresses and TFTP info automatically.
- Router1 registers extensions 1001–1004.
- Router2 registers extensions 2001–2004.
- Dialing 2XXX from TAGS reaches AMA.
- Dialing 1XXX from AMA reaches TAGS.
- All existing LAN and WAN services continue to function without interruption.
