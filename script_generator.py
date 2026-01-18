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
    
    def generate_script(self, topic: str, title: Optional[str] = None, length: str = "medium") -> str:
        """
        Generate a video script from a topic
        
        Args:
            topic: The topic/keyword for the video (e.g., "web agency", "AI automation agency")
            title: Optional title to provide context for script generation
            length: "short" (~2-3 min), "medium" (~4-5 min), "long" (~8-10 min)
        
        Returns:
            Generated script text
        """
        length_guidance = {
            "short": "2-3 minutes (approximately 300-400 words)",
            "medium": "4-5 minutes (approximately 600-800 words)",
            "long": "8-10 minutes (approximately 1200-1500 words)"
        }
        
        title_context = ""
        if title:
            title_context = f"\nVIDEO TITLE: {title}\n- Use this title as context to ensure the script aligns with the title's promise and value proposition\n- The script should deliver on what the title promises\n"
        
        prompt = f"""You are creating a YouTube video script for a channel about profitable business models, side hustles, and money-making opportunities. The channel focuses on businesses that require lead generation.

TOPIC: {topic}{title_context}

CHANNEL CONTEXT:
- This is a YouTube channel about money, business models, profitable businesses, and side hustles
- The channel explains business models and teaches viewers how to get started
- Always mention ScrapeScorpion.com (Scrape Scorpion) as the tool for generating leads
- Focus on businesses that need lead generation: web agencies, AI agencies, AI automation companies, voice agent companies, website building companies, service-based companies, B2B companies

SCRAPE SCORPION INFORMATION:
- ScrapeScorpion.com is a cloud-based lead generation tool
- It scrapes Google Maps, Yelp, Meta Ads, Zillow, and Instagram to find business leads
- Provides: business name, phone number, address, website, and other contact info
- No coding required, just click and run
- Can generate thousands of leads in minutes
- Multiple export options (CSV, JSON, Excel, XML, SQL, PDF)
- Affordable pricing starting at $9.99/month
- Free trial available
- Perfect for agencies, sales professionals, and service businesses

SCRIPT REQUIREMENTS:
- Length: {length_guidance.get(length, length_guidance['medium'])}
- Style: Model after the "$1,200/week side hustle" style - fast-paced, engaging, "feels illegal but isn't" vibe
- Hook: Start with a compelling hook in the first 10-15 seconds that grabs attention (e.g., "Most people think making $X means... That's not true.")
- Structure (write naturally, NO section labels):
  1. Hook (0:00-0:30) - Attention-grabbing opening
  2. The Model Overview (0:30-1:00) - Quick explanation of what this business is
  3. Step-by-Step Breakdown (1:00-6:00) - 3-5 super easy steps explaining exactly how the viewer can get started
  4. Lead Generation Section - Explain how to use ScrapeScorpion.com to get clients/leads
  5. Pricing/Revenue Potential - Show realistic earning potential
  6. Soft CTA - Mention ScrapeScorpion.com and encourage action

CRITICAL - ABSOLUTELY NO SECTION LABELS:
- DO NOT use [INTRO], [HOOK], [STEP-BY-STEP BREAKDOWN], [OUTRO], [PRICING/REVENUE POTENTIAL], [LEAD GENERATION SECTION], [THE MODEL OVERVIEW], [SOFT CTA], or ANY other labels in brackets
- DO NOT use any formatting markers, timestamps, or structural labels
- Write ONLY the spoken words - as if you're talking directly to the camera
- Start immediately with the hook sentence - no labels, no brackets, nothing
- The output must be pure script text that can be read directly as a voiceover
- If you include ANY labels or brackets, the script will be rejected

CONTENT REQUIREMENTS:
- Explain the business model clearly and why it's profitable
- Break down the "how to get started" into 3-5 super easy, actionable steps
- Each step should be specific and easy to follow
- Always include a section about using ScrapeScorpion.com for lead generation
- Show realistic pricing and revenue potential
- Use conversational, natural tone - write as if speaking directly to the camera
- Use short sentences and paragraphs for better pacing
- Include specific examples and numbers when possible
- Make it feel achievable and not too complicated

BUSINESS MODELS TO COVER (if topic is generic):
- Web agencies (using CVG framework: Cursor, Vercel, GitHub)
- AI agencies
- AI automation companies
- Voice agent companies
- Website building companies
- Service-based companies (plumbers, electricians, contractors, etc.)
- B2B companies

IMPORTANT:
- Always mention ScrapeScorpion.com as the solution for getting leads
- Explain how lead generation is essential for this business model
- Make the steps super actionable - viewer should be able to start immediately
- Keep it engaging and fast-paced
- Format as plain text, no markdown, no timestamps, NO SECTION LABELS
- Write ONLY the words that will be spoken - no brackets, no labels, no formatting markers
- The output should be ready to read directly as a voiceover script

Create the script now (output ONLY the spoken words, no section labels):"""
        
        if self.provider == "openai":
            # Try models in order: gpt-3.5-turbo (most reliable), then gpt-4o
            # Removed gpt-4o-mini as it's not available for this project
            models_to_try = ["gpt-3.5-turbo", "gpt-4o"]
            last_error = None
            
            for model in models_to_try:
                try:
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are an expert YouTube script writer specializing in profitable business models, side hustles, and money-making opportunities. You create engaging, fast-paced scripts that explain business models clearly and always incorporate lead generation strategies using ScrapeScorpion.com. Your scripts follow the '$1,200/week side hustle' style - attention-grabbing hooks, simple step-by-step breakdowns, and actionable advice."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.8,
                        max_tokens=3000  # Increased for longer, more detailed scripts
                    )
                    print(f"  ✅ Using model: {model}")
                    script = response.choices[0].message.content.strip()
                    # Remove any section labels that might have been included
                    script = self._clean_script_labels(script)
                    return script
                except Exception as e:
                    last_error = e
                    error_msg = str(e)
                    print(f"  ⚠️  Model {model} failed: {error_msg[:100]}")
                    # Continue to next model
                    continue
            
            # If all models failed, raise the last error with more context
            raise Exception(f"All OpenAI models failed. Last error: {last_error}")
        
        else:  # Claude
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=3000,  # Increased for longer, more detailed scripts
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            script = response.content[0].text.strip()
            # Remove any section labels that might have been included
            script = self._clean_script_labels(script)
            return script
    
    def _clean_script_labels(self, script: str) -> str:
        """
        Aggressively remove ALL section labels and formatting from script
        """
        import re
        lines = script.split('\n')
        cleaned_lines = []
        
        for line in lines:
            original_line = line
            # Remove any lines that are ONLY section labels in brackets
            if re.match(r'^\s*\[.*\]\s*$', line):
                continue
            
            # Remove section labels at the start of lines (more aggressive)
            line = re.sub(r'^\s*\[.*?\]\s*', '', line)
            
            # Remove any remaining brackets with text inside (catch any missed labels)
            line = re.sub(r'\[.*?\]', '', line)
            
            # Remove common label patterns
            label_patterns = [
                r'\[INTRO\]', r'\[HOOK\]', r'\[OUTRO\]',
                r'\[STEP-BY-STEP BREAKDOWN\]', r'\[STEP BY STEP\]',
                r'\[PRICING/REVENUE POTENTIAL\]', r'\[PRICING\]',
                r'\[LEAD GENERATION SECTION\]', r'\[LEAD GENERATION\]',
                r'\[THE MODEL OVERVIEW\]', r'\[MODEL OVERVIEW\]',
                r'\[SOFT CTA\]', r'\[CTA\]'
            ]
            for pattern in label_patterns:
                line = re.sub(pattern, '', line, flags=re.IGNORECASE)
            
            # Only add non-empty lines
            if line.strip():
                cleaned_lines.append(line.strip())
        
        result = '\n'.join(cleaned_lines).strip()
        
        # Final check - if result still contains brackets, remove them
        if '[' in result or ']' in result:
            result = re.sub(r'\[.*?\]', '', result)
            result = '\n'.join([l.strip() for l in result.split('\n') if l.strip()])
        
        return result
    
    def generate_title_and_description(self, topic: str) -> Tuple[str, str, List[str]]:
        """
        Generate title, description, and tags from a topic (no script needed)
        
        Args:
            topic: The topic/keyword for the video
        
        Returns:
            (title, description, tags)
        """
        prompt = f"""You are creating YouTube title, description, and tags for a channel about profitable business models and side hustles.

CHANNEL FOCUS:
- Money-making business models
- Side hustles and profitable businesses
- Lead generation strategies
- ScrapeScorpion.com (lead generation tool)

TOPIC: {topic}

TITLE REQUIREMENTS:
- Create a compelling, click-worthy title (under 60 characters)
- Model after titles like: "The $X/Month [Business] That Feels Illegal (But Isn't)" or "How I Get [Result] Using [Method]"
- Include numbers when possible (e.g., "$10K/month", "30 days", "$1,200/week")
- Make it intriguing and promise value
- Examples of good titles:
  * "The $10K/Month Website Agency System That Feels Illegal (But Isn't)"
  * "I Built a Web Agency From My Laptop Using 2 Free Tools"
  * "How I Get Clients on Autopilot (And Build Sites for Free)"
  * "If I Had 30 Days to Make $10K, I'd Do This"

DESCRIPTION REQUIREMENTS - CRITICAL:
- You MUST use this EXACT template format - copy it precisely, character for character
- DO NOT modify the format, labels, or structure in any way
- DO NOT add extra text, paragraphs, or content beyond what's specified

EXACT TEMPLATE TO USE (copy this exactly):

[HOOK, keep it very short. like two sentences] [Write exactly two sentences about what they'll learn in this video]

[Always include these in this exact format. nothing more or less:]

Lead Generate Tool: ScrapeScorpion.com

Subscribe: Youtube.com/@MoneyLeads

CRITICAL RULES:
1. The hook must be exactly two sentences (no more, no less)
2. Use the EXACT label format: [HOOK, keep it very short. like two sentences]
3. Use the EXACT label format: [Always include these in this exact format. nothing more or less:]
4. Include the blank lines exactly as shown (one blank line after hook, one after the label)
5. DO NOT add any other text, paragraphs, or content
6. Tags will be added separately - DO NOT include them in the description
7. If you deviate from this format, the description will be rejected and reformatted

TAGS REQUIREMENTS:
- Generate 10-15 relevant tags/keywords
- Include: business model name, side hustle, lead generation, ScrapeScorpion, profitable business, make money online, etc.
- Mix of broad and specific tags
- Include variations of the main topic

Format your response as:
TITLE: [title here]

DESCRIPTION:
[description here - keep it SHORT, 2-3 paragraphs max, MUST include the links]

TAGS:
tag1, tag2, tag3, etc.

Generate now:"""
        
        if self.provider == "openai":
            # Try models in order: gpt-3.5-turbo (most reliable), then gpt-4o
            # Removed gpt-4o-mini as it's not available for this project
            models_to_try = ["gpt-3.5-turbo", "gpt-4o"]
            last_error = None
            content = None
            
            for model in models_to_try:
                try:
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are an expert at creating YouTube titles, descriptions, and tags for a channel about profitable business models and side hustles. You specialize in click-worthy titles with numbers and compelling hooks, SEO-optimized descriptions that mention ScrapeScorpion.com, and relevant tags that maximize discoverability."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=800  # Reduced for shorter descriptions (150-250 words)
                    )
                    print(f"  ✅ Using model: {model}")
                    content = response.choices[0].message.content.strip()
                    break
                except Exception as e:
                    last_error = e
                    error_msg = str(e)
                    print(f"  ⚠️  Model {model} failed: {error_msg[:100]}")
                    # Continue to next model
                    continue
            
            if not content:
                raise Exception(f"All OpenAI models failed. Last error: {last_error}")
        else:  # Claude
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,  # Reduced for shorter descriptions (150-250 words)
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
        
        # ALWAYS reformat description to exact template - don't trust AI output
        # Extract hook text from description (first 1-2 sentences that aren't labels)
        hook_text = ""
        for line in description_lines:
            line_stripped = line.strip()
            # Skip label lines, empty lines, and link lines
            if (line_stripped and 
                not line_stripped.startswith("[") and 
                "scrapescorpion" not in line_stripped.lower() and 
                "subscribe" not in line_stripped.lower() and 
                "youtube" not in line_stripped.lower() and
                "lead generate" not in line_stripped.lower()):
                # Extract first meaningful text as hook
                if not hook_text:
                    hook_text = line_stripped
                else:
                    # Add second sentence if we don't have 2 sentences yet
                    if hook_text.count('.') < 2:
                        hook_text += " " + line_stripped
                    else:
                        break
                # Stop after 2 sentences
                if hook_text.count('.') >= 2:
                    break
        
        # If no hook found, use default
        if not hook_text or len(hook_text) < 20:
            hook_text = "Looking to dive into the world of profitable business models and side hustles? In this video, we'll uncover the secrets of starting your own business."
        
        # Ensure hook is exactly 2 sentences (truncate if longer)
        sentences = hook_text.split('.')
        if len(sentences) > 2:
            hook_text = '. '.join(sentences[:2])
            if not hook_text.endswith('.'):
                hook_text += '.'
        
        # ALWAYS rebuild description in exact template format (never trust AI output)
        description = f"""[HOOK, keep it very short. like two sentences] {hook_text}

[Always include these in this exact format. nothing more or less:]

Lead Generate Tool: ScrapeScorpion.com

Subscribe: Youtube.com/@MoneyLeads"""
        
        # Clean up tags (remove duplicates, limit to 15)
        tags = list(dict.fromkeys(tags))[:15]  # Preserve order, remove duplicates
        
        return title, description, tags

