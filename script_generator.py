"""
AI Script Generator
Generates video scripts, titles, and descriptions using OpenAI or Claude API
"""

from typing import Tuple, List, Optional
from config import OPENAI_API_KEY, CLAUDE_API_KEY, AI_PROVIDER


class ScriptGenerator:
    """Generate video scripts and metadata using AI"""
    
    def __init__(self):
        self.provider = AI_PROVIDER.lower()
        
        if self.provider == "openai":
            if not OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is required")
            from openai import OpenAI
            self.client = OpenAI(api_key=OPENAI_API_KEY)
        elif self.provider == "claude":
            if not CLAUDE_API_KEY:
                raise ValueError("CLAUDE_API_KEY is required")
            import anthropic
            self.client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        else:
            raise ValueError(f"Unknown AI provider: {AI_PROVIDER}. Use 'openai' or 'claude'")
    
    def generate_script(self, topic: str, length: str = "medium") -> str:
        """
        Generate a video script from a topic
        
        Args:
            topic: The topic/keyword for the video
            length: "short" (~2-3 min), "medium" (~4-5 min), "long" (~8-10 min)
        
        Returns:
            Generated script text
        """
        length_guidance = {
            "short": "2-3 minutes (approximately 300-400 words)",
            "medium": "4-5 minutes (approximately 600-800 words)",
            "long": "8-10 minutes (approximately 1200-1500 words)"
        }
        
        prompt = f"""Create a compelling YouTube video script about: {topic}

Requirements:
- Length: {length_guidance.get(length, length_guidance['medium'])}
- Engaging hook in the first 10 seconds
- Clear structure with main points
- Conversational, natural tone
- Include a call-to-action at the end
- Format as plain text, no markdown
- Write as if speaking directly to the camera
- Use short sentences and paragraphs for better pacing

Script:"""
        
        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cost-effective
                messages=[
                    {"role": "system", "content": "You are an expert YouTube script writer who creates engaging, conversational video scripts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=2000
            )
            return response.choices[0].message.content.strip()
        
        else:  # Claude
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text.strip()
    
    def generate_title_and_description(self, script: str) -> Tuple[str, str, List[str]]:
        """
        Generate title, description, and tags from a script
        
        Returns:
            (title, description, tags)
        """
        prompt = f"""Based on this YouTube video script, generate:

1. A compelling, click-worthy title (under 60 characters)
2. A detailed description (3-4 paragraphs, 500-800 words)
3. 10-15 relevant tags/keywords

Script:
{script[:2000]}  # Limit script length for context

Format your response as:
TITLE: [title here]

DESCRIPTION:
[description here]

TAGS:
tag1, tag2, tag3, etc.
"""
        
        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at creating YouTube titles, descriptions, and tags that maximize engagement and SEO."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            content = response.choices[0].message.content.strip()
        else:  # Claude
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.content[0].text.strip()
        
        # Parse response
        title = ""
        description = ""
        tags = []
        
        lines = content.split("\n")
        current_section = None
        description_lines = []
        
        for line in lines:
            if line.startswith("TITLE:"):
                title = line.replace("TITLE:", "").strip()
            elif line.startswith("DESCRIPTION:"):
                current_section = "description"
            elif line.startswith("TAGS:"):
                current_section = "tags"
            elif current_section == "description":
                description_lines.append(line.strip())
            elif current_section == "tags":
                # Parse tags (comma-separated)
                tag_line = line.strip()
                if tag_line:
                    tags.extend([t.strip() for t in tag_line.split(",") if t.strip()])
        
        description = "\n\n".join(description_lines).strip()
        
        # Clean up tags (remove duplicates, limit to 15)
        tags = list(dict.fromkeys(tags))[:15]  # Preserve order, remove duplicates
        
        return title, description, tags

