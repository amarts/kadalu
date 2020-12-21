"""
KaDalu Operator Helper methods
"""
import os
import uuid
import json
import logging
import re
import socket

from jinja2 import Template
from kubernetes import client, config, watch

from kadalulib import execute as lib_execute, logging_setup, logf, send_analytics_tracker
from utils import execute as utils_execute, CommandError

NAMESPACE = os.environ.get("KADALU_NAMESPACE", "kadalu")
VERSION = os.environ.get("KADALU_VERSION", "latest")
K8S_DIST = os.environ.get("K8S_DIST", "kubernetes")
KUBELET_DIR = os.environ.get("KUBELET_DIR")
MANIFESTS_DIR = "/kadalu/templates"
KUBECTL_CMD = "/usr/bin/kubectl"
KADALU_CONFIG_MAP = "kadalu-info"
CSI_POD_PREFIX = "csi-"
STORAGE_CLASS_NAME_PREFIX = "kadalu."
# TODO: Add ThinArbiter and Disperse
VALID_HOSTING_VOLUME_TYPES = ["Replica1", "Replica2", "Replica3", "External"]
VOLUME_TYPE_REPLICA_1 = "Replica1"
VOLUME_TYPE_REPLICA_2 = "Replica2"
VOLUME_TYPE_REPLICA_3 = "Replica3"
VOLUME_TYPE_EXTERNAL = "External"

CREATE_CMD = "create"
APPLY_CMD = "apply"
DELETE_CMD = "delete"


def upgrade_storage_pods():
        # Add new entry in the existing config map
    configmap_data = core_v1_client.read_namespaced_config_map(
        KADALU_CONFIG_MAP, NAMESPACE)

    for key, value in configmap.data:
        if ".info" not in key:
            continue

        volname = key.replace('.info','')
        data = json.parse(value)
        
        logging.info(logf("config map", volname=volname, data=data))
        if data['type'] == VOLUME_TYPE_EXTERNAL:
            # nothing to be done for upgrade, say we are good.
            logging.debug(logf(
                "volume type external, nothing to upgrade",
                volname=volname,
                data=data))
            continue

        if data['type'] == VOLUME_TYPE_REPLICA_1:
            # No promise of high availability, upgrade
            logging.debug(logf(
                "volume type Replica1, calling upgrade",
                volname=volname,
                data=data))
            # TODO: call upgrade

        # Replica 2 and Replica 3 needs to check for self-heal
        # count 0 before going ahead with upgrade.

        # glfsheal volname --file-path=/template/file info-summary
        obj = {}
        obj["metadata"]["name"] = volname
        obj["spec"]["type"] = data.type
        obj["spec"]["volume_id"] = data["volume_id"]
        obj["spec"]["storage"] = []

        # Set Node ID for each storage device from configmap
        for val in data["bricks"]):
            idx = val["brick_index"]
            obj["spec"]["storage"][idx] = {}
            obj["spec"]["storage"][idx]["node_id"] = val["node_id"]
            obj["spec"]["storage"][idx]["path"] = val["host_brick_path"]
            obj["spec"]["storage"][idx]["node"] = val["kube_hostname"]
            obj["spec"]["storage"][idx]["device"] = val["brick_device"]
            obj["spec"]["storage"][idx]["pvc"] = val["pvc_name"]

        if data.type == VOLUME_TYPE_REPLICA_2:
            if "tie-breaker.kadalu.io" not in data.tiebreaker.node:
                obj["spec"]["tiebreaker"] = data.tiebreaker;

        # TODO: call upgrade_pods_with_heal_check() here
        deploy_server_pods(obj)
