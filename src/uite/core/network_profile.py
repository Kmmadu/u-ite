import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class NetworkProfile:
    """Profile for a specific network/ISP"""
    
    def __init__(self, network_id: str, name: str, provider: str = ""):
        self.network_id = network_id
        self.name = name  # e.g., "Home Fiber", "Work VPN", "Mobile Hotspot"
        self.provider = provider  # e.g., "Comcast", "AT&T", "Starlink"
        self.tags: List[str] = []  # e.g., ["backup", "primary", "vpn"]
        self.first_seen: datetime = datetime.now()
        self.last_seen: datetime = datetime.now()
        self.notes: str = ""
    
    def to_dict(self) -> dict:
        return {
            "network_id": self.network_id,
            "name": self.name,
            "provider": self.provider,
            "tags": self.tags,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        profile = cls(data["network_id"], data["name"], data.get("provider", ""))
        profile.tags = data.get("tags", [])
        profile.first_seen = datetime.fromisoformat(data["first_seen"])
        profile.last_seen = datetime.fromisoformat(data["last_seen"])
        profile.notes = data.get("notes", "")
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
    
    def get_or_create(self, network_id: str, fingerprint: dict = None) -> NetworkProfile:
        """Get existing profile or create new one"""
        if network_id in self.profiles:
            profile = self.profiles[network_id]
            profile.last_seen = datetime.now()
            return profile
        
        # Try to generate a friendly name from fingerprint
        name = self._generate_name(fingerprint)
        profile = NetworkProfile(network_id, name)
        self.profiles[network_id] = profile
        self.save()
        return profile
    
    def _generate_name(self, fingerprint: dict) -> str:
        """Generate a friendly name from fingerprint"""
        if not fingerprint:
            return f"Network {len(self.profiles) + 1}"
        
        # Try to get network name from gateway or other identifiers
        gateway = fingerprint.get('default_gateway', '')
        if gateway:
            # Could do reverse DNS lookup here
            return f"Network {gateway}"
        
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