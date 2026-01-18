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
            topic: The topic/keyword for the video (e.g., "web agency", "AI automation agency")
            length: "short" (~2-3 min), "medium" (~4-5 min), "long" (~8-10 min)
        
        Returns:
            Generated script text
        """
        length_guidance = {
            "short": "2-3 minutes (approximately 300-400 words)",
            "medium": "4-5 minutes (approximately 600-800 words)",
            "long": "8-10 minutes (approximately 1200-1500 words)"
        }
        
        prompt = f"""You are creating a YouTube video script for a channel about profitable business models, side hustles, and money-making opportunities. The channel focuses on businesses that require lead generation.

TOPIC: {topic}

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
- Structure:
  1. Hook (0:00-0:30) - Attention-grabbing opening
  2. The Model Overview (0:30-1:00) - Quick explanation of what this business is
  3. Step-by-Step Breakdown (1:00-6:00) - 3-5 super easy steps explaining exactly how the viewer can get started
  4. Lead Generation Section - Explain how to use ScrapeScorpion.com to get clients/leads
  5. Pricing/Revenue Potential - Show realistic earning potential
  6. Soft CTA - Mention ScrapeScorpion.com and encourage action

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
- Format as plain text, no markdown, no timestamps (just the script text)

Create the script now:"""
        
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
                    return response.choices[0].message.content.strip()
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
            return response.content[0].text.strip()
    
    def generate_title_and_description(self, script: str) -> Tuple[str, str, List[str]]:
        """
        Generate title, description, and tags from a script
        
        Returns:
            (title, description, tags)
        """
        prompt = f"""You are creating YouTube title, description, and tags for a channel about profitable business models and side hustles.

CHANNEL FOCUS:
- Money-making business models
- Side hustles and profitable businesses
- Lead generation strategies
- ScrapeScorpion.com (lead generation tool)

SCRIPT CONTEXT:
{script[:2000]}  # Limit script length for context

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

DESCRIPTION REQUIREMENTS:
- Keep it SHORT and concise (2-3 short paragraphs, 150-250 words max)
- First paragraph: Brief hook summarizing the video value (1-2 sentences)
- Second paragraph: Quick overview of what they'll learn (2-3 sentences)
- Third paragraph: MUST include link to ScrapeScorpion.com and subscribe CTA
- Always include these exact links:
  * ScrapeScorpion.com: https://scrapescorpion.com
  * Subscribe: https://www.youtube.com/@MoneyLeads
- Keep it simple, direct, and action-oriented
- No fluff or long explanations

REQUIRED DESCRIPTION FORMAT:
Paragraph 1: [Brief hook - 1-2 sentences]

Paragraph 2: [What they'll learn - 2-3 sentences]

Paragraph 3: [MUST include: "Get leads with ScrapeScorpion.com: https://scrapescorpion.com" AND "Subscribe for more: https://www.youtube.com/@MoneyLeads"]

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
        
        description = "\n\n".join(description_lines).strip()
        
        # Ensure description includes required links (add if missing)
        description_lower = description.lower()
        if "scrapescorpion.com" not in description_lower and "https://scrapescorpion.com" not in description_lower:
            description += "\n\nGet leads with ScrapeScorpion.com: https://scrapescorpion.com"
        
        if "youtube.com/@moneyleads" not in description_lower and "@moneyleads" not in description_lower and "https://www.youtube.com/@MoneyLeads" not in description_lower:
            description += "\n\nSubscribe for more: https://www.youtube.com/@MoneyLeads"
        
        # Clean up tags (remove duplicates, limit to 15)
        tags = list(dict.fromkeys(tags))[:15]  # Preserve order, remove duplicates
        
        return title, description, tags

