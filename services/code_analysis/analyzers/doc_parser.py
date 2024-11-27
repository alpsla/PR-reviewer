from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
import re
from enum import Enum

class DocStyle(Enum):
    """Documentation style enumeration"""
    JSDOC = "jsdoc"
    TSDOC = "tsdoc"
    REACT_DOC = "reactdoc"

@dataclass
class ParamInfo:
    """Parameter documentation information"""
    name: str
    type: str
    description: str
    optional: bool = False
    default_value: Optional[str] = None

@dataclass
class ReturnInfo:
    """Return value documentation information"""
    type: str
    description: str
    nullable: bool = False

@dataclass
class TypedefInfo:
    """Type definition documentation information"""
    name: str
    properties: Dict[str, ParamInfo]
    description: str
    extends: List[str] = field(default_factory=list)

@dataclass
class ComponentDocInfo:
    """React component documentation information"""
    component_name: str
    description: str
    props: Dict[str, ParamInfo]
    examples: List[str]
    see_also: List[str]
    deprecated: bool = False
    experimental: bool = False

@dataclass
class DocInfo:
    """Enhanced documentation information"""
    description: str
    params: Dict[str, ParamInfo] = field(default_factory=dict)
    returns: Optional[ReturnInfo] = None
    throws: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    deprecated: bool = False
    since_version: Optional[str] = None
    see_also: List[str] = field(default_factory=list)
    typedefs: Dict[str, TypedefInfo] = field(default_factory=dict)
    component_info: Optional[ComponentDocInfo] = None
    experimental: bool = False
    doc_style: DocStyle = DocStyle.JSDOC

