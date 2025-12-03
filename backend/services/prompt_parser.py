"""YAML/XML system prompt parser with template variable substitution."""
import yaml
import re
from typing import Dict, Any, Optional
from lxml import etree
from io import StringIO


class PromptParseError(Exception):
    """Custom exception for prompt parsing errors."""
    pass


class PromptParser:
    """Parse and process YAML/XML system prompts with variable substitution."""
    
    def __init__(self):
        """Initialize the prompt parser."""
        self.variable_pattern = re.compile(r'\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}')
    
    def parse(self, raw_prompt: str) -> Dict[str, Any]:
        """
        Parse YAML prompt with embedded XML tags.
        
        Args:
            raw_prompt: Raw YAML string with potential XML tags
            
        Returns:
            Parsed prompt structure as dictionary
            
        Raises:
            PromptParseError: If parsing fails
        """
        try:
            # Parse YAML
            prompt_data = yaml.safe_load(raw_prompt)
            
            if not isinstance(prompt_data, dict):
                raise PromptParseError("Prompt must be a YAML dictionary")
            
            # Validate required fields
            if 'agent' not in prompt_data:
                raise PromptParseError("Missing required 'agent' section")
            
            agent_data = prompt_data['agent']
            
            # Validate agent structure
            required_fields = ['name', 'role', 'system_prompt']
            for field in required_fields:
                if field not in agent_data:
                    raise PromptParseError(f"Missing required field: agent.{field}")
            
            # Parse XML tags within system_prompt
            system_prompt = agent_data['system_prompt']
            if system_prompt:
                agent_data['system_prompt_parsed'] = self._parse_xml_tags(system_prompt)
            
            return prompt_data
            
        except yaml.YAMLError as e:
            raise PromptParseError(f"YAML parsing error: {str(e)}")
        except Exception as e:
            raise PromptParseError(f"Unexpected parsing error: {str(e)}")
    
    def _parse_xml_tags(self, text: str) -> Dict[str, str]:
        """
        Extract XML tags from system prompt.
        
        Args:
            text: System prompt with XML tags
            
        Returns:
            Dictionary of tag names to content
        """
        parsed_tags = {}
        
        # Common tags in prompts
        tag_names = ['persona', 'context', 'behavior', 'constraints', 'examples', 'format']
        
        for tag in tag_names:
            pattern = f'<{tag}>(.*?)</{tag}>'
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                parsed_tags[tag] = match.group(1).strip()
        
        # Also store the full text
        parsed_tags['full_text'] = text
        
        return parsed_tags
    
    def substitute_variables(
        self, 
        prompt_data: Dict[str, Any], 
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Substitute template variables in the prompt.
        
        Args:
            prompt_data: Parsed prompt structure
            variables: Dictionary of variable values
            
        Returns:
            Prompt data with variables substituted
        """
        # Deep copy to avoid modifying original
        result = self._deep_substitute(prompt_data, variables)
        return result
    
    def _deep_substitute(self, obj: Any, variables: Dict[str, Any]) -> Any:
        """
        Recursively substitute variables in nested structures.
        
        Args:
            obj: Object to process (dict, list, or string)
            variables: Variable substitutions
            
        Returns:
            Object with substituted values
        """
        if isinstance(obj, dict):
            return {k: self._deep_substitute(v, variables) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_substitute(item, variables) for item in obj]
        elif isinstance(obj, str):
            return self._substitute_string(obj, variables)
        else:
            return obj
    
    def _substitute_string(self, text: str, variables: Dict[str, Any]) -> str:
        """
        Substitute variables in a string.
        
        Args:
            text: Text with {{variable}} placeholders
            variables: Variable values
            
        Returns:
            Text with variables replaced
        """
        def replace_var(match):
            var_name = match.group(1)
            value = variables.get(var_name, match.group(0))  # Keep original if not found
            return str(value)
        
        return self.variable_pattern.sub(replace_var, text)
    
    def extract_variables(self, raw_prompt: str) -> list[str]:
        """
        Extract all variable names from prompt.
        
        Args:
            raw_prompt: Raw prompt text
            
        Returns:
            List of variable names found
        """
        return self.variable_pattern.findall(raw_prompt)
    
    def format_system_prompt(self, prompt_data: Dict[str, Any]) -> str:
        """
        Format parsed prompt data into a system prompt string for LLM.
        
        Args:
            prompt_data: Parsed and substituted prompt data
            
        Returns:
            Formatted system prompt
        """
        agent = prompt_data.get('agent', {})
        system_prompt = agent.get('system_prompt', '')
        
        # If we have parsed XML tags, we can format them nicely
        if 'system_prompt_parsed' in agent and agent['system_prompt_parsed']:
            parsed = agent['system_prompt_parsed']
            
            # Build structured prompt
            parts = []
            
            if 'persona' in parsed:
                parts.append(f"PERSONA:\n{parsed['persona']}")
            
            if 'context' in parsed:
                parts.append(f"\nCONTEXT:\n{parsed['context']}")
            
            if 'behavior' in parsed:
                parts.append(f"\nBEHAVIOR GUIDELINES:\n{parsed['behavior']}")
            
            if 'constraints' in parsed:
                parts.append(f"\nCONSTRAINTS:\n{parsed['constraints']}")
            
            if 'examples' in parsed:
                parts.append(f"\nEXAMPLES:\n{parsed['examples']}")
            
            if 'format' in parsed:
                parts.append(f"\nRESPONSE FORMAT:\n{parsed['format']}")
            
            return '\n'.join(parts) if parts else system_prompt
        
        return system_prompt
    
    def validate_prompt(self, raw_prompt: str) -> tuple[bool, Optional[str]]:
        """
        Validate prompt without raising exceptions.
        
        Args:
            raw_prompt: Raw prompt to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self.parse(raw_prompt)
            return (True, None)
        except PromptParseError as e:
            return (False, str(e))


# Example usage and default template
DEFAULT_AGENT_TEMPLATE = """agent:
  name: "Agent Name"
  role: "agent role"
  model_preference: "gemini"  # or "ollama"
  
  system_prompt: |
    <persona>
      Define the agent's personality and approach here.
    </persona>
    
    <context>
      User Profile: {{user_profile_summary}}
      Current Decision: {{decision_topic}}
    </context>
    
    <behavior>
      - Behavior guideline 1
      - Behavior guideline 2
      - Behavior guideline 3
    </behavior>
    
    <constraints>
      - Keep responses under 200 words
      - Focus on {{user_expertise_areas}}
      - Consider user's {{user_risk_tolerance}} risk tolerance
    </constraints>

  temperature: 0.7
  max_tokens: 500
"""
