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
            Generated script text (between 5,200 and 10,000 characters)
        """
        # Target character count: 5,200-10,000 characters
        # This ensures scripts are substantial and detailed
        min_chars = 5200
        max_chars = 10000
        target_chars = 7500  # Aim for middle of range
        
        length_guidance = {
            "short": f"2-3 minutes (approximately {min_chars}-{int(max_chars*0.6)} characters, ~1,000-1,500 words)",
            "medium": f"4-5 minutes (approximately {min_chars}-{max_chars} characters, ~1,300-2,000 words)",
            "long": f"8-10 minutes (approximately {min_chars}-{max_chars} characters, ~1,300-2,000 words)"
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

SCRIPT REQUIREMENTS - CRITICAL LENGTH REQUIREMENT:
- CHARACTER COUNT: The script MUST be between {min_chars} and {max_chars} characters (approximately {target_chars} characters is ideal)
- This is a HARD REQUIREMENT - scripts shorter than {min_chars} characters or longer than {max_chars} characters will be rejected
- Length: {length_guidance.get(length, length_guidance['medium'])}
- Style: Model after the "$1,200/week side hustle" style - fast-paced, engaging, "feels illegal but isn't" vibe
- Hook: Start with a compelling hook in the first 10-15 seconds that grabs attention (e.g., "Most people think making $X means... That's not true.")
- Structure (write naturally, NO section labels):
  1. Hook (0:00-0:30) - Attention-grabbing opening (200-400 characters)
  2. The Model Overview (0:30-1:00) - Quick explanation of what this business is (400-600 characters)
  3. Step-by-Step Breakdown (1:00-6:00) - 3-5 super easy steps explaining exactly how the viewer can get started (3,000-6,000 characters - THIS IS THE MAIN CONTENT)
  4. Lead Generation Section - Explain how to use ScrapeScorpion.com to get clients/leads (800-1,200 characters)
  5. Pricing/Revenue Potential - Show realistic earning potential (600-1,000 characters)
  6. Soft CTA - Mention ScrapeScorpion.com and encourage action (200-400 characters)
- The Step-by-Step Breakdown should be DETAILED and COMPREHENSIVE - this is where most of the character count comes from
- Each step should be 600-1,200 characters with specific, actionable details
- Include examples, specific numbers, and detailed explanations

CRITICAL - ABSOLUTELY NO SECTION LABELS:
- DO NOT use [INTRO], [HOOK], [STEP-BY-STEP BREAKDOWN], [OUTRO], [PRICING/REVENUE POTENTIAL], [LEAD GENERATION SECTION], [THE MODEL OVERVIEW], [SOFT CTA], or ANY other labels in brackets
- DO NOT use any formatting markers, timestamps, or structural labels
- Write ONLY the spoken words - as if you're talking directly to the camera
- Start immediately with the hook sentence - no labels, no brackets, nothing
- The output must be pure script text that can be read directly as a voiceover
- If you include ANY labels or brackets, the script will be rejected

CONTENT REQUIREMENTS:
- Explain the business model clearly and why it's profitable (be detailed and comprehensive)
- Break down the "how to get started" into 3-5 super easy, actionable steps
- Each step should be 600-1,200 characters with SPECIFIC, DETAILED instructions
- Include examples, case studies, specific tools, exact processes, and real numbers
- Always include a detailed section about using ScrapeScorpion.com for lead generation (800-1,200 characters)
- Show realistic pricing and revenue potential with specific numbers and scenarios
- Use conversational, natural tone - write as if speaking directly to the camera
- Use short sentences and paragraphs for better pacing
- Include specific examples, numbers, tool names, website names, and detailed explanations
- Make it feel achievable and not too complicated
- EXPAND on each point - don't be brief, be thorough and detailed
- The script should feel comprehensive and valuable - viewers should feel they got their money's worth

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

CRITICAL - CHARACTER COUNT VERIFICATION:
- Before submitting, count the characters in your script
- The script MUST be between {min_chars} and {max_chars} characters
- If your script is too short, EXPAND the Step-by-Step Breakdown section with more details, examples, and specific instructions
- If your script is too long, trim unnecessary repetition but keep all essential content
- Aim for approximately {target_chars} characters for optimal length

Create the script now (output ONLY the spoken words, no section labels, and ensure it's between {min_chars}-{max_chars} characters):"""
        
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
                        max_tokens=4000  # Increased for 5,200-10,000 character scripts (roughly 1,300-2,500 tokens)
                    )
                    print(f"  ✅ Using model: {model}")
                    script = response.choices[0].message.content.strip()
                    # Remove any section labels that might have been included
                    script = self._clean_script_labels(script)
                    
                    # Validate and regenerate if needed
                    script = self._validate_and_fix_script_length(script, topic, title, model, min_chars, max_chars, target_chars)
                    
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
                max_tokens=4000,  # Increased for 5,200-10,000 character scripts
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            script = response.content[0].text.strip()
            # Remove any section labels that might have been included
            script = self._clean_script_labels(script)
            
            # Validate and regenerate if needed
            script = self._validate_and_fix_script_length(script, topic, title, "claude-3-5-sonnet-20241022", min_chars, max_chars, target_chars)
            
            return script
    
    def _validate_and_fix_script_length(self, script: str, topic: str, title: Optional[str], model: str, min_chars: int, max_chars: int, target_chars: int) -> str:
        """
        Validate script length and regenerate if needed to meet character requirements
        
        Args:
            script: The generated script
            topic: Original topic
            title: Original title (if any)
            model: Model name used
            min_chars: Minimum character count
            max_chars: Maximum character count
            target_chars: Target character count
        
        Returns:
            Script that meets length requirements
        """
        script_length = len(script)
        
        # If script is within acceptable range, return it
        if min_chars <= script_length <= max_chars:
            print(f"  ✅ Script length: {script_length} characters (target: {min_chars}-{max_chars})")
            return script
        
        # If script is too short, regenerate with emphasis on expansion
        if script_length < min_chars:
            print(f"  ⚠️  Script too short: {script_length} characters (need {min_chars}-{max_chars}). Regenerating with expansion...")
            
            expansion_prompt = f"""The previous script was only {script_length} characters, but it needs to be between {min_chars} and {max_chars} characters (target: {target_chars}).

TOPIC: {topic}
TITLE: {title or 'N/A'}

CURRENT SCRIPT (too short):
{script[:500]}...

REQUIREMENTS:
- EXPAND the script significantly to reach {min_chars}-{max_chars} characters
- Add MORE DETAILS to each step in the Step-by-Step Breakdown
- Include MORE specific examples, tool names, website URLs, exact processes
- Add MORE details about pricing, revenue potential, and real-world scenarios
- Expand the ScrapeScorpion.com section with more specific use cases
- Include MORE actionable advice and specific instructions
- Keep the same structure and style, but make everything more comprehensive
- DO NOT add section labels or brackets - just expand the content
- The script should be DETAILED and THOROUGH, not brief

Generate the expanded script now (must be {min_chars}-{max_chars} characters):"""
            
            try:
                if self.provider == "openai":
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are an expert YouTube script writer. You create detailed, comprehensive scripts that are thorough and valuable. You expand content with specific examples, detailed instructions, and actionable advice."},
                            {"role": "user", "content": expansion_prompt}
                        ],
                        temperature=0.8,
                        max_tokens=4000
                    )
                    expanded_script = response.choices[0].message.content.strip()
                else:  # Claude
                    response = self.client.messages.create(
                        model=model,
                        max_tokens=4000,
                        messages=[
                            {"role": "user", "content": expansion_prompt}
                        ]
                    )
                    expanded_script = response.content[0].text.strip()
                
                expanded_script = self._clean_script_labels(expanded_script)
                expanded_length = len(expanded_script)
                
                if min_chars <= expanded_length <= max_chars:
                    print(f"  ✅ Expanded script length: {expanded_length} characters")
                    return expanded_script
                elif expanded_length < min_chars:
                    print(f"  ⚠️  Still too short after expansion: {expanded_length} characters. Using expanded version anyway.")
                    return expanded_script
                else:
                    # Too long, trim it
                    print(f"  ⚠️  Expanded script too long: {expanded_length} characters. Trimming...")
                    return expanded_script[:max_chars]
                    
            except Exception as e:
                print(f"  ⚠️  Failed to expand script: {e}. Using original.")
                return script
        
        # If script is too long, trim it
        if script_length > max_chars:
            print(f"  ⚠️  Script too long: {script_length} characters (max: {max_chars}). Trimming...")
            # Try to trim intelligently - cut from the end but preserve structure
            trimmed = script[:max_chars]
            # Try to end at a sentence boundary
            last_period = trimmed.rfind('.')
            last_exclamation = trimmed.rfind('!')
            last_question = trimmed.rfind('?')
            last_sentence_end = max(last_period, last_exclamation, last_question)
            
            if last_sentence_end > max_chars * 0.9:  # If we can find a sentence end in the last 10%
                trimmed = trimmed[:last_sentence_end + 1]
            
            print(f"  ✅ Trimmed script length: {len(trimmed)} characters")
            return trimmed
        
        return script
    
    def _clean_script_labels(self, script: str) -> str:
        """
        Aggressively remove ALL section labels, intro/outro text, and formatting from script
        """
        import re
        lines = script.split('\n')
        cleaned_lines = []
        skip_until_content = True  # Skip intro text
        
        for line in lines:
            line_stripped = line.strip()
            
            # Skip empty lines initially (we'll add them back for paragraph breaks)
            if not line_stripped:
                continue
            
            # Skip intro phrases
            intro_patterns = [
                r'^alright,?\s+let\'?s\s+dive',
                r'^let\'?s\s+dive',
                r'^here\'?s\s+the\s+script',
                r'^script\s+for\s+our',
                r'^for\s+our\s+youtube',
            ]
            if any(re.search(pattern, line_stripped, re.IGNORECASE) for pattern in intro_patterns):
                skip_until_content = True
                continue
            
            # Skip separator lines
            if re.match(r'^---+$', line_stripped) or re.match(r'^===+$', line_stripped):
                continue
            
            # Skip lines that are ONLY section labels in brackets (with or without timestamps)
            if re.match(r'^\s*\[.*\]\s*$', line_stripped):
                continue
            
            # Remove section labels at the start of lines (with timestamps like [Hook - 0:00-0:30])
            line = re.sub(r'^\s*\[.*?\]\s*-?\s*', '', line)
            
            # Remove any remaining brackets with text inside
            line = re.sub(r'\[.*?\]', '', line)
            
            # Remove common label patterns (case insensitive)
            label_patterns = [
                r'\[INTRO\]', r'\[HOOK\]', r'\[OUTRO\]',
                r'\[STEP-BY-STEP BREAKDOWN\]', r'\[STEP BY STEP\]', r'\[STEP-BY-STEP\]',
                r'\[PRICING/REVENUE POTENTIAL\]', r'\[PRICING\]', r'\[REVENUE\]',
                r'\[LEAD GENERATION SECTION\]', r'\[LEAD GENERATION\]',
                r'\[THE MODEL OVERVIEW\]', r'\[MODEL OVERVIEW\]',
                r'\[SOFT CTA\]', r'\[CTA\]', r'\[CALL TO ACTION\]'
            ]
            for pattern in label_patterns:
                line = re.sub(pattern, '', line, flags=re.IGNORECASE)
            
            # Skip outro phrases
            outro_patterns = [
                r'^and\s+there\s+you\s+have\s+it',
                r'^don\'?t\s+forget\s+to\s+like',
                r'^see\s+you\s+in\s+the\s+next',
                r'^time\s+to\s+turn\s+those\s+dreams',
                r'^thanks\s+for\s+(watching|tuning)',
            ]
            if any(re.search(pattern, line_stripped, re.IGNORECASE) for pattern in outro_patterns):
                # Stop processing - we've hit the outro
                break
            
            # Only add non-empty lines that contain actual content
            if line.strip() and len(line.strip()) > 10:  # Minimum content length
                cleaned_lines.append(line.strip())
                skip_until_content = False
        
        result = '\n'.join(cleaned_lines).strip()
        
        # Final aggressive cleanup - remove any remaining brackets
        if '[' in result or ']' in result:
            result = re.sub(r'\[.*?\]', '', result)
            result = '\n'.join([l.strip() for l in result.split('\n') if l.strip()])
        
        # Remove any remaining intro/outro phrases that might have slipped through
        result_lines = result.split('\n')
        final_lines = []
        for line in result_lines:
            line_stripped = line.strip()
            # Skip if it's an intro/outro phrase
            if any(re.search(pattern, line_stripped, re.IGNORECASE) for pattern in intro_patterns + outro_patterns):
                continue
            if line_stripped and len(line_stripped) > 10:
                final_lines.append(line_stripped)
        
        return '\n'.join(final_lines).strip()
    
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

EXACT TEMPLATE TO USE (copy this exactly - NO bracket labels):

[Write exactly two sentences about what they'll learn in this video]

Lead Generate Tool: ScrapeScorpion.com

Subscribe: Youtube.com/@MoneyLeads

CRITICAL RULES:
1. The hook must be exactly two sentences (no more, no less)
2. NO bracket labels - just write the hook text directly
3. Include one blank line after the hook
4. Then include "Lead Generate Tool: ScrapeScorpion.com" on its own line
5. Then include "Subscribe: Youtube.com/@MoneyLeads" on its own line
6. DO NOT add any other text, paragraphs, or content
7. DO NOT use brackets or labels - just the hook text and the two links
8. Tags will be added separately - DO NOT include them in the description
9. If you deviate from this format, the description will be rejected and reformatted

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
        
        # ALWAYS rebuild description in exact template format (no bracket labels, just content)
        description = f"""{hook_text}

Lead Generate Tool: ScrapeScorpion.com
Subscribe: Youtube.com/@MoneyLeads"""
        
        # Clean up tags (remove duplicates, limit to 15)
        tags = list(dict.fromkeys(tags))[:15]  # Preserve order, remove duplicates
        
        return title, description, tags