class DocParser:
    """Enhanced documentation parser for JSDoc, TSDoc, and React documentation"""

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for documentation parsing"""
        self.patterns = {
            'doc_block': re.compile(r'/\*\*\s*(.*?)\s*\*/', re.DOTALL),
            'param': re.compile(
                r'@param\s+(?:{([^}]+)})?\s*(?:\[([^\]]+)\]|(\w+))\s*-?\s*([^\n]+)?'
            ),
            'returns': re.compile(r'@returns?\s+(?:{([^}]+)})?\s*-?\s*([^\n]+)?'),
            'throws': re.compile(r'@throws?\s+(?:{([^}]+)})?\s*-?\s*([^\n]+)?'),
            'typedef': re.compile(
                r'@typedef\s+(?:{([^}]+)})?\s*(\w+)\s*(?:extends\s+([^\n]+))?'
            ),
            'property': re.compile(
                r'@property\s+(?:{([^}]+)})?\s*(?:\[([^\]]+)\]|(\w+))\s*-?\s*([^\n]+)?'
            ),
            'example': re.compile(r'@example\s*\n((?:(?!\s*@|\*/).|\n)*)', re.MULTILINE),
            'since': re.compile(r'@since\s+([^\n]+)'),
            'see': re.compile(r'@see\s+([^\n]+)'),
            'deprecated': re.compile(r'@deprecated\s*(?:\s+([^\n]+))?'),
            'experimental': re.compile(r'@experimental\s*(?:\s+([^\n]+))?'),
            
            # React-specific patterns
            'component': re.compile(r'@component\s+(\w+)'),
            'prop': re.compile(
                r'@prop\s+(?:{([^}]+)})?\s*(?:\[([^\]]+)\]|(\w+))\s*-?\s*([^\n]+)?'
            )
        }

    def parse(self, content: str, style: DocStyle = DocStyle.JSDOC) -> List[DocInfo]:
        """Parse documentation blocks from content"""
        doc_blocks = self.patterns['doc_block'].finditer(content)
        parsed_docs = []

        for block in doc_blocks:
            doc_text = block.group(1)
            doc_info = self._parse_doc_block(doc_text, style)
            if doc_info:
                parsed_docs.append(doc_info)

        return parsed_docs

    def _parse_doc_block(self, doc_text: str, style: DocStyle) -> Optional[DocInfo]:
        """Parse a single documentation block"""
        try:
            # Initialize doc info
            doc_info = DocInfo(description="", doc_style=style)
            
            # Split into lines and process
            lines = doc_text.split('\n')
            current_section = 'description'
            current_example = []
            
            for line in lines:
                line = line.strip().strip('* ')
                
                if not line:
                    continue

                # Handle different documentation sections
                if line.startswith('@param') or line.startswith('@prop'):
                    param_info = self._parse_parameter(line)
                    if param_info:
                        doc_info.params[param_info.name] = param_info
                
                elif line.startswith('@returns'):
                    return_info = self._parse_return(line)
                    if return_info:
                        doc_info.returns = return_info
                
                elif line.startswith('@throws'):
                    error_info = self._parse_throws(line)
                    if error_info:
                        doc_info.throws.append(error_info)
                
                elif line.startswith('@typedef'):
                    typedef_info = self._parse_typedef(line)
                    if typedef_info:
                        doc_info.typedefs[typedef_info.name] = typedef_info
                
                elif line.startswith('@example'):
                    current_section = 'example'
                    continue
                
                elif line.startswith('@since'):
                    match = self.patterns['since'].match(line)
                    if match:
                        doc_info.since_version = match.group(1)
                
                elif line.startswith('@see'):
                    match = self.patterns['see'].match(line)
                    if match:
                        doc_info.see_also.append(match.group(1))
                
                elif line.startswith('@deprecated'):
                    doc_info.deprecated = True
                
                elif line.startswith('@experimental'):
                    doc_info.experimental = True
                
                elif line.startswith('@component') and style in [DocStyle.JSDOC, DocStyle.REACT_DOC]:
                    self._parse_component_info(line, doc_info)
                
                elif line.startswith('@'):
                    current_section = 'other'
                
                elif current_section == 'description':
                    doc_info.description += line + ' '
                
                elif current_section == 'example':
                    if line.startswith('```'):
                        if current_example:
                            doc_info.examples.append('\n'.join(current_example))
                            current_example = []
                    else:
                        current_example.append(line)

            # Clean up description
            doc_info.description = doc_info.description.strip()
            
            # Add any remaining example
            if current_example:
                doc_info.examples.append('\n'.join(current_example))

            return doc_info

        except Exception as e:
            print(f"Error parsing doc block: {str(e)}")
            return None

    def _parse_parameter(self, line: str) -> Optional[ParamInfo]:
        """Parse parameter documentation"""
        match = self.patterns['param'].match(line) or self.patterns['prop'].match(line)
        if match:
            type_str, optional_name, regular_name, description = match.groups()
            name = optional_name or regular_name
            
            return ParamInfo(
                name=name,
                type=type_str or 'any',
                description=description or '',
                optional=bool(optional_name),
                default_value=self._extract_default_value(optional_name) if optional_name else None
            )
        return None

    def _parse_return(self, line: str) -> Optional[ReturnInfo]:
        """Parse return documentation"""
        match = self.patterns['returns'].match(line)
        if match:
            type_str, description = match.groups()
            return ReturnInfo(
                type=type_str or 'any',
                description=description or '',
                nullable='|' in type_str and 'null' in type_str if type_str else False
            )
        return None

    def _parse_throws(self, line: str) -> Optional[str]:
        """Parse throws documentation"""
        match = self.patterns['throws'].match(line)
        if match:
            type_str, description = match.groups()
            return f"{type_str}: {description}" if type_str else description
        return None

    def _parse_typedef(self, line: str) -> Optional[TypedefInfo]:
        """Parse typedef documentation"""
        match = self.patterns['typedef'].match(line)
        if match:
            type_str, name, extends_str = match.groups()
            extends = [t.strip() for t in extends_str.split(',')] if extends_str else []
            
            return TypedefInfo(
                name=name,
                properties={},
                description=type_str or '',
                extends=extends
            )
        return None

    def _parse_component_info(self, line: str, doc_info: DocInfo):
        """Parse React component documentation"""
        match = self.patterns['component'].match(line)
        if match:
            component_name = match.group(1)
            doc_info.component_info = ComponentDocInfo(
                component_name=component_name,
                description=doc_info.description,
                props=doc_info.params,
                examples=doc_info.examples,
                see_also=doc_info.see_also,
                deprecated=doc_info.deprecated,
                experimental=doc_info.experimental
            )

    def _extract_default_value(self, optional_param: str) -> Optional[str]:
        """Extract default value from optional parameter"""
        if '=' in optional_param:
            return optional_param.split('=')[1].strip()
        return None
