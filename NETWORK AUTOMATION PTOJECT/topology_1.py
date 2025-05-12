"""Custom topology example

Goal: create a ring network with 3 switches and 2 hosts per switch

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""

from mininet.topo import Topo

class MyTopo( Topo ):
    "Simple topology example."

    def build( self ):
        "Create custom topo."

        # Add hosts------------------------------------------
        # self.addHost(name, cpu=f): specify a fraction of overall 
        # system CPU resources which will be allocated to the virtual host

        h1 = self.addHost( 'h1' )
        h2 = self.addHost( 'h2' )

        # Add switches---------------------------------------
        s1 = self.addSwitch( 's1' )
        s2 = self.addSwitch( 's2' )
        s3 = self.addSwitch( 's3' )

        s4 = self.addSwitch( 's4' )
        s5 = self.addSwitch( 's5' )
        s6 = self.addSwitch( 's6' )
        s7 = self.addSwitch( 's7' )

        s8 = self.addSwitch( 's8' )
        s9 = self.addSwitch( 's9' )
        s10 = self.addSwitch( 's10' )
        s11 = self.addSwitch( 's11' )
        s12 = self.addSwitch( 's12' )

        s13 = self.addSwitch( 's13' )
        s14 = self.addSwitch( 's14' )
        s15 = self.addSwitch( 's15' )
        s16 = self.addSwitch( 's16' )
        s17 = self.addSwitch( 's17' )
        s18 = self.addSwitch( 's18' )

        s19 = self.addSwitch( 's19' )





        # Add links-----------------------------------------
        #
        # Optional parameters -> bw=10, delay='5ms', loss=2, max_queue_size=1000, use_htb=True
        #
        # adds a bidirectional link with bandwidth, delay and loss characteristics, 
        # with a maximum queue size of 1000 packets using the Hierarchical Token Bucket rate limiter 
        # and netem delay/loss emulator. The parameter bw is expressed as a number in Mbit; 
        # delay is expressed as a string with units in place (e.g. '5ms', '100us', '1s'); 
        # loss is expressed as a percentage (between 0 and 100); and max_queue_size is expressed in packets.
        
        ###
        self.addLink( h1, s1 )
        self.addLink( h2, s2 )

        #primary path
        self.addLink( s1, s2 )

        #secondary path
        self.addLink( s1, s3 )
        self.addLink( s3, s2 )

        #third path
        self.addLink( s1, s4 )
        self.addLink( s4, s5 )
        self.addLink( s5, s2 )

        #fourth path
        self.addLink( s1, s6 )
        self.addLink( s6, s7 )
        self.addLink( s7, s8 )
        self.addLink( s8, s2 )

        #fifth path
        self.addLink( s1, s9 )
        self.addLink( s9, s10 )
        self.addLink( s10, s11 )
        self.addLink( s11, s12 )
        self.addLink( s12, s13 )
        self.addLink( s13, s2 )

        #sixth path
        self.addLink(s1, s14)
        self.addLink(s14, s15)
        self.addLink(s15, s16)
        self.addLink(s16, s17)
        self.addLink(s17, s18)
        self.addLink(s18, s19)
        self.addLink(s19, s2)

 


topos = { 'mytopo': ( lambda: MyTopo() ) }


