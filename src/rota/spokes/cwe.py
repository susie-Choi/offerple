"""CWE (Common Weakness Enumeration) collector from MITRE."""

from datetime import datetime
from typing import Dict, Any, List
import logging
import xml.etree.ElementTree as ET

from .base import BaseCollector

logger = logging.getLogger(__name__)


class CWECollector(BaseCollector):
    """
    Collect CWE data from MITRE CWE database.
    
    CWE provides a comprehensive dictionary of software weaknesses.
    Source: https://cwe.mitre.org/data/downloads.html
    """
    
    source_name = "cwe"
    CWE_XML_URL = "https://cwe.mitre.org/data/xml/cwec_latest.xml.zip"
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect CWE database from MITRE.
        
        Returns:
            Collection statistics
        """
        logger.info("Collecting CWE database from MITRE")
        
        # Download and extract XML
        import zipfile
        import io
        
        response = self._request("GET", self.CWE_XML_URL)
        
        # Extract XML from zip
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            # Find the XML file
            xml_files = [f for f in zf.namelist() if f.endswith('.xml')]
            if not xml_files:
                raise Exception("No XML file found in CWE zip")
            
            xml_content = zf.read(xml_files[0])
        
        logger.info(f"Downloaded CWE XML ({len(xml_content)} bytes)")
        
        # Parse XML
        root = ET.fromstring(xml_content)
        
        # Extract weaknesses
        weaknesses = []
        for weakness in root.findall('.//{http://cwe.mitre.org/cwe-7}Weakness'):
            cwe_data = self._parse_weakness(weakness)
            if cwe_data and self.validate(cwe_data):
                weaknesses.append(cwe_data)
        
        logger.info(f"Parsed {len(weaknesses)} CWE entries")
        
        # Save to JSONL
        if weaknesses:
            filename = f"cwe_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jsonl"
            self.save_jsonl(weaknesses, filename)
        
        return self.get_stats(weaknesses)
    
    def _parse_weakness(self, weakness_elem) -> Dict[str, Any]:
        """Parse CWE weakness element from XML."""
        ns = {'cwe': 'http://cwe.mitre.org/cwe-7'}
        
        try:
            cwe_id = weakness_elem.get('ID')
            name = weakness_elem.get('Name', '')
            abstraction = weakness_elem.get('Abstraction', '')
            structure = weakness_elem.get('Structure', '')
            status = weakness_elem.get('Status', '')
            
            # Description
            description_elem = weakness_elem.find('cwe:Description', ns)
            description = description_elem.text if description_elem is not None else ''
            
            # Extended description
            extended_desc_elem = weakness_elem.find('cwe:Extended_Description', ns)
            extended_description = ''
            if extended_desc_elem is not None:
                extended_description = ''.join(extended_desc_elem.itertext())
            
            # Likelihood of exploit
            likelihood_elem = weakness_elem.find('cwe:Likelihood_Of_Exploit', ns)
            likelihood = likelihood_elem.text if likelihood_elem is not None else ''
            
            # Common consequences
            consequences = []
            for consequence in weakness_elem.findall('.//cwe:Consequence', ns):
                scope_elem = consequence.find('cwe:Scope', ns)
                impact_elem = consequence.find('cwe:Impact', ns)
                if scope_elem is not None and impact_elem is not None:
                    consequences.append({
                        'scope': scope_elem.text,
                        'impact': impact_elem.text
                    })
            
            # Related weaknesses
            related = []
            for relation in weakness_elem.findall('.//cwe:Related_Weakness', ns):
                related_id = relation.get('CWE_ID')
                nature = relation.get('Nature', '')
                if related_id:
                    related.append({
                        'cwe_id': f"CWE-{related_id}",
                        'nature': nature
                    })
            
            # Applicable platforms
            languages = []
            for lang in weakness_elem.findall('.//cwe:Language', ns):
                lang_name = lang.get('Name', '')
                if lang_name:
                    languages.append(lang_name)
            
            return {
                'cwe_id': f"CWE-{cwe_id}",
                'name': name,
                'abstraction': abstraction,
                'structure': structure,
                'status': status,
                'description': description.strip(),
                'extended_description': extended_description.strip(),
                'likelihood_of_exploit': likelihood,
                'consequences': consequences,
                'related_weaknesses': related,
                'applicable_languages': languages,
            }
            
        except Exception as e:
            logger.warning(f"Failed to parse weakness: {e}")
            return {}
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate CWE data."""
        required_fields = ["cwe_id", "name", "description"]
        
        for field in required_fields:
            if field not in data or not data[field]:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate CWE ID format
        cwe_id = data["cwe_id"]
        if not cwe_id.startswith("CWE-"):
            logger.warning(f"Invalid CWE ID format: {cwe_id}")
            return False
        
        return True


__all__ = ['CWECollector']
