#
# Copyright (c) 2014, Arista Networks, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
#   Neither the name of Arista Networks nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ARISTA NETWORKS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""Module for working with EOS static routes

The staticroute resource provides configuration management of static
route resources on an EOS node. It provides the following class
implementations:

    * StaticRoute - Configure static routes in EOS

StaticRoute Attributes:
    ip_dest (string): The ip address of the destination in the
        form of A.B.C.D/E
    next_hop (string): The next hop interface or ip address
    next_hop_ip (string): The next hop address on destination interface
    distance (int): Administrative distance for this route
    tag (int): Route tag
    route_name (string): Route name

Notes:
    The 'default' prefix function of the 'ip route' command,
    'default ip route ...', currently equivalent to the 'no ip route ...'
    command.
"""

import re

from pyeapi.api import EntityCollection

# Create the regular expression for matching ip route strings
# ROUTES_RE = re.compile(r'''(?<=^ip\sroute\s)
#                            (?P<ip_dest>[^\s]+)\s
#                            (?P<next_hop>[^\s$]+)
#                            [\s|$]{0,1}(?P<next_hop_ip>\d+\.\d+\.\d+\.\d+)?
#                            [\s|$](?P<distance>\d+)
#                            [\s|$]{1}(?:tag\s(?P<tag>\d+))?
#                            [\s|$]{1}(?:name\s(?P<name>.+))?
#                         ''', re.X)
# Define the regex to match ip route lines (by lines in regex):
#   'ip route' header
#   ip_dest
#   next_hop
#   next_hop_ip
#   distance
#   tag
#   name
ROUTES_RE = re.compile(r'(?<=^ip route)'
                       r' (\d+\.\d+\.\d+\.\d+\/\d+)'
                       r' (\d+\.\d+\.\d+\.\d+|\S+)'
                       r'(?: (\d+\.\d+\.\d+\.\d+))?'
                       r' (\d+)'
                       r'(?: tag (\d+))?'
                       r'(?: name (\S+))?', re.M)
# (?<=^ip route )(\d+\.\d+\.\d+\.\d+\/\d+) (\d+\.\d+\.\d+\.\d+|[^\s]+)(?: (\d+\.\d+\.\d+\.\d+))?( \d+)(?: tag (\d+))?(?: name (\S+))?

ROUTE_ID = "%s--%s--%s"

class StaticRoute(EntityCollection):
    """The StaticRoute class provides a configuration instance
    for working with static routes

    """

    def __str__(self):
        return 'StaticRoute'

    def get(self, ip_dest, next_hop, distance):
        """Retrieves the ip route information for the route specified
            by the ip_dest, next_hop, and distance parameters

        Args:
            ip_dest (string): The ip address of the destination in the
                form of A.B.C.D/E
            next_hop (string): The next hop interface or ip address
            distance (int): Administrative distance for this route

        Returns:
            dict: An ip route dict object

            If the unique route specified by the ip_dest, next_hop, and
            distance does not exist, then None is returned.
        """

        # If distance is None, then set to 1 to match what EOS will
        # do when distance is not specified.
        if distance is None:
            distance = 1

        # Make the unique route_id for the requested route
        route_id = ROUTE_ID % (ip_dest, next_hop, distance)

        # Return the route configuration if found, or return None
        return self.getall().get(route_id)

    def getall(self):
        """Return all ip routes configured on the switch as a resource dict

        Returns:
            dict: A dict of unique ip route names with a nested route
                dict object. The unique name is built with the ip destination,
                next hop, and distance values for the route.
        """

        # Find all the ip routes in the config
        matches = ROUTES_RE.findall(self.config)

        # Parse the routes and add them to the routes dict
        routes = dict()
        for match in matches:
            # Set the route dict to the returned values, replacing
            # empty strings with None
            route = dict()
            route['ip_dest'] = match[0]
            route['next_hop'] = match[1]
            route['next_hop_ip'] = None if match[2] is '' else match[2]
            route['distance'] = match[3]
            route['tag'] = None if match[4] is '' else match[4]
            route['route_name'] = None if match[5] is '' else match[5]

            # Build a unique route_id from the ip_dest, next_hop, and distance
            route_id = ROUTE_ID % \
                (route['ip_dest'], route['next_hop'], route['distance'])

            # Update the routes dict
            routes.update({route_id: route})

        return routes

    def create(self, ip_dest, next_hop, next_hop_ip=None,
               distance=None, tag=None, route_name=None):
        """Create a static route

        Args:
            ip_dest (string): The ip address of the destination in the
                form of A.B.C.D/E
            next_hop (string): The next hop interface or ip address
            next_hop_ip (string): The next hop address on destination
                interface
            distance (int): Administrative distance for this route
            tag (int): Route tag
            route_name (string): Route name

        Returns:
            True if the operation succeeds, otherwise False.
        """

        # Call _set_route with the delete flag set to True
        return self._set_route(ip_dest, next_hop, next_hop_ip=next_hop_ip,
                               distance=distance, tag=tag,
                               route_name=route_name)

    def delete(self, ip_dest, next_hop, next_hop_ip=None,
               distance=None, tag=None, route_name=None):
        """Delete a static route

        Args:
            ip_dest (string): The ip address of the destination in the
                form of A.B.C.D/E
            next_hop (string): The next hop interface or ip address
            next_hop_ip (string): The next hop address on destination
                interface
            distance (int): Administrative distance for this route
            tag (int): Route tag
            route_name (string): Route name

        Returns:
            True if the operation succeeds, otherwise False.
        """

        # Call _set_route with the delete flag set to True
        return self._set_route(ip_dest, next_hop, next_hop_ip=next_hop_ip,
                               distance=distance, tag=tag,
                               route_name=route_name, delete=True)

    def default(self, ip_dest, next_hop, next_hop_ip=None,
                distance=None, tag=None, route_name=None):
        """Set a static route to default (i.e. delete the matching route)

        Args:
            ip_dest (string): The ip address of the destination in the
                form of A.B.C.D/E
            next_hop (string): The next hop interface or ip address
            next_hop_ip (string): The next hop address on destination
                interface
            distance (int): Administrative distance for this route
            tag (int): Route tag
            route_name (string): Route name

        Returns:
            True if the operation succeeds, otherwise False.
        """

        # Call _set_route with the delete flag set to True
        return self._set_route(ip_dest, next_hop, next_hop_ip=next_hop_ip,
                               distance=distance, tag=tag,
                               route_name=route_name, default=True)

    def _build_commands(self, ip_dest, next_hop, next_hop_ip=None,
                        distance=None, tag=None, route_name=None):
        """Build the EOS command string for ip route interactions.

        Args:
            ip_dest (string): The ip address of the destination in the
                form of A.B.C.D/E
            next_hop (string): The next hop interface or ip address
            next_hop_ip (string): The next hop address on destination
                interface
            distance (int): Administrative distance for this route
            tag (int): Route tag
            route_name (string): Route name

        Returns the ip route command string to be sent to the switch for
        the given set of parameters.
        """

        commands = "ip route %s %s" % (ip_dest, next_hop)

        if next_hop_ip is not None:
            commands += " %s" % next_hop_ip
        if distance is not None:
            commands += " %s" % distance
        if tag is not None:
            commands += " tag %s" % tag
        if route_name is not None:
            commands += " name %s" % route_name

        return commands

    def _set_route(self, ip_dest, next_hop, next_hop_ip=None,
                   distance=None, tag=None, route_name=None,
                   delete=False, default=False):
        """Configure a static route

        Args:
            ip_dest (string): The ip address of the destination in the
                form of A.B.C.D/E
            next_hop (string): The next hop interface or ip address
            next_hop_ip (string): The next hop address on destination
                interface
            distance (int): Administrative distance for this route
            tag (int): Route tag
            route_name (string): Route name
            delete (boolean): If true, deletes the specified route
                instead of creating or setting values for the route

        Returns:
            True if the operation succeeds, otherwise False.
        """

        # Build the route string based on the parameters given
        commands = self._build_commands(ip_dest, next_hop,
                                        next_hop_ip=next_hop_ip,
                                        distance=distance,
                                        tag=tag,
                                        route_name=route_name)

        # Prefix with 'no' if delete is set
        if delete:
            commands = "no " + commands
        # Or with 'default' if default is setting
        else:
            if default:
                commands = "default " + commands

        return self.configure(commands)


def instance(node):
    """Returns an instance of Vlans

    This method will create and return an instance of the Vlans object passing
    the value of API to the object.  The instance method is required for the
    resource to be autoloaded by the Node object

    Args:
        node (Node): The node argument passes an instance of Node to the
            resource
    """
    return StaticRoute(node)
