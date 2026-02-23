import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import hashlib

class NetworkProfile:
    """Profile for a specific network/ISP"""
    
    def __init__(self, network_id: str, name: str = None, provider: str = ""):
        self.network_id = network_id
        self.name = name or f"Network {network_id[:8]}"  # Use ID if no name
        self.provider = provider
        self.tags: List[str] = []
        self.first_seen: datetime = datetime.now()
        self.last_seen: datetime = datetime.now()
        self.notes: str = ""
        self.is_offline_network = False  # Flag for offline-only networks
    
    def to_dict(self) -> dict:
        return {
            "network_id": self.network_id,
            "name": self.name,
            "provider": self.provider,
            "tags": self.tags,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "notes": self.notes,
            "is_offline_network": self.is_offline_network
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        profile = cls(data["network_id"], data.get("name"), data.get("provider", ""))
        profile.tags = data.get("tags", [])
        profile.first_seen = datetime.fromisoformat(data["first_seen"])
        profile.last_seen = datetime.fromisoformat(data["last_seen"])
        profile.notes = data.get("notes", "")
        profile.is_offline_network = data.get("is_offline_network", False)
        return profile

class NetworkProfileManager:
    """Manages network profiles"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".u-ite"
        self.profiles_file = self.config_dir / "network_profiles.json"
        self.profiles: Dict[str, NetworkProfile] = {}
        self.load()
    
    def load(self):
        """Load profiles from disk"""
        if self.profiles_file.exists():
            try:
                data = json.loads(self.profiles_file.read_text())
                for network_id, profile_data in data.items():
                    self.profiles[network_id] = NetworkProfile.from_dict(profile_data)
            except:
                pass
    
    def save(self):
        """Save profiles to disk"""
        self.config_dir.mkdir(exist_ok=True)
        data = {pid: p.to_dict() for pid, p in self.profiles.items()}
        self.profiles_file.write_text(json.dumps(data, indent=2))
    
    def get_or_create(self, network_id: str, fingerprint: dict = None, is_offline: bool = False) -> NetworkProfile:
        """Get existing profile or create new one, always updating last_seen"""
        # First check if we already have this profile
        if network_id in self.profiles:
            profile = self.profiles[network_id]
            profile.last_seen = datetime.now()  # Update last_seen timestamp
            self.save()  # Save the updated profile to disk
            return profile
        
        # Check if this might be the same as a previous offline network
        # by looking at the router IP or other identifiers
        router_ip = fingerprint.get('default_gateway') if fingerprint else None
        
        # Special handling for offline state
        if is_offline or not router_ip:
            # Look for any existing network with the same router IP when it was online
            for pid, existing in self.profiles.items():
                if existing.notes and router_ip and router_ip in existing.notes:
                    # This is the same network, just offline
                    existing.last_seen = datetime.now()  # Update last_seen timestamp
                    self.save()  # Save the updated profile to disk
                    return existing
            
            # Create a temporary offline profile
            name = "Offline State"
            profile = NetworkProfile(network_id, name)
            profile.is_offline_network = True
            profile.notes = f"Offline network (last seen router: {router_ip})" if router_ip else "No network connection"
        else:
            # Generate a friendly name from fingerprint
            name = self._generate_name(fingerprint)
            profile = NetworkProfile(network_id, name)
        
        self.profiles[network_id] = profile
        self.save()
        return profile
    
    def _generate_name(self, fingerprint: dict) -> str:
        """Generate a friendly name from fingerprint"""
        if not fingerprint:
            return f"Network {len(self.profiles) + 1}"
        
        # Try to get network name from gateway
        gateway = fingerprint.get('default_gateway', '')
        if gateway:
            return f"Network {gateway}"
        
        # Try hostname
        hostname = fingerprint.get('hostname', '')
        if hostname and hostname != 'unknown':
            return f"{hostname}'s Network"
        
        return f"Network {len(self.profiles) + 1}"
    
    def rename(self, network_id: str, name: str):
        """Rename a network"""
        if network_id in self.profiles:
            self.profiles[network_id].name = name
            self.save()
    
    def tag(self, network_id: str, tag: str):
        """Add a tag to a network"""
        if network_id in self.profiles:
            if tag not in self.profiles[network_id].tags:
                self.profiles[network_id].tags.append(tag)
                self.save()
    
    def list_profiles(self) -> List[NetworkProfile]:
        """List all profiles"""
        return list(self.profiles.values())
    
    def merge_offline_network(self, offline_id: str, online_id: str):
        """Merge an offline network profile into an online one"""
        if offline_id in self.profiles and online_id in self.profiles:
            offline = self.profiles[offline_id]
            online = self.profiles[online_id]
            
            # Transfer any useful data
            if offline.first_seen < online.first_seen:
                online.first_seen = offline.first_seen
            
            # Remove the offline profile
            del self.profiles[offline_id]
            self.save()
            return True
        return False
