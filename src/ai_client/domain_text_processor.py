"""
Domain-specific text processor for DailyFeedSanity.

Wraps ModuLLe's generic BaseTextProcessor with RSS-specific methods:
- Article summarization with clickbait/ad detection
- Title generation
- Clickbait detection
- Ad/sponsored content detection

All methods build domain prompts and delegate to ModuLLe's generate().
"""

from datetime import datetime
from typing import Optional, Dict, Any
from lib.modulle.utils.response_cleaner import (
    clean_response,
    looks_like_reasoning,
    parse_yes_no,
)
from lib.modulle.utils.json_extractor import extract_json
from ..utils.logging_config import get_logger
from ..config import (
    TEXT_SUMMARY_TEMPERATURE,
    TEXT_TITLE_TEMPERATURE,
    CLICKBAIT_DETECTION_TEMPERATURE,
    CLICKBAIT_AUTHORS,
    AD_DETECTION_TEMPERATURE,
    DECISION_VERDICT_THRESHOLD,
)

logger = get_logger(__name__)


class DomainTextProcessor:
    """
    Domain-specific text processor that wraps ModuLLe's generic text processor.

    Provides article summarization, title generation, clickbait detection,
    and ad detection by crafting domain-specific prompts and calling
    the underlying generic generate() method.
    """

    def __init__(self, text_processor, enable_ad_detection=True,
                 decision_client=None, decision_model=None,
                 decision_threshold=None):
        """
        Initialize domain text processor.

        Args:
            text_processor: ModuLLe BaseTextProcessor instance (has generate() method)
            enable_ad_detection: Enable ad detection feature (default: True)
            decision_client: Optional OllamaClient with system_one() access.
                When set together with decision_model, clickbait/ad verdicts
                are produced by a decision model (noul probabilities) in a
                single /v1/systemone request instead of the generative model.
            decision_model: Decision model name (e.g. 'd1k32:latest', 'clef-flash')
            decision_threshold: Probability of 'true' above which a verdict
                is positive (default from config)
        """
        self.processor = text_processor
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.enable_ad_detection = enable_ad_detection
        self.decision_client = decision_client
        self.decision_model = decision_model
        self.decision_threshold = (
            decision_threshold if decision_threshold is not None
            else DECISION_VERDICT_THRESHOLD
        )

    def generate(self, prompt, system_prompt=None, temperature=0.7, max_tokens=None):
        """
        Pass-through to underlying ModuLLe text processor's generate() method.

        This allows components like feed detectors to call generate() directly
        for non-domain-specific prompts.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens (optional)

        Returns:
            Generated text string, or None on error
        """
        return self.processor.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def detect_clickbait(self, title, text):
        """
        Detect if article is clickbait using AI.

        Args:
            title: Article title
            text: Article text (first 1000 chars used)

        Returns:
            bool: True if clickbait detected, False otherwise
        """
        if not title or not text:
            return False

        excerpt = text[:1000]

        system_prompt = (
            "You are a clickbait detection expert. "
            "Analyze the article title and excerpt to determine if it is clickbait. "
            "Clickbait indicators include: "
            "- Sensationalized or exaggerated headlines "
            "- Misleading titles that don't match the content "
            "- Emotional manipulation tactics "
            "- Exaggerated claims or promises "
            "- 'You won't believe...', 'This one trick...', 'Shocking...' type language "
            "- Withholding key information to force clicks "
            "- Overly dramatic or provocative language "
            "Respond with ONLY 'yes' if it is clickbait, or 'no' if it is not."
        )

        user_prompt = f"Title: {title}\n\nExcerpt: {excerpt}\n\nIs this clickbait?"

        try:
            response = self.processor.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=CLICKBAIT_DETECTION_TEMPERATURE,
            )

            verdict = parse_yes_no(response)

            if verdict is None:
                logger.warning(f"Unclear clickbait detection response: {str(response)[:100] if response else '(empty)'}")
                return False

            if verdict:
                logger.info(f"AI detected clickbait: {title[:50]}...")
            return verdict

        except Exception as e:
            logger.error(f"Error in clickbait detection: {e}")
            return False

    def detect_ad(self, title, text):
        """
        Detect if article is an advertisement or sponsored content.

        Args:
            title: Article title
            text: Article text (first 1000 chars used)

        Returns:
            bool: True if ad/sponsored content detected, False otherwise
        """
        if not title or not text:
            return False

        excerpt = text[:1000]

        system_prompt = (
            "You are an advertisement/sponsored content detection expert. "
            "Analyze the article title and excerpt to determine if it is an ad or sponsored content. "
            "Ad/sponsored indicators include: "
            "- Promotional language for a specific product or service "
            "- 'Sponsored', 'Partner', 'Promoted', 'Ad' labels "
            "- Affiliate links or discount codes "
            "- Overly positive product reviews without criticism "
            "- Press releases disguised as articles "
            "- Content that reads like marketing copy "
            "- 'Brought to you by...', 'In partnership with...' language "
            "Respond with ONLY 'yes' if it is an ad/sponsored, or 'no' if it is not."
        )

        user_prompt = f"Title: {title}\n\nExcerpt: {excerpt}\n\nIs this an advertisement or sponsored content?"

        try:
            response = self.processor.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=AD_DETECTION_TEMPERATURE,
            )

            verdict = parse_yes_no(response)

            if verdict is None:
                logger.warning(f"Unclear ad detection response: {str(response)[:100] if response else '(empty)'}")
                return False

            if verdict:
                logger.info(f"AI detected ad/sponsored content: {title[:50]}...")
            return verdict

        except Exception as e:
            logger.error(f"Error in ad detection: {e}")
            return False

    def detect_verdicts_decision(self, title, text):
        """
        Produce clickbait/ad verdicts via the decision-model stage.

        One /v1/systemone request answers both questions as noul
        probabilities on the article's title and excerpt. Probabilities are
        returned directly - no generated text, no JSON parsing, no
        chain-of-thought to clean.

        Args:
            title: Article title
            text: Article text (first 2000 chars used as state context)

        Returns:
            dict with 'is_clickbait', 'clickbait_probability',
            'is_ad', 'ad_probability', or None on error/failure
        """
        if not self.decision_client or not self.decision_model:
            return None
        if not title:
            return None

        state = f"{title}\n\n{text[:2000]}"

        questions = {
            "is_clickbait": {
                "type": "noul",
                "instructions": (
                    "Is this article's title a sensationalized, misleading, "
                    "or withheld-information clickbait headline rather than "
                    "straightforward news?"
                ),
                "criteria": {
                    "false": "Straightforward, factual, informative headline",
                    "true": "Sensationalized, misleading, or clickbait headline",
                },
            }
        }
        if self.enable_ad_detection:
            questions["is_ad"] = {
                "type": "noul",
                "instructions": (
                    "Is this article an advertisement, sponsored placement, "
                    "or promotional content rather than editorial news?"
                ),
                "criteria": {
                    "false": "Regular editorial news content",
                    "true": "Advertisement, sponsored, or promotional content",
                },
            }

        try:
            logger.info(f"Decision-stage verdicts (model: {self.decision_model})")
            result = self.decision_client.system_one(
                model=self.decision_model,
                state=state,
                questions=questions,
            )

            answers = (result or {}).get("answers", {})
            clickbait_answer = answers.get("is_clickbait", {})
            clickbait_prob = clickbait_answer.get("noul")
            if clickbait_prob is None:
                logger.warning("Decision stage returned no clickbait answer")
                return None

            verdicts = {
                "is_clickbait": clickbait_prob >= self.decision_threshold,
                "clickbait_probability": clickbait_prob,
                "is_ad": False,
                "ad_probability": None,
            }
            logger.info(
                f"Decision clickbait p={clickbait_prob:.3f} "
                f"({title[:50]}...)"
            )

            if self.enable_ad_detection:
                ad_answer = answers.get("is_ad", {})
                ad_prob = ad_answer.get("noul")
                if ad_prob is not None:
                    verdicts["is_ad"] = ad_prob >= self.decision_threshold
                    verdicts["ad_probability"] = ad_prob
                    logger.info(f"Decision ad p={ad_prob:.3f}")

            return verdicts

        except Exception as e:
            logger.warning(f"Decision-stage verdicts failed: {e}")
            return None

    def _gather_verdicts(self, text, title, author):
        """
        Determine clickbait/ad verdicts for an article.

        Prefers the decision-model stage when configured (one system_one
        request, direct probabilities); falls back to legacy generative
        detection calls (or full-JSON verdicts are supplied by the caller)
        otherwise.

        Returns:
            dict with 'is_clickbait', 'clickbait_detected_by', 'is_ad',
            and optionally 'clickbait_probability'/'ad_probability'
        """
        is_clickbait_author = author in CLICKBAIT_AUTHORS if author else False

        decision = self.detect_verdicts_decision(title, text)
        result = {
            "is_clickbait": False,
            "clickbait_detected_by": None,
            "is_ad": False,
        }

        if decision is not None:
            is_clickbait_ai = decision["is_clickbait"]
            if is_clickbait_author and is_clickbait_ai:
                result["clickbait_detected_by"] = "both"
            elif is_clickbait_author:
                result["clickbait_detected_by"] = "author"
            elif is_clickbait_ai:
                result["clickbait_detected_by"] = "decision_model"
            result["is_clickbait"] = is_clickbait_author or is_clickbait_ai
            result["is_ad"] = decision["is_ad"]
            result["clickbait_probability"] = decision["clickbait_probability"]
            if decision.get("ad_probability") is not None:
                result["ad_probability"] = decision["ad_probability"]
            return result

        # Legacy generative path (or decision stage unavailable/failed)
        is_clickbait_ai = False
        if title:
            try:
                is_clickbait_ai = self.detect_clickbait(title, text)
            except Exception as e:
                logger.warning(f"AI clickbait detection failed: {e}")

        if is_clickbait_author and is_clickbait_ai:
            result["clickbait_detected_by"] = "both"
        elif is_clickbait_author:
            result["clickbait_detected_by"] = "author"
        elif is_clickbait_ai:
            result["clickbait_detected_by"] = "ai"
        result["is_clickbait"] = is_clickbait_author or is_clickbait_ai

        if title and self.enable_ad_detection:
            try:
                result["is_ad"] = self.detect_ad(title, text)
            except Exception as e:
                logger.warning(f"AI ad detection failed: {e}")

        return result

    def generate_summary(
        self, text, title=None, author=None, language="English", max_length=500
    ):
        """
        Generate a summary of the article text.

        Args:
            text: Article text to summarize
            title: Article title (for clickbait detection)
            author: Article author (for clickbait detection)
            language: Language to use for the summary
            max_length: Maximum summary length in characters

        Returns:
            dict with 'summary', 'title', 'is_clickbait', 'clickbait_detected_by', 'is_ad',
            or None on error
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for summarization")
            return None

        # Clickbait/ad verdicts (decision stage when configured, else legacy)
        verdicts = self._gather_verdicts(text, title, author)
        is_clickbait = verdicts["is_clickbait"]
        clickbait_detected_by = verdicts["clickbait_detected_by"]
        is_ad = verdicts["is_ad"]

        logger.info(f"Generating summary in {language}")

        # Choose prompt based on clickbait status
        if is_clickbait:
            system_prompt = self._get_clickbait_prompt()
        else:
            system_prompt = self._get_standard_prompt()

        user_prompt = f"IMPORTANT: You MUST respond in {language}. Summarize the following article:\n\n{text[:10000]}"

        try:
            summary = self.processor.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=TEXT_SUMMARY_TEMPERATURE,
            )

            # Strip reasoning traces (also salvages answer after reasoning)
            summary = clean_response(summary)

            if not summary:
                logger.error("Failed to generate summary")
                return None

            # Safety net: reject responses that still look like reasoning
            # (e.g. thinking models with missing tags)
            if looks_like_reasoning(summary):
                logger.warning(
                    "Summary rejected: response contains chain-of-thought reasoning "
                    f"(starts with: {summary[:80]}...)"
                )
                return None

            # Truncate if too long
            if len(summary) > max_length:
                summary = summary[:max_length].rsplit(".", 1)[0] + "."

            # Generate title from summary
            generated_title = self.generate_title(summary, language=language)

            result = {
                "summary": summary,
                "title": generated_title,
                "is_clickbait": is_clickbait,
                "clickbait_detected_by": clickbait_detected_by,
                "is_ad": is_ad,
            }
            if "clickbait_probability" in verdicts:
                result["clickbait_probability"] = verdicts["clickbait_probability"]
            if "ad_probability" in verdicts:
                result["ad_probability"] = verdicts["ad_probability"]
            return result

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return None

    def generate_summary_single_call(
        self, text, title=None, author=None, language="English", max_length=500
    ):
        """
        Generate summary + title + clickbait/ad verdicts in ONE AI call.

        The model returns a JSON object with all fields. Falls back to None
        when no valid JSON can be extracted (caller should skip the article).

        Args:
            text: Article text to summarize
            title: Original article title (context for the model)
            author: Article author (for clickbait detection)
            language: Language to use for summary/title
            max_length: Maximum summary length in characters

        Returns:
            dict with 'summary', 'title', 'is_clickbait', 'clickbait_detected_by',
            'is_ad', or None on error
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for summarization")
            return None

        is_clickbait_author = author in CLICKBAIT_AUTHORS if author else False

        # Two-stage: decision model owns verdicts, so the generative call
        # only produces summary + title
        use_decision_verdicts = bool(self.decision_client and self.decision_model)
        ad_instruction = (
            "Determine if it is an advertisement or sponsored content"
            if self.enable_ad_detection and not use_decision_verdicts
            else None
        )

        system_prompt = self._get_single_call_prompt(
            language, ad_instruction, include_verdicts=not use_decision_verdicts
        )
        user_prompt = (
            f"Article title: {title or '(none)'}\n\n"
            f"Article text:\n{text[:10000]}\n\n"
            "Respond with ONLY the JSON object described in the system prompt."
        )

        try:
            logger.info(f"Generating summary + verdicts in one call (language: {language})")
            raw = self.processor.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=TEXT_SUMMARY_TEMPERATURE,
            )

            data = extract_json(raw)
            if not data:
                logger.warning(
                    f"No JSON found in response: {str(raw)[:120] if raw else '(empty)'}"
                )
                return None

            summary = clean_response(str(data.get("summary", "")))
            if not summary:
                logger.error("JSON response missing usable 'summary' field")
                return None

            if looks_like_reasoning(summary):
                logger.warning(
                    "Summary rejected: reasoning leaked into 'summary' field "
                    f"(starts with: {summary[:80]}...)"
                )
                return None

            # Truncate if too long
            if len(summary) > max_length:
                summary = summary[:max_length].rsplit(".", 1)[0] + "."

            # Title: use generated one, fall back to original
            generated_title = clean_response(str(data.get("title", "")))
            if not generated_title or looks_like_reasoning(generated_title):
                generated_title = title or "Article Summary"
            generated_title = generated_title.strip().strip("\"'")
            if len(generated_title) > 80:
                generated_title = generated_title[:77] + "..."

            if use_decision_verdicts:
                # Decision stage supplies verdicts (already computed with the
                # original title/excerpt below)
                verdicts = self._gather_verdicts(text, title, author)
                result = {
                    "summary": summary,
                    "title": generated_title,
                    "is_clickbait": verdicts["is_clickbait"],
                    "clickbait_detected_by": verdicts["clickbait_detected_by"],
                    "is_ad": verdicts["is_ad"],
                }
                if "clickbait_probability" in verdicts:
                    result["clickbait_probability"] = verdicts["clickbait_probability"]
                if "ad_probability" in verdicts:
                    result["ad_probability"] = verdicts["ad_probability"]
                return result

            # Verdicts come from this same JSON response (no decision model)
            def _to_bool(value):
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    verdict = parse_yes_no(str(value))
                    if verdict is not None:
                        return verdict
                    normalized = str(value).strip().lower()
                    if normalized in ("true", "1"):
                        return True
                    if normalized in ("false", "0"):
                        return False
                return False

            is_clickbait_ai = _to_bool(data.get("is_clickbait"))
            is_clickbait = is_clickbait_author or is_clickbait_ai

            if is_clickbait_author and is_clickbait_ai:
                clickbait_detected_by = "both"
            elif is_clickbait_author:
                clickbait_detected_by = "author"
            elif is_clickbait_ai:
                clickbait_detected_by = "ai"
            else:
                clickbait_detected_by = None

            is_ad = _to_bool(data.get("is_ad")) if self.enable_ad_detection else False

            return {
                "summary": summary,
                "title": generated_title,
                "is_clickbait": is_clickbait,
                "clickbait_detected_by": clickbait_detected_by,
                "is_ad": is_ad,
            }

        except Exception as e:
            logger.error(f"Error in single-call summary: {e}")
            return None

    def _get_single_call_prompt(self, language, ad_instruction=None, include_verdicts=True):
        """
        Get system prompt for the single-call JSON workflow.

        Args:
            language: Language for the generated summary/title
            ad_instruction: Description of the ad-detection task, or None
                to ask the model to always report is_ad as false
            include_verdicts: When False (decision-model stage owns
                verdicts), the prompt asks only for title + summary

        Returns:
            System prompt string
        """
        if include_verdicts:
            clickbait_rule = (
                "  \"is_clickbait\": true if the article title is clickbait "
                "(sensationalized, misleading, emotional manipulation, withholding "
                "key information), otherwise false,\n"
            )
            ad_rule = (
                f"  \"is_ad\": true if the article is an advertisement or sponsored "
                f"content ({ad_instruction or 'sponsored placement detection'}), otherwise false"
                if ad_instruction
                else "  \"is_ad\": always false (ad detection is disabled)"
            )
        else:
            # Decision-model stage supplies verdicts; generative call stays
            # focused on summary + title
            clickbait_rule = ""
            ad_rule = ""

        return (
            f"Today is {self.current_date}. "
            "You are a professional news processing assistant. "
            "Analyze the article and respond with ONLY a JSON object, no other text, "
            "with exactly these fields:\n"
            "{\n"
            "  \"title\": a clear, informative headline for the article "
            "(max 80 characters, no clickbait language),\n"
            "  \"summary\": an objective, factual summary of the article "
            "(100-300 words, neutral professional tone, focus on key facts),\n"
            f"{clickbait_rule}"
            f"{ad_rule}\n"
            "}\n"
            f"Write \"title\" and \"summary\" in {language}. "
            "Output raw JSON only - no markdown fences, no explanations."
        )

    def generate_title(self, summary, language="English"):
        """
        Generate a concise title from the summary.

        Args:
            summary: Article summary
            language: Language to use for the title

        Returns:
            Generated title string
        """
        logger.debug(f"Generating title in {language}")

        system_prompt = (
            "You are a professional headline writer. "
            "Generate a clear, concise, and informative headline (max 80 characters) "
            "based on the provided summary. "
            "Do not use clickbait language or sensationalism."
        )

        user_prompt = f"IMPORTANT: You MUST respond in {language}. Generate a headline for this summary:\n\n{summary}"

        try:
            title = self.processor.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=TEXT_TITLE_TEMPERATURE,
            )

            title = clean_response(title)

            if not title or looks_like_reasoning(title):
                return "Article Summary"

            title = title.strip().strip("\"'")
            if len(title) > 80:
                title = title[:77] + "..."

            return title

        except Exception as e:
            logger.error(f"Error generating title: {e}")
            return "Article Summary"

    def summarize_article(self, article_data):
        """
        Summarize an article from structured data.

        Args:
            article_data: dict with 'text', 'title', 'author', 'url' fields

        Returns:
            dict with summary results, or None on error
        """
        text = article_data.get("text", "")
        author = article_data.get("author")
        original_title = article_data.get("title", "")
        url = article_data.get("url", "")

        logger.info(f"Summarizing article: {original_title[:50]}...")

        result = self.generate_summary(text, title=original_title, author=author)

        if result:
            result["original_title"] = original_title
            result["url"] = url
            result["author"] = author

        return result

    def _get_standard_prompt(self):
        """Get standard summarization system prompt."""
        return (
            f"Today is {self.current_date}. "
            "You are a professional news summarizer. "
            "Provide clear, concise, and objective summaries of articles. "
            "Focus on the key facts, main points, and important details. "
            "Maintain a neutral, professional tone. "
            "Keep summaries between 100-300 words."
        )

    def _get_clickbait_prompt(self):
        """Get clickbait-specific summarization system prompt."""
        return (
            f"Today is {self.current_date}. "
            "This article shows signs of clickbait or sensationalism. "
            "Provide an objective, factual summary that strips away dramatic language "
            "and focuses on verifiable facts only. "
            "If no substantial facts exist, state 'Clickbait article with no substantial content.' "
            "Maintain a neutral, skeptical tone and avoid amplifying sensationalism."
        )
