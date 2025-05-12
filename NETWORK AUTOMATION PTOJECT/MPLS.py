from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.topology.api import get_switch, get_link, get_host, get_all_host
import networkx as nx
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet.packet import Packet
from ryu.lib.packet import arp
from ryu.lib.packet import ipv4
from ryu.lib.packet import tcp
from ryu.lib.packet import udp
from ryu.ofproto import ether
from ryu.app.ofctl.api import get_datapath

class MPLS(app_manager.RyuApp):
	OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

	def __init__(self, *args, **kwargs):
		super(MPLS, self).__init__(*args, **kwargs)
		self.topology_api_app = self
		self.net = nx.DiGraph()	 # Nx graph topology
		self.nodes = {}			 # nodes represent switches
		self.links = {}			 # links represent the connections between switches
		self.dpid_to_mac = {}	   # dpid to mac address
		self.port_to_mac = {}	   # port to mac address
		self.mac_to_port = {}	   # mac to port
		self.mac_to_dpid = {}	   # mac to dpid
		self.ip_to_mac = {}		 # ip to mac address
		self.mac_to_ip = {}		 # mac to ip address
		self.port_occupied = {}		# used ports
		self.default_priority = 100

		self.mpls_labels = {}  # (src_dpid, dst_dpid): label
		self.label_counter = 16  # MPLS labels usually start from 16
		self.datapaths = {}
		self.cached_paths = {}
		self.flag = False
		self.selected_path =[]
		self.installed_flows = {}
		self.flow_entries = []
	
	# Default function to install a flow rule
	def add_flow(self, datapath, priority, match, actions, buffer_id=None):
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser

		inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
												actions)]
		if buffer_id:
			mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
									priority=priority, match=match,
									instructions=inst)
		else:
			mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
									match=match, instructions=inst)
		datapath.send_msg(mod)
		barrier_req = parser.OFPBarrierRequest(datapath)
		datapath.send_msg(barrier_req)
		self.logger.info('')
		self.logger.info('')
		self.logger.info('###########################################')
		self.logger.info(f'[SWITCH {datapath.id}] New rule installed: '
				 f'Priority: {priority}, '
				 #f'Source MAC: {src}, '
				 #f'Destination MAC: {dst}, '
				 f'Actions: {actions}')
		self.logger.info('###########################################')


	# Event handler for switch features reply
	@set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)		
	def switch_features_handler(self, ev):
		datapath = ev.msg.datapath
		self.datapaths[datapath.id] = datapath
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser	

		# TABLE MISS ENTRY
		match = parser.OFPMatch()
		action = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
											ofproto.OFPCML_NO_BUFFER)]
		self.add_flow(datapath, 0, match, action)	

		self.logger.info('')
		self.logger.info('')
		self.logger.info('###########################################')
		self.logger.info("[SWITCH %s] Default entry -TABLE MISS- initialized", datapath.id)
		self.logger.info('###########################################')
		self.logger.info('FIRST EVENT')
		self.logger.info('###########################################')



	# Main dispatcher for packet_in events
	@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
	def _packet_in_handler(self, ev):
		msg = ev.msg
		datapath = msg.datapath
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		in_port = msg.match['in_port']
		
		pkt = packet.Packet(msg.data)
		eth = pkt.get_protocols(ethernet.ethernet)[0]

		dst = eth.dst
		src = eth.src
		dpid_src = datapath.id

		if eth.ethertype == ether_types.ETH_TYPE_LLDP: # Ignore LLDP packets
			return

		if eth.ethertype == ether_types.ETH_TYPE_IPV6: # Ignore IPv6 packets
			return
	
		# TOPOLOGY DISCOVERY------------------------------------------
		switch_list = get_switch(self.topology_api_app, None) 	# I get the list of switches  		
		switches=[switch.dp.id for switch in switch_list]
		
		for id_,s in enumerate(switches):
			for switch_port in range(1, len(switch_list[id_].ports)):  	# Set the port_occupied dictionary
				self.port_occupied.setdefault(s, {})
				self.port_occupied[s][switch_port] = 0
		self.net.add_nodes_from(switches) 

		self.logger.info('')
		self.logger.info('')
		self.logger.info('###########################################')  
		self.logger.info('NODES ADDED')								# Adding nodes to the topology
		self.logger.info('###########################################')

		links_list = get_link(self.topology_api_app, None)	  			# Get the list of links
		links=[(link.src.dpid,link.dst.dpid,{'port':link.src.port_no}) for link in links_list]
		
		
		self.net.add_edges_from(links)	  								# Adding edges to the topology
		links=[(link.dst.dpid,link.src.dpid,{'port':link.dst.port_no}) for link in links_list]
		self.net.add_edges_from(links)
		links_=[(link.dst.dpid,link.src.dpid,link.dst.port_no) for link in links_list]

		self.logger.info('')
		self.logger.info('')
		self.logger.info('###########################################')
		self.logger.info(f'LINKS ADDED: {links}')
		self.logger.info(f'NETWORK :{self.net}')
		self.logger.info('###########################################')
		for l in links_:
			self.port_occupied[l[0]][l[2]] = 1  	# If the link is referring to an host-switch, the value is set to 1

