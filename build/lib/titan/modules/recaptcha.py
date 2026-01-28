import logging
import time
import os
import random
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class RecaptchaSolver:
    """
    Solver for Google reCAPTCHA v2 and v3 using Playwright.
    """

    def __init__(self, provider_config: Optional[Dict[str, Any]] = None):
        self.provider_config = provider_config or {}
        self.external_solver = None
        
        if self.provider_config.get("provider") and self.provider_config.get("api_key"):
            from .external_solvers import ExternalSolver
            self.external_solver = ExternalSolver(
                self.provider_config["provider"], 
                self.provider_config["api_key"],
                **self.provider_config
            )

    def solve_v2(self, page) -> bool:
        """
        Attempt to solve reCAPTCHA v2 using the Audio Challenge method.
        Returns True if solved, False otherwise.
        """
        try:
            # 1. Find the reCAPTCHA frame
            logger.info("Recaptcha: Looking for v2 iframe...")
            # Usually the checkbox is in the first iframe, challenge in the second (bframe)
            # But the checkbox frame has src containing 'anchor'
            
            # Wait for any recaptcha frame
            try:
                page.wait_for_selector("iframe[src*='recaptcha/api2/anchor']", state="attached", timeout=5000)
            except:
                logger.info("Recaptcha: No v2 anchor found.")
                return False

            frames = page.frames
            anchor_frame = next((f for f in frames if "recaptcha/api2/anchor" in f.url), None)
            
            if not anchor_frame:
                return False
                
            # 2. Click the checkbox
            logger.info("Recaptcha: Clicking checkbox...")
            checkbox = anchor_frame.wait_for_selector("#recaptcha-anchor", state="visible", timeout=5000)
            checkbox.click()
            
            # 3. Check if solved immediately
            time.sleep(2)
            if self._is_solved(page):
                logger.info("Recaptcha: Solved immediately (One-click)!")
                return True
                
            # 4. If not solved, look for the challenge frame (bframe)
            # The challenge popup
            bframe_selector = "iframe[src*='recaptcha/api2/bframe']"
            try:
                page.wait_for_selector(bframe_selector, state="visible", timeout=5000)
            except:
                logger.warning("Recaptcha: Checkbox clicked but no challenge frame appeared.")
                return False
                
            bframe = next((f for f in page.frames if "recaptcha/api2/bframe" in f.url), None)
            if not bframe:
                return False
                
            # 5. Switch to Audio Challenge
            logger.info("Recaptcha: Switching to audio challenge...")
            try:
                audio_button = bframe.wait_for_selector("#recaptcha-audio-button", state="visible", timeout=5000)
                audio_button.click()
            except:
                logger.warning("Recaptcha: Audio button not found or blocked.")
                return False
                
            # 6. Handle Audio Logic or External Solver
            time.sleep(2)
            
            if self.external_solver:
                logger.info(f"Recaptcha: Using external solver ({self.provider_config['provider']}) for v2...")
                # Extract sitekey from iframe src
                sitekey_match = re.search(r'k=([^&]+)', anchor_frame.url)
                if sitekey_match:
                    site_key = sitekey_match.group(1)
                    token = self.external_solver.solve_recaptcha_v2(site_key, page.url)
                    if token:
                        logger.info("Recaptcha: External solver returned token. Injecting...")
                        page.evaluate(f"document.getElementById('g-recaptcha-response').innerHTML='{token}';")
                        # Some sites need you to call a callback or submit
                        # We try a common injection method
                        page.evaluate(f"if(window.onSuccess) window.onSuccess('{token}');")
                        return True
            
            if self._solve_audio_challenge(bframe):
                # Wait for verification
                time.sleep(2)
                if self._is_solved(page):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Recaptcha V2 Error: {e}")
            return False

    def _solve_audio_challenge(self, frame) -> bool:
        try:
            # Check for "Your computer or network may be sending automated queries" error
            if frame.locator(".rc-doscaptcha-header").is_visible():
                logger.error("Recaptcha: Audio challenge blocked (Automated queries detected).")
                return False

            # Get Audio Link
            download_link = frame.wait_for_selector(".rc-audiochallenge-edownload-link", timeout=5000)
            url = download_link.get_attribute("href")
            
            if not url:
                return False
                
            logger.info(f"Recaptcha: Downloading audio from {url[:30]}...")
            
            # Download audio
            audio_content = requests.get(url).content
            
            # Temp files
            temp_id = random.randint(1000, 99999)
            mp3_file = f"temp_audio_{temp_id}.mp3"
            wav_file = f"temp_audio_{temp_id}.wav"
            
            with open(mp3_file, "wb") as f:
                f.write(audio_content)
                
            # Convert to WAV
            try:
                from pydub import AudioSegment
                sound = AudioSegment.from_mp3(mp3_file)
                sound.export(wav_file, format="wav")
            except Exception as e:
                logger.error(f"Recaptcha: Audio conversion failed (ffmpeg missing?): {e}")
                self._cleanup([mp3_file])
                return False
            except ImportError:
                logger.error("Recaptcha: pydub not installed.")
                self._cleanup([mp3_file])
                return False
                
            # Transcribe
            try:
                import speech_recognition as sr
                recognizer = sr.Recognizer()
                with sr.AudioFile(wav_file) as source:
                    audio = recognizer.record(source)
                    text = recognizer.recognize_google(audio)
                    logger.info(f"Recaptcha: Transcribed text: '{text}'")
            except Exception as e:
                logger.error(f"Recaptcha: Transcription failed: {e}")
                self._cleanup([mp3_file, wav_file])
                return False
                
            self._cleanup([mp3_file, wav_file])
            
            # Enter text
            input_box = frame.wait_for_selector("#audio-response")
            input_box.fill(text)
            
            verify_btn = frame.wait_for_selector("#recaptcha-verify-button")
            verify_btn.click()
            
            return True

        except Exception as e:
            logger.error(f"Recaptcha Audio Logic Error: {e}")
            return False

    def _is_solved(self, page) -> bool:
        # Check if the hidden textarea has a token
        # This is a bit tricky across frames. 
        # Easier: Check if the checkbox has 'aria-checked="true"'
        try:
             # We need to find the anchor frame again properly
             frames = page.frames
             anchor = next((f for f in frames if "recaptcha/api2/anchor" in f.url), None)
             if anchor:
                 checkbox = anchor.locator("#recaptcha-anchor")
                 if checkbox.get_attribute("aria-checked") == "true":
                     return True
        except:
            pass
        return False

    def _cleanup(self, files):
        for f in files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass

    def solve_v3(self, page, action: str = "homepage") -> Optional[str]:
        """
        Attempt to extract reCAPTCHA v3 token.
        Presumes the page calls grecaptcha.execute().
        """
        try:
            logger.info("Recaptcha: Attempting v3 token extraction...")
            
            # 1. Wait for grecaptcha to be loaded
            # We can check window.grecaptcha
            try:
                page.wait_for_function("() => window.grecaptcha && window.grecaptcha.execute", timeout=5000)
            except:
                logger.warning("Recaptcha: grecaptcha not found on page.")
                return None

            # 2. Find sitekey
            # Search DOM for data-sitekey matches just in case code needs it, 
            # but usually we can just call execute if we find the client.
            # However, execute() takes a sitekey. We need it.
            
            sitekey = page.evaluate("""() => {
                // Try finding element with data-sitekey
                const el = document.querySelector('[data-sitekey]');
                if (el) return el.getAttribute('data-sitekey');
                
                // Try finding src including render=KEY
                const script = document.querySelector('script[src*="render="]');
                if (script) {
                    const match = script.src.match(/render=([^&]+)/);
                    if (match) return match[1];
                }
                return null;
            }""")
            
            if not sitekey:
                logger.warning("Recaptcha: Could not find v3 sitekey.")
                return None
                
            logger.info(f"Recaptcha: Found sitekey {sitekey[:10]}...")
            
            # 3. Execute
            token = page.evaluate(f"""async () => {{
                return await window.grecaptcha.execute('{sitekey}', {{action: '{action}'}});
            }}""")
            
            if token:
                logger.info(f"Recaptcha: v3 Token extracted! ({len(token)} chars)")
                return token
            
        except Exception as e:
            logger.error(f"Recaptcha v3 Error: {e}")
            
        return None
