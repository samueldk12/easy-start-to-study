"""
NetworkInspector Service
Provides deep visibility into active containers, host/container port allocations,
inter-service communication links ("quem se liga a quem"), and Docker network topology.
"""

import asyncio
import os
import json
import re
import socket
from typing import List, Dict, Any, Optional, Set
from studio.services.catalog import get_tool_by_id
from studio.services.topology_graph import RELATIONSHIPS, CATEGORY_COLORS
from studio.services.project_store import ProjectStore


def is_port_bound(port: int) -> bool:
    """Checks if a TCP port is currently bound/listening on localhost."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.2)
            return s.connect_ex(('127.0.0.1', port)) == 0
    except Exception:
        return False


class NetworkInspector:

    @staticmethod
    def _parse_labels(labels_str: str) -> Dict[str, str]:
        """Parses docker label string key1=val1,key2=val2 into a dict."""
        labels = {}
        if not labels_str:
            return labels
        for part in labels_str.split(","):
            if "=" in part:
                k, v = part.split("=", 1)
                labels[k.strip()] = v.strip()
        return labels

    @staticmethod
    def _parse_ports(ports_str: str) -> List[Dict[str, Any]]:
        """Parses raw docker port string into structured port objects."""
        ports = []
        if not ports_str:
            return ports

        # Examples: "0.0.0.0:8090->8081/tcp, [::]:8090->8081/tcp", "9000-9001/tcp"
        seen_pairs = set()
        for item in ports_str.split(","):
            item = item.strip()
            if not item:
                continue
            
            # Match 0.0.0.0:HOST->CONTAINER/PROTO or [::]:HOST->CONTAINER/PROTO
            match = re.search(r'(?:[\d\.]+|\[::\]):(\d+)->(\d+)/?(\w+)?', item)
            if match:
                host_port = int(match.group(1))
                container_port = int(match.group(2))
                proto = match.group(3) or "tcp"
                pair_key = (host_port, container_port, proto)
                if pair_key not in seen_pairs:
                    seen_pairs.add(pair_key)
                    ports.append({
                        "host_port": host_port,
                        "container_port": container_port,
                        "protocol": proto,
                        "raw": f"{host_port}->{container_port}/{proto}"
                    })
            else:
                # Direct exposed port like 8080/tcp or 9000-9001/tcp
                single_match = re.search(r'(\d+)(?:-\d+)?/?(\w+)?', item)
                if single_match:
                    c_port = int(single_match.group(1))
                    proto = single_match.group(2) or "tcp"
                    pair_key = (c_port, c_port, proto)
                    if pair_key not in seen_pairs:
                        seen_pairs.add(pair_key)
                        ports.append({
                            "host_port": None,
                            "container_port": c_port,
                            "protocol": proto,
                            "raw": item
                        })
        return ports

    @classmethod
    async def get_active_containers(cls) -> List[Dict[str, Any]]:
        """Queries Docker for all active running containers with enriched project, service, and network data."""
        try:
            process = await asyncio.create_subprocess_exec(
                "docker", "ps", "--format", "{{json .}}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            if process.returncode != 0 or not stdout:
                return []

            lines = [l.strip() for l in stdout.decode("utf-8", errors="replace").strip().split("\n") if l.strip()]
            containers = []

            for line in lines:
                try:
                    data = json.loads(line)
                except Exception:
                    continue

                labels = cls._parse_labels(data.get("Labels", ""))
                project_name = labels.get("com.docker.compose.project") or ""
                service_name = labels.get("com.docker.compose.service") or (data.get("Names", "").split("-")[-2] if "-" in data.get("Names", "") else data.get("Names", ""))
                working_dir = labels.get("com.docker.compose.project.working_dir") or ""
                
                parsed_ports = cls._parse_ports(data.get("Ports", ""))
                networks = [n.strip() for n in (data.get("Networks", "") or "").split(",") if n.strip()]
                status_raw = data.get("Status", "")
                state_raw = (data.get("State", "") or "running").lower()

                # Health extraction
                health = None
                if "(healthy)" in status_raw.lower():
                    health = "healthy"
                elif "(unhealthy)" in status_raw.lower():
                    health = "unhealthy"
                elif "(health: starting)" in status_raw.lower() or "starting" in status_raw.lower():
                    health = "starting"

                visual_status = "green"
                if health == "unhealthy" or state_raw in ("dead", "crashed", "error"):
                    visual_status = "red"
                elif health == "starting" or state_raw in ("starting", "restarting", "created"):
                    visual_status = "yellow"
                elif state_raw in ("paused", "exited", "stopped"):
                    visual_status = "orange"

                # Tool metadata lookup for icon and category
                tool_id_clean = service_name.lower().replace("-", "_")
                try:
                    tool_def = get_tool_by_id(tool_id_clean)
                    cat_id = tool_def.category
                    icon = tool_def.icon
                    badge = tool_def.badge or "Service"
                    ui_url_template = tool_def.ui_url
                except Exception:
                    cat_id = "backend"
                    icon = "box"
                    badge = "Container"
                    ui_url_template = None

                # Construct primary UI URL if container has a web interface
                primary_ui_url = None
                is_web_ui = False
                non_web_services = ("postgres", "mysql", "mariadb", "redis", "mongodb", "kafka", "zookeeper", "clickhouse-keeper")

                svc_low = service_name.lower()
                img_low = data.get("Image", "").lower()
                is_non_web = any(nw in svc_low for nw in non_web_services) and not any(w in svc_low for w in ("ui", "web", "admin", "connect", "registry", "rest"))

                if parsed_ports and not is_non_web:
                    for p in parsed_ports:
                        hp = p.get("host_port")
                        cp = p.get("container_port")
                        if hp:
                            if "vscode" in svc_low or "code-server" in svc_low or "coder" in img_low:
                                primary_ui_url = f"http://localhost:{hp}/?folder=/home/coder/project"
                                is_web_ui = True
                                break
                            elif "clickhouse" in svc_low and cp in (8123, 80):
                                primary_ui_url = f"http://localhost:{hp}/play"
                                is_web_ui = True
                                break
                            elif "minio" in svc_low:
                                if cp == 9001 or hp in (9001, 9007, 9091):
                                    primary_ui_url = f"http://localhost:{hp}"
                                    is_web_ui = True
                                    break
                            elif "spark" in svc_low:
                                if cp == 8080 or hp in (8080, 8082, 8096):
                                    primary_ui_url = f"http://localhost:{hp}"
                                    is_web_ui = True
                                    break
                            elif any(w in svc_low for w in ("airflow", "trino", "jupyter", "kafka-ui", "kafka_ui", "connect", "registry", "rest", "superset", "metabase", "grafana", "prometheus", "pgadmin", "keycloak", "mlflow", "wazuh", "splunk", "sonarqube", "defectdojo", "zap", "n8n", "rabbitmq", "redis-commander", "doris", "starrocks", "redpanda", "pulsar", "portainer", "kibana", "opensearch", "jaeger", "open-webui", "dify", "flowise", "langfuse", "qdrant", "web", "frontend", "app")):
                                primary_ui_url = f"http://localhost:{hp}"
                                is_web_ui = True
                                break
                            elif not primary_ui_url:
                                primary_ui_url = f"http://localhost:{hp}"
                                is_web_ui = True

                colors = CATEGORY_COLORS.get(cat_id, CATEGORY_COLORS["backend"])

                containers.append({
                    "id": data.get("ID", ""),
                    "name": data.get("Names", ""),
                    "service": service_name,
                    "project": project_name or (os.path.basename(working_dir) if working_dir else "Standalone"),
                    "working_dir": working_dir,
                    "image": data.get("Image", ""),
                    "command": data.get("Command", ""),
                    "state": state_raw,
                    "status": status_raw,
                    "health": health,
                    "running_for": data.get("RunningFor", ""),
                    "size": data.get("Size", ""),
                    "networks": networks,
                    "ports": parsed_ports,
                    "ports_summary": ", ".join([p["raw"] for p in parsed_ports]) if parsed_ports else "-",
                    "primary_ui_url": primary_ui_url,
                    "visual_status": visual_status,
                    "category": cat_id,
                    "category_label": colors.get("label", "Serviço"),
                    "icon": icon,
                    "badge": badge,
                    "badge_color": colors.get("border", "#6366f1")
                })

            return containers
        except Exception as e:
            return []

    @classmethod
    async def get_all_port_mappings(cls) -> List[Dict[str, Any]]:
        """Gathers all host ports currently mapped, checks availability, and detects collisions."""
        containers = await cls.get_active_containers()
        port_list = []
        host_port_map: Dict[int, List[Dict[str, Any]]] = {}

        for c in containers:
            for p in c.get("ports", []):
                hp = p.get("host_port")
                if hp:
                    bound = is_port_bound(hp)
                    entry = {
                        "host_port": hp,
                        "container_port": p.get("container_port"),
                        "protocol": p.get("protocol", "tcp"),
                        "container_name": c["name"],
                        "service": c["service"],
                        "project": c["project"],
                        "image": c["image"],
                        "is_bound": bound,
                        "visual_status": c["visual_status"],
                        "ui_url": f"http://localhost:{hp}",
                        "icon": c["icon"],
                        "category": c["category"]
                    }
                    port_list.append(entry)
                    if hp not in host_port_map:
                        host_port_map[hp] = []
                    host_port_map[hp].append(entry)

        # Mark conflicts if multiple containers bind the same host port
        for p in port_list:
            hp = p["host_port"]
            p["has_conflict"] = len(host_port_map.get(hp, [])) > 1

        # Sort numerically by host port
        port_list.sort(key=lambda x: x["host_port"])
        return port_list

    @classmethod
    async def get_network_topology(cls) -> Dict[str, Any]:
        """Builds a global inter-service communication and dependency topology graph across all active containers."""
        containers = await cls.get_active_containers()
        if not containers:
            return {"nodes": [], "edges": [], "networks": [], "total_nodes": 0, "total_edges": 0}

        # Index containers by service and project
        nodes = []
        node_ids = set()
        service_to_nodes: Dict[str, List[str]] = {}
        networks_map: Dict[str, List[str]] = {}

        for c in containers:
            node_id = c["name"]
            node_ids.add(node_id)
            svc_clean = c["service"].lower().replace("-", "_")
            if svc_clean not in service_to_nodes:
                service_to_nodes[svc_clean] = []
            service_to_nodes[svc_clean].append(node_id)

            # Map networks
            for net in c.get("networks", []):
                if net not in networks_map:
                    networks_map[net] = []
                networks_map[net].append(node_id)

            nodes.append({
                "id": node_id,
                "label": c["name"],
                "service": c["service"],
                "project": c["project"],
                "image": c["image"],
                "visual_status": c["visual_status"],
                "status": c["status"],
                "health": c["health"],
                "ports": c["ports_summary"],
                "primary_ui_url": c["primary_ui_url"],
                "category": c["category"],
                "category_label": c["category_label"],
                "icon": c["icon"],
                "badge": c["badge"],
                "networks": c["networks"]
            })

        edges = []
        seen_edges = set()

        # 1. Add Architectural & Data Flow Edges from RELATIONSHIPS
        for rel in RELATIONSHIPS:
            src_svc = rel["source"].lower()
            tgt_svc = rel["target"].lower()

            src_nodes = service_to_nodes.get(src_svc, [])
            tgt_nodes = service_to_nodes.get(tgt_svc, [])

            for sn in src_nodes:
                for tn in tgt_nodes:
                    # Prefer linking containers in the same project or sharing a network
                    sn_obj = next((c for c in containers if c["name"] == sn), None)
                    tn_obj = next((c for c in containers if c["name"] == tn), None)
                    
                    same_project = sn_obj and tn_obj and sn_obj["project"] == tn_obj["project"]
                    shares_network = sn_obj and tn_obj and any(n in tn_obj.get("networks", []) for n in sn_obj.get("networks", []))

                    if same_project or shares_network:
                        edge_key = (sn, tn, rel["label"])
                        if edge_key not in seen_edges:
                            seen_edges.add(edge_key)
                            edges.append({
                                "source": sn,
                                "target": tn,
                                "label": rel["label"],
                                "type": rel["type"],
                                "active": sn_obj.get("visual_status") == "green" and tn_obj.get("visual_status") == "green",
                                "same_project": same_project,
                                "network": (sn_obj.get("networks") or [""])[0] if sn_obj else ""
                            })

        # 2. Grouped networks summary
        networks_summary = []
        for net_name, members in networks_map.items():
            if net_name.lower() in ("bridge", "host", "none"):
                continue
            networks_summary.append({
                "name": net_name,
                "container_count": len(members),
                "containers": members
            })

        return {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "nodes": nodes,
            "edges": edges,
            "networks": networks_summary
        }

    @classmethod
    async def get_full_overview(cls) -> Dict[str, Any]:
        """Bundles containers, port maps, topology graph, and real-time statistics."""
        containers = await cls.get_active_containers()
        ports = await cls.get_all_port_mappings()
        topology = await cls.get_network_topology()

        unique_projects = list(set([c["project"] for c in containers if c.get("project")]))
        unique_networks = list(set([n for c in containers for n in c.get("networks", []) if n not in ("bridge", "host", "none")]))

        healthy_count = sum(1 for c in containers if c.get("visual_status") == "green")
        starting_count = sum(1 for c in containers if c.get("visual_status") == "yellow")
        error_count = sum(1 for c in containers if c.get("visual_status") == "red")

        return {
            "stats": {
                "total_containers": len(containers),
                "healthy_containers": healthy_count,
                "starting_containers": starting_count,
                "error_containers": error_count,
                "total_ports_allocated": len(ports),
                "unique_projects": len(unique_projects),
                "unique_networks": len(unique_networks),
                "projects_list": sorted(unique_projects),
                "networks_list": sorted(unique_networks)
            },
            "containers": containers,
            "ports": ports,
            "topology": topology
        }