# MAC LEARNING-------------------------------------------------
		# Initializing dictionaries for mac learning
		if dpid_src not in self.mac_to_port.keys() :
			self.mac_to_port.setdefault(dpid_src, {})	  
			self.port_to_mac.setdefault(dpid_src, {})	   
			self.mac_to_port[dpid_src][src] = in_port
			self.mac_to_dpid[src] = dpid_src
			self.dpid_to_mac[dpid_src] = src
			self.port_to_mac[dpid_src][in_port] = src

		self.logger.info('')
		self.logger.info('')
		self.logger.info('###########################################')
		self.logger.info(f"MAC SEEN BY SWITCH {dpid_src}, IS FROM HOST {src}")
		self.logger.info(self.dpid_to_mac)
		self.logger.info('')
		self.logger.info('')
		self.logger.info('###########################################')
		self.logger.info(f'SWITCH {dpid_src}, RECEIVES FROM PORT {in_port} HOST {src}')
		self.logger.info(self.port_to_mac)
		self.logger.info('###########################################')

	# ARP PACKET--------------------------------------------   
		if eth.ethertype == ether_types.ETH_TYPE_ARP:						
			arp_packet = pkt.get_protocol(arp.arp)
			arp_dst_ip = arp_packet.dst_ip
			arp_src_ip = arp_packet.src_ip
			
			# 1 = ARP REQUEST
			if arp_packet.opcode == 1:
				
				if arp_dst_ip in self.ip_to_mac:	# If I know the address of the destination I reply (=2)					
					
					srcIp = arp_dst_ip
					dstIp = arp_src_ip
					srcMac = self.ip_to_mac[arp_dst_ip]

					self.logger.info('')
					self.logger.info('')
					self.logger.info('###########################################')
					self.logger.info('ARP REQUEST')
					self.logger.info('###########################################')
					self.logger.info('')
					self.logger.info('###########################################')
					self.logger.info('I KNOW MAC ADDRESS OF THE DESTINATION')
					self.logger.info(f'IP AND MAC DICTIONARY: {self.ip_to_mac}')
					self.logger.info('###########################################')

					dstMac = src
					outPort = in_port
					opcode = 2
					self.send_arp(datapath, opcode, srcMac, srcIp, dstMac, dstIp, outPort) 
					
					
				else:   # If I don't know the address of the destination I broadcast the request
					
					srcIp = arp_src_ip
					dstIp = arp_dst_ip
					srcMac = src
					dstMac = dst
					self.ip_to_mac.setdefault(srcIp, {})
					self.ip_to_mac[srcIp] = srcMac

					self.logger.info('')
					self.logger.info('')
					self.logger.info('###########################################')
					self.logger.info(f'{srcIp} SENDS ARP REQUEST')
					self.logger.info('###########################################')
					self.logger.info('')
					self.logger.info('###########################################')
					self.logger.info('I DO NOT KNOW THE MAC ADDRESS OF THE DESTINATION')
					self.logger.info(f'IP AND MAC DICTIONARY: {self.ip_to_mac}')
					self.logger.info('###########################################')
					
					self.mac_to_ip.setdefault(srcMac,{})
					self.mac_to_ip[srcMac] = srcIp
					
					opcode = 1
					for id_switch in switches:
						
						datapath_dst = get_datapath(self, id_switch)
						for po in range(1,len(self.port_occupied[id_switch])+1):
							if self.port_occupied[id_switch][po] == 0:
								outPort = po
								if id_switch == dpid_src:
									if outPort != in_port:
										self.logger.info('')
										self.logger.info('')
										self.logger.info('###########################################')
										self.logger.info(f'{id_switch} SENDS ARP REQUEST ')
										self.logger.info('###########################################')
										self.send_arp(datapath_dst, opcode, srcMac, srcIp, dstMac, dstIp, outPort)
								else:
									self.logger.info('')
									self.logger.info('')
									self.logger.info('###########################################')
									self.logger.info(f'{id_switch} SENDS ARP REQUEST')
									self.logger.info('###########################################')
									self.send_arp(datapath_dst, opcode, srcMac, srcIp, dstMac, dstIp, outPort)
	
			else:	   # 2 = ARP REPLY
				srcIp = arp_src_ip
				dstIp = arp_dst_ip
				srcMac = src
				dstMac = dst
				if arp_dst_ip in self.ip_to_mac:
					# Learn the new IP address
					self.ip_to_mac.setdefault(srcIp, {})
					self.ip_to_mac[srcIp] = srcMac

					self.logger.info('')
					self.logger.info('')
					self.logger.info('###########################################')
					self.logger.info('I KNOW THE MAC ADDRESS OF THE DESTINATION')
					self.logger.info('###########################################')

					self.logger.info(self.ip_to_mac)
					self.mac_to_ip.setdefault(srcMac,{})
					self.mac_to_ip[srcMac] = srcIp
					
					# Send the ARP reply to the destination
				opcode = 2
				outPort = self.mac_to_port[self.mac_to_dpid[dstMac]][dstMac]
				datapath_dst = get_datapath(self, self.mac_to_dpid[dstMac])
				self.send_arp(datapath_dst, opcode, srcMac, srcIp, dstMac, dstIp, outPort)

				self.logger.info('')
				self.logger.info('')
				self.logger.info('###########################################')
				self.logger.info(f'ARP REPLY SENT TO DESTINATION {dstMac}')
				self.logger.info('###########################################')
						
		# IP PACKETS-----------------------------------------------
		ip4_pkt = pkt.get_protocol(ipv4.ipv4)
		
		if ip4_pkt:
							

			src_ip = ip4_pkt.src
			dst_ip = ip4_pkt.dst
			
			src_MAC = src

			self.logger.info('')
			self.logger.info('')
			self.logger.info('###########################################')
			self.logger.info('SAVING MAC ADDRESS OF THE SRC:')
			self.logger.info('###########################################')
			self.logger.info(src_MAC)

			self.ip_to_mac.setdefault(src_ip, {})
			self.ip_to_mac[src_ip] = src_MAC
			self.logger.info(self.ip_to_mac)
			dst_MAC = dst
			proto  = str(ip4_pkt.proto)
			sport = "0"
			dport = "0" 
			if proto == "6":
				tcp_pkt = pkt.get_protocol(tcp.tcp)
				sport = str(tcp_pkt.src_port)
				dport = str(tcp_pkt.dst_port)
					
			if proto == "17":
				udp_pkt = pkt.get_protocol(udp.udp)
				sport = str(udp_pkt.src_port)
				dport = str(udp_pkt.dst_port)
			
			self.logger.info('')
			self.logger.info('')	
			self.logger.info('###########################################')
			self.logger.info(f"IP ADDRESS OF THE DESTINATION: {dst_ip}")
			self.logger.info('###########################################')
			self.logger.info(f'IP AND MAC DICTIONARY {self.ip_to_mac}')
			self.logger.info('###########################################')
			if dst_ip in self.ip_to_mac:		# If the destination IP is known

				dpid_dst = self.mac_to_dpid[self.ip_to_mac[dst_ip]]		
				
				try:
					(dst_dpid, dst_port) = self.find_destination_switch(dst_MAC) # Find the switch and port where the destination host is connected

					self.logger.info('')
					self.logger.info('')
					self.logger.info('+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
					self.logger.info(f"Destination DPID: {dst_dpid}")
					self.logger.info(f'Output port: {dst_port}')
					self.logger.info('+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')

					if dst_dpid == datapath.id: # If the destination is connected to the same switch
						out_port = dst_port
						
						self.logger.info('')
						self.logger.info('')
						self.logger.info('###########################################')
						self.logger.info('DESTINATION CONNECTED TO THE SAME SWITCH')
						self.logger.info('###########################################')

						match = parser.OFPMatch(eth_type=ether.ETH_TYPE_IP, eth_dst=dst_MAC)
						actions = [
						parser.OFPActionOutput(out_port)
						]	
						self.logger.info(f'MATCH: {match}')
						self.logger.info(f'ACTIONS: {actions}')	
						
						self.add_flow(datapath, self.default_priority, match, actions) # Install the flow rule
						out = parser.OFPPacketOut(datapath=datapath,
											  buffer_id=ofproto.OFP_NO_BUFFER,
											  in_port=in_port, actions=actions,
											  data=msg.data)
						self.flag = False
						self.get_new_priority()

					else: # If the destination is connected to another switch
						self.logger.info('')
						self.logger.info('')
						self.logger.info('###########################################')
						self.logger.info('DESTINATION CONNECTED TO ANOTHER SWITCH')
						self.logger.info('###########################################')

						out_port,next_node = self.find_next_hop_to_destination(datapath.id, dst_dpid,dst_port) # Find the next hop to reach the destination

						# Installa il flusso MPLS se la destinazione non è conosciuta direttamente
						self.logger.info('SENDING THROUGH MPLS PATH')
						#self.logger.info([datapath.id, next_node])
						#self.logger.info(f'FLOW ENTRIES:  {self.flow_entries}')
						#value =  next((t for t in self.flow_entries if t[0] == datapath.id), None)
						value = next((t for t in reversed(self.flow_entries) if t[0] == datapath.id), None)
						dpid_first, match, actions = value
						self.logger.info(f'MATCH: {match}')
						self.logger.info(f'ACTIONS: {actions}')	

						out = parser.OFPPacketOut(datapath=datapath,
											  buffer_id=ofproto.OFP_NO_BUFFER,
											  in_port=in_port, actions=actions,
											  data=msg.data)
						
					datapath.send_msg(out)  # Send the packet
					#self.logger.info(out)

					self.logger.info('')
					self.logger.info('')
					self.logger.info('###########################################')
					self.logger.info('IP PACKET SENT, KNOWING THE MAC')
					self.logger.info('###########################################')
				except:
					self.logger.info("No route between %s and %s", datapath.id, dpid_dst) # If no route, print a message
					return

			else:			# If the destination IP is unknown, broadcast the ARP request
				out_port = in_port
				opcode = 1
				self.send_arp(datapath, opcode, src_MAC, src_ip, dst_MAC, dst_ip, out_port)
				self.logger.info('')
				self.logger.info('')
				self.logger.info('###########################################')
				self.logger.info('BROADCAST MESSAGE BECAUSE I DO NOT KNOW THE MAC')
				self.logger.info('###########################################')

	# Send ARP packet
	def send_arp(self, datapath, opcode, srcMac, srcIp, dstMac, dstIp, outPort):
			
			if opcode == 1: # Arp request is 1
				targetMac = "00:00:00:00:00:00"
				targetIp = dstIp
			
			elif opcode == 2: # Arp reply is 2
				targetMac = dstMac
				targetIp = dstIp

			e = ethernet.ethernet(dstMac, srcMac, ether.ETH_TYPE_ARP)
			a = arp.arp(1, 0x0800, 6, 4, opcode, srcMac, srcIp, targetMac, targetIp)
			p = Packet()
			p.add_protocol(e)
			p.add_protocol(a)
			p.serialize()
		
			actions = [datapath.ofproto_parser.OFPActionOutput(outPort, 0)]
			out = datapath.ofproto_parser.OFPPacketOut(
					datapath=datapath,
					buffer_id=0xffffffff,
					in_port=datapath.ofproto.OFPP_CONTROLLER,
					actions=actions,
					data=p.data)
			self.logger.info('')
			self.logger.info('') 
			self.logger.info('###########################################')
			self.logger.info(f'SEND TO DESTINATION {dstMac}, {dstIp}')
			self.logger.info('###########################################')
			datapath.send_msg(out)
	
	@set_ev_cls(ofp_event.EventOFPBarrierReply, MAIN_DISPATCHER)
	def _barrier_reply_handler(self, ev):
		datapath = ev.msg.datapath
		self.logger.info(f"✅ BarrierReply received from switch {datapath.id}, xid={ev.msg.xid}")

	def get_new_label(self):
		label = self.label_counter
		self.label_counter += 1
		return label
	def get_new_priority(self):
		priority = self.default_priority
		self.default_priority -= 10
		return priority
					
	# Find the switch and port where the destination host is connected
	def find_destination_switch(self,destination_mac): 
		for host in get_all_host(self):
			if host.mac == destination_mac:
				return (host.port.dpid, host.port.port_no)
		return (None,None)
	
	# Find the next hop to reach the destination
	def find_next_hop_to_destination(self,source_id,destination_id,dst_port):
		net = nx.DiGraph()
		self.logger.info(f'ecco il nodo da cui parto: {source_id}')
		for link in get_link(self):
			net.add_edge(link.src.dpid, link.dst.dpid, port=link.src.port_no)

		if (source_id,destination_id) not in self.cached_paths and self.flag == False:
			ppp = self.find_disjoint_paths(source_id,destination_id,k=5)
			#ppp.sort(key=len)

			self.logger.info('')
			self.logger.info('')
			self.logger.info('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
			self.logger.info('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
			self.logger.info(f'DISJOINT PATHS:{ppp}')
			self.logger.info('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
			self.logger.info('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

			self.selected_path = ppp[5] # here you can choose the path
			self.cached_paths[(source_id, destination_id)] = self.selected_path
			self.logger.info(f"✅ Cached disjoint path: {self.selected_path}")
			self.flag = True

		index = self.selected_path.index(source_id)
		path = self.selected_path[index:]


		if source_id != path[0]:#need to do a for ppp to check all the paths
			self.logger.error(f"❌ Node {source_id} is not the start of the cached path {path}")
			return None
		self.logger.info(f"🚦 Installing MPLS path from {source_id} to {destination_id}: {path}")

		# Install MPLS along the path
		label = self.install_mpls_path(path, destination_id,dst_port) 
		self.mpls_labels[(source_id, path[1])] = label

		self.logger.info('')
		self.logger.info('')
		self.logger.info('###########################################')
		self.logger.info(f'PATH: {path}')
		self.logger.info('###########################################')

		first_link = net[ path[0] ][ path[1] ]
		out_port = first_link['port']

		self.logger.info('')
		self.logger.info('')
		self.logger.info('###########################################')
		self.logger.info(f"📦 MPLS path installed: {path} with label {label}")
		self.logger.info(f"➡️ Forward packet from {source_id} to {path[1]} via port {out_port}")
		self.logger.info('###########################################')
		return out_port,path[1]

	def find_disjoint_paths(self,src,dst,k=5):
		try:
			all_paths = list(nx.shortest_simple_paths(self.net, src, dst))
			self.logger.info(all_paths)
			disjoint_paths = []
			used_links = set()

			for path in all_paths:
				path_links = set((path[i], path[i + 1]) for i in range(len(path) - 1))
				self.logger.info(path_links)
            
            	# Check if the path is link-disjoint from the already selected ones
				if used_links.isdisjoint(path_links):
					disjoint_paths.append(path)
					used_links.update(path_links)
				#self.logger.info(f'disjoint_paths: {disjoint_paths}')
            
				if len(disjoint_paths) > k:
					break

			while len(disjoint_paths) < k and disjoint_paths:
				disjoint_paths.append(disjoint_paths[-1])
				#self.logger.info(f'eccoli: {disjoint_paths}')
        
			return disjoint_paths

		except nx.NetworkXNoPath:
			self.logger.info('')
			self.logger.info('')
			self.logger.info('###########################################')
			self.logger.info(f"NO PATH BETWEEN {src} AND {dst}")
			self.logger.info('###########################################')
			return []
		
			
	def install_mpls_path(self, path, dst_mac,dst_port):
		label = None
		flow_entries = []
		mpls_pushed = False

		for i in range(len(path)):
			current_dpid = path[i]
			self.logger.info('')
			self.logger.info('')
			self.logger.info('###########################################')
			self.logger.info(f'INDEX OF THE SWITCH {i}')
			self.logger.info('###########################################')

			datapath = self.datapaths[current_dpid]
			parser = datapath.ofproto_parser
			ofproto = datapath.ofproto
			match = None
			actions = None
			priority = self.default_priority 
			#out_port = self.net[current_dpid][next_dpid]['port']
			self.logger.info(f'lunghezza path: {len(path)}')

			# Path with 2 switches
			if len(path) == 2 and i == 0:
				current_dpid = path[0]
				self.logger.info(current_dpid)
				next_dpid = path[1]
				self.logger.info(next_dpid)
				match = parser.OFPMatch(eth_type=ether.ETH_TYPE_IP, eth_dst=dst_mac)
				out_port = self.net[current_dpid][next_dpid]['port']
				actions = [parser.OFPActionOutput(out_port)]

				self.logger.info("SHORT PATH (2 nodes) → IP FORWARD ONLY")

			# First switch: push MPLS label
			elif i == 0 and len(path) > 2:
				label = self.get_new_label()
				current_dpid = path[i]
				next_dpid = path[i + 1]

				self.logger.info('')
				self.logger.info('')
				self.logger.info('###########################################')
				self.logger.info('FIRST NODE')
				self.logger.info('###########################################')

				match = parser.OFPMatch(eth_type=ether.ETH_TYPE_IP, eth_dst=dst_mac)
				out_port = self.net[current_dpid][next_dpid]['port']
				actions = [
					parser.OFPActionPushMpls(ether_types.ETH_TYPE_MPLS),
					parser.OFPActionSetField(mpls_label=label),
					parser.OFPActionOutput(out_port)
				]
				mpls_pushed = True
				self.logger.info('PUSH MPLS LABEL')

        	# Last node: no rules
			elif i == len(path) - 1:
				self.logger.info('LAST NODE - NO ACTION')
				continue	
		
			# Penultimate node → POP MPLS
			elif i == len(path) - 2 and mpls_pushed:
				current_dpid = path[i]
				next_dpid = path[i + 1]

				self.logger.info('')
				self.logger.info('')
				self.logger.info('###########################################')
				self.logger.info('PENULTIMATE NODE')
				self.logger.info('###########################################')

				match = parser.OFPMatch(eth_type=ether.ETH_TYPE_MPLS, mpls_label=label)
				out_port = self.net[current_dpid][next_dpid]['port']
				actions = [
					parser.OFPActionPopMpls(ether_types.ETH_TYPE_IP),
					parser.OFPActionOutput(out_port)
				]

				self.logger.info(f'MATCH: {match}')
				self.logger.info(f'ACTIONS: {actions}')	
				self.logger.info('POP MPLS LABEL')
				mpls_pushed = False

		
			# Intermediate nodes: forward with MPLS label
			elif mpls_pushed:
				current_dpid = path[i]
				next_dpid = path[i + 1]

				self.logger.info('')
				self.logger.info('')
				self.logger.info('###########################################')
				self.logger.info('INTERMEDIATE NODE')
				self.logger.info('###########################################')

				match = parser.OFPMatch(eth_type=ether.ETH_TYPE_MPLS, mpls_label=label)
				out_port = self.net[current_dpid][next_dpid]['port']
				label = self.get_new_label()
				actions = [
					parser.OFPActionSetField(mpls_label=label),
					parser.OFPActionOutput(out_port)
				]

				self.logger.info('FORWARD MPLS LABEL')

			# Avoid redundant flows
			if match and actions:
				flow_id = out_port  # out_port is the key

				if flow_id not in self.installed_flows.get(current_dpid, set()):
					self.add_flow(datapath, priority, match, actions)
					self.installed_flows.setdefault(current_dpid, set()).add(flow_id)
					self.logger.info(f"✅ Installed flow on switch {current_dpid}")
					self.flow_entries.append((current_dpid, match, actions))
				else:
					self.logger.info(f"⏭ Skipped duplicate flow on switch {current_dpid}")
					priority = priority - 10
        
		self.logger.info('')
		self.logger.info('')
		if label:
			self.logger.info(f"✅ LSP MPLS INSTALLED: {path} WITH LABEL {label}")
		else:
			self.logger.info(f"✅ LSP IP PATH INSTALLED (NO MPLS): {path}")
		return label


	
	@set_ev_cls(ofp_event.EventOFPPortStateChange, MAIN_DISPATCHER) # Event handler for port state change, in case of broken link
	def port_states_change(self, ev):
		#self.logger.info(f"------> Call to broken link : {ev.datapath.id}, {ev.reason.}, {ev.port_no}")
		switch_dp = ev.datapath
		for switch_deleting in get_switch(self):
			delete_dp = switch_deleting.dp
			# If the switch is not the one that has lost the link and it has an id associated
			if switch_deleting != switch_dp : #and switch_dp.id in self.dpid_to_mac.keys() 
				try:
					self.logger.info("[SWITCH %s] Rules deleted", delete_dp.id)
					parser = delete_dp.ofproto_parser
					ofproto = delete_dp.ofproto
					mac = self.dpid_to_mac[switch_dp.id]
					#self.logger.info("Dest_ip_to delate %s", deleting_dp.id)
					#self.logger.info("Dest_ip_to mac to delate %s", mac)
					dst_ip = self.mac_to_ip[mac]
					#self.logger.info("Dest_ip %s", dst_ip)
					match = parser.OFPMatch(eth_type = ether.ETH_TYPE_IP, ipv4_dst = dst_ip)
					instructions = []
					flow_mod = parser.OFPFlowMod(switch_dp, 0, 0, 0, ofproto.OFPFC_DELETE, 0, 0, 1, ofproto.OFPCML_NO_BUFFER, ofproto.OFPP_ANY, ofproto.OFPG_ANY, 0, match, instructions)
					delete_dp.send_msg(flow_mod)
				except Exception as e: 
					self.logger.info("")


