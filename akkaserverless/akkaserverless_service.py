"""
Copyright 2020 Lightbend Inc.
Licensed under the Apache License, Version 2.0.
"""
import logging
import multiprocessing
import os
from concurrent import futures
from dataclasses import dataclass, field
from typing import List, Optional

import grpc

from akkaserverless.akkaserverless.component.action.action_pb2_grpc import add_ActionsServicer_to_server
from akkaserverless.action_protocol_entity import Action
from akkaserverless.action_servicer import AkkaServerlessActionProtocolServicer
from akkaserverless.discovery_servicer import AkkaServerlessEntityDiscoveryServicer
from akkaserverless.akkaserverless.protocol.discovery_pb2_grpc import add_DiscoveryServicer_to_server
from akkaserverless.event_sourced_entity import EventSourcedEntity
from akkaserverless.akkaserverless.component.eventsourcedentity.event_sourced_entity_pb2_grpc import add_EventSourcedEntitiesServicer_to_server
from akkaserverless.eventsourced_servicer import AkkaServerlessEventSourcedServicer

# from grpc_reflection.v1alpha import reflection


@dataclass
class AkkaServerlessService:
    logging.basicConfig(
        format="%(asctime)s - %(filename)s - %(levelname)s: %(message)s",
        level=logging.DEBUG,
    )
    logging.root.setLevel(logging.DEBUG)

    __address: str = ""
    __host = "0.0.0.0"
    __port = "8080"
    __workers = multiprocessing.cpu_count()
    __event_sourced_entities: List[EventSourcedEntity] = field(default_factory=list)
    __action_protocol_entities: List[Action] = field(default_factory=list)

    def host(self, address: str):
        """Set the address of the network Host.
        Default Address is 127.0.0.1.
        """
        self.__host = address
        return self

    def port(self, port: str):
        """Set the address of the network Port.
        Default Port is 8080.
        """
        self.__port = port
        return self

    def max_workers(self, workers: Optional[int] = multiprocessing.cpu_count()):
        """Set the gRPC Server number of Workers.
        Default is equal to the number of CPU Cores in the machine.
        """
        self.__workers = workers
        return self

    def register_event_sourced_entity(self, entity: EventSourcedEntity):
        """Registry the user EventSourced entity."""
        self.__event_sourced_entities.append(entity)
        return self

    def register_action_entity(self, entity: Action):
        """Registry the user Stateless Function entity."""
        self.__action_protocol_entities.append(entity)
        return self

    def start(self):
        """Start the user function and gRPC Server."""

        self.__address = "{}:{}".format(
            os.environ.get("HOST", self.__host), os.environ.get("PORT", self.__port)
        )

        server = grpc.server(futures.ThreadPoolExecutor(max_workers=self.__workers))

        # event sourced
        
        d = AkkaServerlessEntityDiscoveryServicer(self.__event_sourced_entities, self.__action_protocol_entities)
        print(d)
        add_DiscoveryServicer_to_server(
            AkkaServerlessEntityDiscoveryServicer(
                self.__event_sourced_entities, self.__action_protocol_entities
            ),
            server,
        )
        print(server)
        '''
        add_EntityDiscoveryServicer_to_server(
            CloudStateEntityDiscoveryServicer(
                self.__event_sourced_entities, self.__action_protocol_entities
            ),
            server,
        )
        '''
        add_EventSourcedEntitiesServicer_to_server(
            AkkaServerlessEventSourcedServicer(self.__event_sourced_entities), server
        )
        
        add_ActionsServicer_to_server(
            AkkaServerlessActionProtocolServicer(self.__action_protocol_entities),
            server,
        )
        
        logging.info("Starting Cloudstate on address %s", self.__address)
        try:
            server.add_insecure_port(self.__address)
            server.start()
            server.wait_for_termination()
        except IOError as e:
            logging.error("Error on start Cloudstate %s", e.__cause__)
        
        return server
