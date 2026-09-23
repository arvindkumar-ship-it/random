import requests
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
import hashlib
from typing import Dict, Any, Optional, List, Tuple


class TemporalVerifier:
    def __init__(self):
        self.wayback_api = "http://archive.org/wayback/available"

    def check_wayback_snapshot(self, url: str, claim_date: datetime) -> Dict[str, Any]:
        """Check if URL existed at claim time via Wayback Machine"""
        try:
            response = requests.get(
                self.wayback_api,
                params={'url': url, 'timestamp': claim_date.strftime('%Y%m%d')},
                timeout=5
            )
            data = response.json()

            if 'archived_snapshots' in data and 'closest' in data['archived_snapshots']:
                snapshot = data['archived_snapshots']['closest']
                return {
                    'exists': True,
                    'snapshot_url': snapshot['url'],
                    'snapshot_date': snapshot['timestamp'],
                    'available': snapshot['available']
                }
            return {'exists': False}
        except Exception as e:
            return {'exists': False, 'error': str(e)}

    def extract_image_metadata(self, image_path: str) -> Dict[str, Any]:
        """Extract EXIF metadata from image"""
        try:
            img = Image.open(image_path)
            exif_data = img.getexif()
            metadata = {}
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    metadata[tag] = value

            with open(image_path, 'rb') as f:
                metadata['image_hash'] = hashlib.md5(f.read()).hexdigest()

            return metadata
        except Exception as e:
            return {'error': str(e)}

    def verify_temporal_consistency(self, claim_date: datetime,
                                     evidence_date: datetime,
                                     image_metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Check if timeline is consistent"""
        result = {
            'claim_date': claim_date.isoformat(),
            'evidence_date': evidence_date.isoformat(),
            'consistent': evidence_date >= claim_date,
            'reason': 'Evidence published after claim' if evidence_date >= claim_date
                      else f'Evidence predates claim by {(claim_date - evidence_date).days} days'
        }

        if image_metadata and 'DateTimeOriginal' in image_metadata:
            try:
                exif_date = datetime.strptime(image_metadata['DateTimeOriginal'],
                                               '%Y:%m:%d %H:%M:%S')
                if exif_date > claim_date:
                    result['consistent'] = False
                    result['reason'] += f'; Image EXIF shows later date: {exif_date}'
            except Exception:
                pass

        return result


class GeolocationVerifier:
    """Free geolocation via OpenStreetMap — Nominatim (geocode) + Overpass (nearby places). No API key."""

    def __init__(self, google_api_key: str = ""):  # kept for backward-compat call signature
        self.geocode_url = "https://nominatim.openstreetmap.org/search"
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        self.headers = {"User-Agent": "claim-verification-engine/1.0"}

    def verify_location(self, claimed_location: str,
                         image_landmarks: List[str],
                         image_path: Optional[str] = None) -> Dict[str, Any]:
        """Verify if image matches claimed location"""
        try:
            coords = self._get_coordinates(claimed_location)
            lat, lng = coords
            # Overpass: named nodes/ways within 5km, tagged as notable places
            query = f"""
            [out:json][timeout:10];
            (
              node["name"](around:5000,{lat},{lng});
            );
            out body 30;
            """
            response = requests.post(self.overpass_url, data={'data': query},
                                      headers=self.headers, timeout=15)
            places_data = response.json()

            known_landmarks = [
                el['tags']['name'] for el in places_data.get('elements', [])
                if el.get('tags', {}).get('name')
            ]
            overlap = set(image_landmarks).intersection(set(known_landmarks))

            return {
                'claimed_location': claimed_location,
                'detected_landmarks': image_landmarks,
                'known_landmarks_at_location': known_landmarks[:10],
                'overlap_count': len(overlap),
                'confidence': len(overlap) / max(len(image_landmarks), 1) if image_landmarks else 0.0,
                'verified': len(overlap) >= 2
            }
        except Exception as e:
            return {'verified': False, 'error': str(e)}

    def _get_coordinates(self, location_name: str) -> Tuple[float, float]:
        """Geocode location name to lat/lng via Nominatim (OpenStreetMap, free)"""
        try:
            params = {'q': location_name, 'format': 'json', 'limit': 1}
            response = requests.get(self.geocode_url, params=params,
                                     headers=self.headers, timeout=10)
            data = response.json()
            if data:
                return (float(data[0]['lat']), float(data[0]['lon']))
        except Exception:
            pass
        return (28.6139, 77.2090)  # Default: Delhi
