# This script will generate a file to append to an ASA configuration for routing the MS Office 365 addresses to a alerternative interface
# Like an SDWAN lite like function 

import json
import os
import urllib.request
import uuid
import socket
import struct

# required inputs
interface=input('Name of the outgoing interface for office365 ex:outside2: ') or 'outside2'
gateway=input('Enter the ip address of the gateway ex:1.1.1.1: ') or '1.1.1.1'
trackedip=input('Enter an ip address for route tracking ex:8.8.8.8: ') or '8.8.8.8'

#convert cidr to netmask
def cidr_to_netmask(cidr):
	network, net_bits = cidr.split('/')
	host_bits = 32 - int(net_bits)
	netmask = socket.inet_ntoa(struct.pack('!I', (1 << 32) - (1 << host_bits)))
	return network, netmask

#get Microsoft Json File
def webApiGet(methodName, instanceName, clientRequestId):
	ws = "https://endpoints.office.com"
	requestPath = ws + '/' + methodName + '/' + instanceName + '?clientRequestId=' + clientRequestId
	request = urllib.request.Request(requestPath)
	with urllib.request.urlopen(request) as response:
		return json.loads(response.read().decode())

clientRequestId = str(uuid.uuid4())
endpointSets = webApiGet('endpoints', 'Worldwide', clientRequestId)

#get the ip adresses
flatIps = []
for endpointSet in endpointSets:
	if endpointSet['category'] in ('Optimize', 'Allow'):
		ips = endpointSet['ips'] if 'ips' in endpointSet else []
		ip4s = [ip for ip in ips if '.' in ip]
		flatIps.extend([(ip) for ip in ip4s])

#generate configuration append file
max=str(flatIps).count(',')
routes = 'conf t\ntrack 123 rtr 123 reachability\nsla monitor 123\ntype echo protocol ipIcmpEcho '+ str(trackedip) + ' interface outside2\nsla monitor schedule 123 life forever start-time now\n'
i = 0

while i <= max :
	subnet=(cidr_to_netmask(flatIps[i]))
	routes = routes + 'route '+ interface +' '+ (subnet[0]) +' '+ (subnet[1]) + ' ' + gateway + ' track 123' +'\n'
	i += 1

print(('\nThe configuration to append in your ASA is written in the file route-add-to-asa-for-office365.txt\n'))
file = open('route-add-to-asa-for-office365.txt', "w")
file.write(routes)
file.close()
