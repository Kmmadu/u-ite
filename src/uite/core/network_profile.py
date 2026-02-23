"""
Network Profile Management Module for U-ITE
============================================
Manages persistent profiles for networks the device has connected to.
Each profile stores metadata about a network including name, provider,
tags, and timestamps.

Features:
- Automatic profile creation for new networks
- Persistent storage in JSON format
- Metadata management (name, provider, tags)
- Offline session tracking
- Profile merging for reconnected networks
- Human-readable name generation from fingerprints
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import hashlib


class NetworkProfile:
    """
    Profile for a specific network/ISP.
    
    Stores all metadata associated with a network connection.
    Each network is uniquely identified by its network_id (derived from
    stable network characteristics like router IP and MAC address).
    
    Attributes:
        network_id: Unique identifier for the network
        name: Human-readable name (user-assignable)
        provider: ISP name (user-assignable)
        tags: List of user-defined tags for organization
        first_seen: When this network was first detected
        last_seen: When this network was last seen
        notes: Additional notes about the network
        is_offline_network: Flag for temporary offline sessions
    
    Example:
        >>> profile = NetworkProfile("a1b2c3d4", "Home Fiber", "Comcast")
        >>> profile.tags.append("primary")
        >>> profile.last_seen = datetime.now()
    """
    
    def __init__(self, network_id: str, name: str = None, provider: str = ""):
        """
        Initialize a new network profile.
        
        Args:
            network_id: Unique identifier for the network
            name: Optional human-readable name (auto-generated if None)
            provider: Optional ISP/provider name
        """
        self.network_id = network_id
        self.name = name or f"Network {network_id[:8]}"  # Auto-generate name from ID
        self.provider = provider
        self.tags: List[str] = []
        self.first_seen: datetime = datetime.now()
        self.last_seen: datetime = datetime.now()
        self.notes: str = ""
        self.is_offline_network = False  # Flag for temporary offline sessions
    
    def to_dict(self) -> dict:
        """
        Convert profile to dictionary for JSON serialization.
        
        Returns:
            dict: Dictionary representation of the profile
        """
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
        """
        Create a profile from a dictionary (deserialization).
        
        Args:
            data: Dictionary containing profile data
            
        Returns:
            NetworkProfile: Reconstructed profile object
        """
        profile = cls(data["network_id"], data.get("name"), data.get("provider", ""))
        profile.tags = data.get("tags", [])
        profile.first_seen = datetime.fromisoformat(data["first_seen"])
        profile.last_seen = datetime.fromisoformat(data["last_seen"])
        profile.notes = data.get("notes", "")
        profile.is_offline_network = data.get("is_offline_network", False)
        return profile


class NetworkProfileManager:
    """
    Manages network profiles with persistent storage.
    
    Handles loading/saving profiles to disk, profile creation,
    updates, and queries. Acts as a central registry for all
    networks the device has ever connected to.
    
    Storage format: JSON file at ~/.u-ite/network_profiles.json
    
    Example:
        >>> manager = NetworkProfileManager()
        >>> profile = manager.get_or_create(network_id, fingerprint)
        >>> manager.rename(profile.network_id, "Home WiFi")
        >>> manager.tag(profile.network_id, "primary")
        >>> manager.save()
    """
    
    def __init__(self):
        """Initialize the manager and load existing profiles."""
        self.config_dir = Path.home() / ".u-ite"
        self.profiles_file = self.config_dir / "network_profiles.json"
        self.profiles: Dict[str, NetworkProfile] = {}
        self.load()
    
    def load(self):
        """
        Load profiles from disk.
        
        Reads the JSON file and reconstructs all profile objects.
        If the file doesn't exist or is corrupted, starts with empty profiles.
        """
        if self.profiles_file.exists():
            try:
                data = json.loads(self.profiles_file.read_text())
                for network_id, profile_data in data.items():
                    self.profiles[network_id] = NetworkProfile.from_dict(profile_data)
            except (json.JSONDecodeError, KeyError, ValueError):
                # If file is corrupted, start fresh
                self.profiles = {}
    
    def save(self):
        """
        Save profiles to disk.
        
        Writes all profiles to the JSON file with pretty formatting.
        Creates the config directory if it doesn't exist.
        """
        self.config_dir.mkdir(exist_ok=True)
        data = {pid: p.to_dict() for pid, p in self.profiles.items()}
        self.profiles_file.write_text(json.dumps(data, indent=2))
    
    def get_or_create(self, network_id: str, fingerprint: dict = None, is_offline: bool = False) -> NetworkProfile:
        """
        Get existing profile or create a new one, always updating last_seen.
        
        This is the main entry point for the observer. It ensures that:
        - Existing profiles are retrieved and their last_seen updated
        - New profiles are created with appropriate names
        - Offline sessions are handled specially
        - Profiles are persisted immediately
        
        Args:
            network_id: Unique network identifier
            fingerprint: Network fingerprint dictionary (for name generation)
            is_offline: Whether this is an offline session
            
        Returns:
            NetworkProfile: The retrieved or created profile
        """
        # Case 1: Existing profile found
        if network_id in self.profiles:
            profile = self.profiles[network_id]
            profile.last_seen = datetime.now()  # Update timestamp
            self.save()  # Persist immediately
            return profile
        
        # Extract router IP from fingerprint for offline matching
        router_ip = fingerprint.get('default_gateway') if fingerprint else None
        
        # Case 2: Offline session - try to match with existing online network
        if is_offline or not router_ip:
            # Look for any existing network that had this router IP
            for pid, existing in self.profiles.items():
                if existing.notes and router_ip and router_ip in existing.notes:
                    # Found a match - this is the same network, just offline
                    existing.last_seen = datetime.now()
                    self.save()
                    return existing
            
            # No match found - create a temporary offline profile
            name = "Offline State"
            profile = NetworkProfile(network_id, name)
            profile.is_offline_network = True
            profile.notes = f"Offline network (last seen router: {router_ip})" if router_ip else "No network connection"
        
        # Case 3: New online network
        else:
            # Generate a friendly name from the fingerprint
            name = self._generate_name(fingerprint)
            profile = NetworkProfile(network_id, name)
        
        # Save and return the new profile
        self.profiles[network_id] = profile
        self.save()
        return profile
    
    def _generate_name(self, fingerprint: dict) -> str:
        """
        Generate a friendly, human-readable name from a network fingerprint.
        
        Tries multiple strategies in order:
        1. Use gateway IP if available
        2. Use hostname if available
        3. Fall back to generic "Network X"
        
        Args:
            fingerprint: Network fingerprint dictionary
            
        Returns:
            str: Suggested network name
        """
        if not fingerprint:
            return f"Network {len(self.profiles) + 1}"
        
        # Strategy 1: Use gateway IP (most descriptive)
        gateway = fingerprint.get('default_gateway', '')
        if gateway:
            return f"Network {gateway}"
        
        # Strategy 2: Use hostname
        hostname = fingerprint.get('hostname', '')
        if hostname and hostname != 'unknown':
            return f"{hostname}'s Network"
        
        # Strategy 3: Generic name
        return f"Network {len(self.profiles) + 1}"
    
    def rename(self, network_id: str, name: str):
        """
        Rename a network with a user-friendly name.
        
        Args:
            network_id: Network identifier
            name: New human-readable name
        """
        if network_id in self.profiles:
            self.profiles[network_id].name = name
            self.save()
    
    def tag(self, network_id: str, tag: str):
        """
        Add a tag to a network for easy filtering and organization.
        
        Args:
            network_id: Network identifier
            tag: Tag to add (e.g., "primary", "backup", "work")
        """
        if network_id in self.profiles:
            if tag not in self.profiles[network_id].tags:
                self.profiles[network_id].tags.append(tag)
                self.save()
    
    def list_profiles(self) -> List[NetworkProfile]:
        """
        Get all network profiles.
        
        Returns:
            List[NetworkProfile]: All profiles (both online and offline)
        """
        return list(self.profiles.values())
    
    def merge_offline_network(self, offline_id: str, online_id: str) -> bool:
        """
        Merge an offline session profile into its corresponding online profile.
        
        When a network reconnects after being offline, this method merges
        the temporary offline profile into the main network profile to
        preserve continuity.
        
        Args:
            offline_id: ID of the temporary offline profile
            online_id: ID of the main network profile
            
        Returns:
            bool: True if merge was successful, False otherwise
        """
        if offline_id in self.profiles and online_id in self.profiles:
            offline = self.profiles[offline_id]
            online = self.profiles[online_id]
            
            # Transfer earliest first_seen to maintain history
            if offline.first_seen < online.first_seen:
                online.first_seen = offline.first_seen
            
            # Remove the temporary offline profile
            del self.profiles[offline_id]
            self.save()
            return True
        return False


# ============================================================================
# Utility functions for working with profiles
# ============================================================================
def format_profile_summary(profile: NetworkProfile) -> str:
    """
    Format a profile for display in CLI output.
    
    Args:
        profile: Network profile to format
        
    Returns:
        str: Human-readable profile summary
    """
    tags = f" [{', '.join(profile.tags)}]" if profile.tags else ""
    provider = f" ({profile.provider})" if profile.provider else ""
    return f"{profile.name}{provider}{tags}"


def find_profile_by_name(manager: NetworkProfileManager, name: str) -> Optional[NetworkProfile]:
    """
    Find a profile by its name (case-insensitive partial match).
    
    Args:
        manager: NetworkProfileManager instance
        name: Name to search for
        
    Returns:
        Optional[NetworkProfile]: First matching profile, or None
    """
    name_lower = name.lower()
    for profile in manager.list_profiles():
        if name_lower in profile.name.lower():
            return profile
    return None


# Export public interface
__all__ = ['NetworkProfile', 'NetworkProfileManager', 'format_profile_summary', 'find_profile_by_name']
