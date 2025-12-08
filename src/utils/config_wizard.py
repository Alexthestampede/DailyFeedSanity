"""
Configuration Wizard for RSS Feed Processor
Interactive setup tool for first-run configuration and ongoing management.
"""
import json
import os
import sys
import urllib.request
import urllib.error
from typing import Dict, Optional, List
from pathlib import Path

# Import our utilities
try:
    from .ollama_inspector import OllamaInspector, ModelCapabilities
except ImportError:
    from ollama_inspector import OllamaInspector, ModelCapabilities


# Configuration file path
CONFIG_FILE = Path(__file__).parent.parent.parent / '.config.json'
RSS_FILE = Path(__file__).parent.parent.parent / 'rss.txt'


# AI Provider Information
AI_PROVIDERS = {
    'ollama': {
        'name': 'Ollama',
        'type': 'local',
        'cost': 'Free',
        'requires_api_key': False,
        'description': 'Run AI models locally on your machine',
        'setup_url': 'https://ollama.com/download',
    },
    'lm_studio': {
        'name': 'LM Studio',
        'type': 'local',
        'cost': 'Free',
        'requires_api_key': False,
        'description': 'Run AI models locally with a GUI interface',
        'setup_url': 'https://lmstudio.ai/',
    },
    'openai': {
        'name': 'OpenAI',
        'type': 'cloud',
        'cost': 'Paid (GPT-4o-mini: ~$0.15/1M input tokens)',
        'requires_api_key': True,
        'description': 'Cloud-based AI service from OpenAI',
        'setup_url': 'https://platform.openai.com/api-keys',
        'warning': 'Using OpenAI API will incur costs charged to your account. You are responsible for all token usage charges.',
    },
    'gemini': {
        'name': 'Google Gemini',
        'type': 'cloud',
        'cost': 'Free tier available, then paid',
        'requires_api_key': True,
        'description': 'Google\'s AI service with generous free tier',
        'setup_url': 'https://aistudio.google.com/app/apikey',
        'warning': 'Gemini has a free tier, but exceeding limits will incur costs at your risk.',
    },
    'claude': {
        'name': 'Anthropic Claude',
        'type': 'cloud',
        'cost': 'Paid (Claude 3.5 Haiku: ~$0.80/1M input tokens)',
        'requires_api_key': True,
        'description': 'Anthropic\'s Claude AI service',
        'setup_url': 'https://console.anthropic.com/',
        'warning': 'Using Claude API will incur costs charged to your account. You are responsible for all token usage charges.',
    },
}


def load_config() -> Optional[Dict]:
    """
    Load configuration from .config.json file.

    Returns:
        Configuration dictionary or None if file doesn't exist
    """
    if not CONFIG_FILE.exists():
        return None

    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading configuration: {e}")
        return None


def save_config(config: Dict) -> bool:
    """
    Save configuration to .config.json file.

    Args:
        config: Configuration dictionary to save

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except IOError as e:
        print(f"Error saving configuration: {e}")
        return False


def should_run_first_setup() -> bool:
    """
    Determine if first-time setup should be run.

    Returns:
        True if configuration doesn't exist or first_run_complete is False, False otherwise
    """
    config = load_config()
    if config is None:
        return True

    # Check if first run was completed
    return not config.get('first_run_complete', False)


def clear_screen():
    """Clear the terminal screen."""
    os.system('clear' if os.name != 'nt' else 'cls')


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_section(title: str):
    """Print a section divider."""
    print(f"\n--- {title} ---\n")


def get_input(prompt: str, default: Optional[str] = None) -> str:
    """
    Get user input with optional default value.

    Args:
        prompt: Prompt to display
        default: Default value if user presses Enter

    Returns:
        User input or default value
    """
    if default:
        response = input(f"{prompt} [{default}]: ").strip()
        return response if response else default
    else:
        response = input(f"{prompt}: ").strip()
        return response


def get_yes_no(prompt: str, default: bool = True) -> bool:
    """
    Get yes/no input from user.

    Args:
        prompt: Prompt to display
        default: Default value (True for yes, False for no)

    Returns:
        True for yes, False for no
    """
    default_str = "Y/n" if default else "y/N"
    response = input(f"{prompt} [{default_str}]: ").strip().lower()

    if not response:
        return default

    return response in ['y', 'yes']


def validate_url(url: str) -> bool:
    """
    Validate if a string is a valid URL.

    Args:
        url: URL to validate

    Returns:
        True if valid URL, False otherwise
    """
    try:
        from urllib.parse import urlparse
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def test_ollama_connection(server_url: str) -> bool:
    """
    Test connection to Ollama server.

    Args:
        server_url: Ollama server URL

    Returns:
        True if connection successful, False otherwise
    """
    try:
        inspector = OllamaInspector(server_url)
        return inspector.test_connection()
    except Exception as e:
        print(f"Connection failed: {e}")
        return False


def test_lm_studio_connection(server_url: str) -> bool:
    """
    Test connection to LM Studio server.

    Args:
        server_url: LM Studio server URL

    Returns:
        True if connection successful, False otherwise
    """
    try:
        url = f"{server_url.rstrip('/')}/v1/models"
        req = urllib.request.Request(url)

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            # Check if response has 'data' field (OpenAI format)
            return 'data' in data

    except Exception as e:
        print(f"Connection failed: {e}")
        return False


def get_lm_studio_models(server_url: str) -> List[Dict]:
    """
    Get list of available models from LM Studio.

    Args:
        server_url: LM Studio server URL

    Returns:
        List of model dictionaries
    """
    try:
        url = f"{server_url.rstrip('/')}/v1/models"
        req = urllib.request.Request(url)

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get('data', [])

    except Exception as e:
        print(f"Failed to get models: {e}")
        return []


def display_model_info(model: ModelCapabilities, index: int):
    """Display formatted model information."""
    print(f"  [{index}] {model.name}")
    print(f"      Parameters: {model.parameters}, Size: {model.size}")
    print(f"      Context: {model.actual_context or model.context_window or 'Unknown'}")
    print(f"      Vision: {'Yes' if model.vision_capable else 'No'}")

    # Warning if context is low
    context = model.actual_context or model.context_window or 0
    if context > 0 and context < 4096:
        print(f"      WARNING: Context size ({context}) is below recommended minimum (4096)")
    print()


def select_ollama_model(inspector: OllamaInspector, model_type: str) -> Optional[str]:
    """
    Interactive model selection for Ollama.

    Args:
        inspector: OllamaInspector instance
        model_type: 'text' or 'vision'

    Returns:
        Selected model name or None
    """
    print_section(f"Select {model_type.title()} Model")

    # Get appropriate models
    if model_type == 'vision':
        models = inspector.get_vision_models(min_context=0)  # Show all vision models
        if not models:
            print("No vision-capable models found on server.")
            print("You can skip vision model selection or add one later.")
            return None
    else:
        models = inspector.get_text_models(min_context=0)  # Show all models
        if not models:
            print("No models found on server.")
            return None

    # Display models
    print(f"Available {model_type} models:\n")
    for i, model in enumerate(models, 1):
        display_model_info(model, i)

    # Get selection
    while True:
        if model_type == 'vision':
            response = input(f"Select model [1-{len(models)}, or 's' to skip]: ").strip()
            if response.lower() == 's':
                return None
        else:
            response = input(f"Select model [1-{len(models)}]: ").strip()

        try:
            index = int(response) - 1
            if 0 <= index < len(models):
                selected = models[index]

                # Warn about low context
                context = selected.actual_context or selected.context_window or 0
                if context > 0 and context < 4096:
                    print(f"\nWARNING: This model has a context size of {context}, which is below")
                    print("the recommended minimum of 4096. It may not work well for long articles.")
                    if not get_yes_no("Continue with this model anyway?", default=False):
                        continue

                return selected.name
            else:
                print(f"Please enter a number between 1 and {len(models)}")
        except ValueError:
            if model_type == 'vision':
                print(f"Please enter a number between 1 and {len(models)}, or 's' to skip")
            else:
                print(f"Please enter a number between 1 and {len(models)}")


def select_lm_studio_model(server_url: str) -> Optional[str]:
    """
    Interactive model selection for LM Studio.

    Args:
        server_url: LM Studio server URL

    Returns:
        Selected model ID or None
    """
    print_section("Select LM Studio Model")

    models = get_lm_studio_models(server_url)

    if not models:
        print("No models found on LM Studio server.")
        print("Make sure you have loaded a model in LM Studio.")
        return None

    # Display models
    print("Available models:\n")
    for i, model in enumerate(models, 1):
        model_id = model.get('id', 'unknown')
        print(f"  [{i}] {model_id}")
    print()

    # Get selection
    while True:
        response = input(f"Select model [1-{len(models)}]: ").strip()

        try:
            index = int(response) - 1
            if 0 <= index < len(models):
                return models[index].get('id')
            else:
                print(f"Please enter a number between 1 and {len(models)}")
        except ValueError:
            print(f"Please enter a number between 1 and {len(models)}")


def configure_ollama() -> Optional[Dict]:
    """
    Configure Ollama provider.

    Returns:
        Configuration dictionary or None if setup failed
    """
    print_section("Ollama Configuration")

    # Get server URL
    default_url = "http://localhost:11434"
    server_url = get_input("Enter Ollama server URL", default=default_url)

    # Test connection
    print("\nTesting connection to Ollama server...")
    if not test_ollama_connection(server_url):
        print("\nFailed to connect to Ollama server.")
        print(f"Please ensure Ollama is running at {server_url}")
        print(f"Visit {AI_PROVIDERS['ollama']['setup_url']} for installation instructions.")
        return None

    print("Connection successful!")

    # Initialize inspector
    inspector = OllamaInspector(server_url)

    # Select text model
    text_model = select_ollama_model(inspector, 'text')
    if not text_model:
        print("Text model is required. Setup cancelled.")
        return None

    # Select vision model (optional)
    if get_yes_no("\nDo you want to configure a vision model?", default=False):
        vision_model = select_ollama_model(inspector, 'vision')
    else:
        vision_model = None

    return {
        'ai_provider': 'ollama',
        'ollama_base_url': server_url,
        'text_model': text_model,
        'vision_model': vision_model,
    }


def configure_lm_studio() -> Optional[Dict]:
    """
    Configure LM Studio provider.

    Returns:
        Configuration dictionary or None if setup failed
    """
    print_section("LM Studio Configuration")

    # Get server URL
    default_url = "http://localhost:1234"
    server_url = get_input("Enter LM Studio server URL", default=default_url)

    # Test connection
    print("\nTesting connection to LM Studio server...")
    if not test_lm_studio_connection(server_url):
        print("\nFailed to connect to LM Studio server.")
        print(f"Please ensure LM Studio is running with a model loaded at {server_url}")
        print(f"Visit {AI_PROVIDERS['lm_studio']['setup_url']} for installation instructions.")
        return None

    print("Connection successful!")

    # Select model
    model = select_lm_studio_model(server_url)
    if not model:
        print("Model selection is required. Setup cancelled.")
        return None

    print(f"\nNote: LM Studio will use the same model ({model}) for both text and vision tasks.")
    print("Make sure your model supports vision if you plan to use image validation.")

    return {
        'ai_provider': 'lm_studio',
        'lm_studio_base_url': server_url,
        'text_model': model,
        'vision_model': model,  # LM Studio uses same model for both
    }


def configure_cloud_provider(provider: str) -> Optional[Dict]:
    """
    Configure a cloud AI provider (OpenAI, Gemini, or Claude).

    Args:
        provider: Provider name ('openai', 'gemini', or 'claude')

    Returns:
        Configuration dictionary or None if setup cancelled
    """
    provider_info = AI_PROVIDERS[provider]
    print_section(f"{provider_info['name']} Configuration")

    # Show cost warning
    if 'warning' in provider_info:
        print("WARNING:")
        print(f"  {provider_info['warning']}")
        print()

        if not get_yes_no("Do you accept the risk and want to continue?", default=False):
            print("Setup cancelled.")
            return None

    # Get API key
    print(f"\nTo use {provider_info['name']}, you need an API key.")
    print(f"Get your API key from: {provider_info['setup_url']}")
    print()

    api_key = get_input(f"Enter your {provider_info['name']} API key")

    if not api_key:
        print("API key is required. Setup cancelled.")
        return None

    # Set default models based on provider
    if provider == 'openai':
        text_model = 'gpt-4o-mini'
        vision_model = 'gpt-4o'
    elif provider == 'gemini':
        text_model = 'gemini-1.5-flash'
        vision_model = 'gemini-1.5-flash'
    elif provider == 'claude':
        text_model = 'claude-3-5-haiku-20241022'
        vision_model = 'claude-3-5-haiku-20241022'
    else:
        text_model = ''
        vision_model = ''

    print(f"\nDefault models will be used:")
    print(f"  Text: {text_model}")
    print(f"  Vision: {vision_model}")
    print()

    return {
        'ai_provider': provider,
        f'{provider}_api_key': api_key,
        'text_model': text_model,
        'vision_model': vision_model,
    }


def select_ai_provider() -> Optional[Dict]:
    """
    Interactive AI provider selection.

    Returns:
        Configuration dictionary or None if setup failed
    """
    print_section("AI Provider Selection")

    print("Available AI providers:\n")
    providers = list(AI_PROVIDERS.keys())

    for i, provider_key in enumerate(providers, 1):
        info = AI_PROVIDERS[provider_key]
        print(f"  [{i}] {info['name']} ({info['type']})")
        print(f"      {info['description']}")
        print(f"      Cost: {info['cost']}")
        print()

    # Get selection
    while True:
        response = input(f"Select AI provider [1-{len(providers)}]: ").strip()

        try:
            index = int(response) - 1
            if 0 <= index < len(providers):
                provider = providers[index]
                break
            else:
                print(f"Please enter a number between 1 and {len(providers)}")
        except ValueError:
            print(f"Please enter a number between 1 and {len(providers)}")

    # Configure selected provider
    if provider == 'ollama':
        return configure_ollama()
    elif provider == 'lm_studio':
        return configure_lm_studio()
    else:
        return configure_cloud_provider(provider)


def add_rss_feed(config: Dict) -> bool:
    """
    Add an RSS feed to the configuration.

    Args:
        config: Configuration dictionary

    Returns:
        True if feed was added, False otherwise
    """
    print_section("Add RSS Feed")

    feed_url = get_input("Enter RSS feed URL")

    if not feed_url:
        print("No URL provided.")
        return False

    if not validate_url(feed_url):
        print("Invalid URL format.")
        return False

    # Initialize rss_feeds list if not present
    if 'rss_feeds' not in config:
        config['rss_feeds'] = []

    # Check if already exists
    if feed_url in config['rss_feeds']:
        print("This feed is already in your configuration.")
        return False

    # Add to config
    config['rss_feeds'].append(feed_url)

    # Also append to rss.txt file
    try:
        # Ensure the file ends with a newline before appending
        if RSS_FILE.exists():
            with open(RSS_FILE, 'rb') as f:
                f.seek(0, 2)  # Go to end of file
                if f.tell() > 0:  # File is not empty
                    f.seek(-1, 2)  # Go to last byte
                    last_char = f.read(1)
                    needs_newline = last_char != b'\n'
                else:
                    needs_newline = False
        else:
            needs_newline = False

        # Append the feed URL
        with open(RSS_FILE, 'a') as f:
            if needs_newline:
                f.write('\n')
            f.write(f"{feed_url}\n")
        print(f"Feed added successfully!")
        return True
    except IOError as e:
        print(f"Error writing to rss.txt: {e}")
        # Remove from config since file write failed
        config['rss_feeds'].remove(feed_url)
        return False


def remove_rss_feed(config: Dict) -> bool:
    """
    Remove an RSS feed from the configuration.

    Args:
        config: Configuration dictionary

    Returns:
        True if feed was removed, False otherwise
    """
    print_section("Remove RSS Feed")

    if 'rss_feeds' not in config or not config['rss_feeds']:
        print("No feeds configured.")
        return False

    # Display feeds
    print("Current feeds:\n")
    for i, feed in enumerate(config['rss_feeds'], 1):
        print(f"  [{i}] {feed}")
    print()

    # Get selection
    response = input(f"Select feed to remove [1-{len(config['rss_feeds'])}, or 'c' to cancel]: ").strip()

    if response.lower() == 'c':
        return False

    try:
        index = int(response) - 1
        if 0 <= index < len(config['rss_feeds']):
            feed_to_remove = config['rss_feeds'][index]

            # Remove from config
            config['rss_feeds'].pop(index)

            # Also remove from rss.txt file
            try:
                # Read all feeds
                with open(RSS_FILE, 'r') as f:
                    feeds = [line.strip() for line in f if line.strip()]

                # Remove the feed
                feeds = [f for f in feeds if f != feed_to_remove]

                # Write back
                with open(RSS_FILE, 'w') as f:
                    for feed in feeds:
                        f.write(f"{feed}\n")

                print(f"Feed removed successfully!")
                return True

            except IOError as e:
                print(f"Error updating rss.txt: {e}")
                # Re-add to config since file write failed
                config['rss_feeds'].insert(index, feed_to_remove)
                return False
        else:
            print(f"Please enter a number between 1 and {len(config['rss_feeds'])}")
            return False
    except ValueError:
        print("Invalid input.")
        return False


def view_all_feeds(config: Dict):
    """Display all configured RSS feeds."""
    print_section("RSS Feeds")

    if 'rss_feeds' not in config or not config['rss_feeds']:
        print("No feeds configured.")
        return

    print(f"Total feeds: {len(config['rss_feeds'])}\n")
    for i, feed in enumerate(config['rss_feeds'], 1):
        print(f"  {i}. {feed}")
    print()


def test_ai_connection(config: Dict):
    """Test connection to configured AI provider."""
    print_section("Test AI Connection")

    provider = config.get('ai_provider', 'ollama')
    print(f"Testing connection to {AI_PROVIDERS[provider]['name']}...\n")

    try:
        if provider == 'ollama':
            url = config.get('ollama_base_url', 'http://localhost:11434')
            if test_ollama_connection(url):
                print("Connection successful!")
                inspector = OllamaInspector(url)
                models = inspector.list_models()
                print(f"\nAvailable models: {', '.join(models)}")
            else:
                print("Connection failed!")

        elif provider == 'lm_studio':
            url = config.get('lm_studio_base_url', 'http://localhost:1234')
            if test_lm_studio_connection(url):
                print("Connection successful!")
                models = get_lm_studio_models(url)
                print(f"\nAvailable models: {', '.join([m.get('id', '') for m in models])}")
            else:
                print("Connection failed!")

        else:
            # Cloud providers
            api_key = config.get(f'{provider}_api_key', '')
            if api_key:
                print(f"API key configured: {api_key[:8]}...")
                print("Note: Cannot test cloud provider connection without making an API call.")
            else:
                print("No API key configured!")

    except Exception as e:
        print(f"Error testing connection: {e}")


def display_config_summary(config: Dict):
    """Display a summary of current configuration."""
    print_header("Current Configuration")

    provider = config.get('ai_provider', 'unknown')
    provider_info = AI_PROVIDERS.get(provider, {'name': provider})

    print(f"AI Provider: {provider_info['name']}")

    if provider == 'ollama':
        print(f"Server URL: {config.get('ollama_base_url', 'Not configured')}")
    elif provider == 'lm_studio':
        print(f"Server URL: {config.get('lm_studio_base_url', 'Not configured')}")
    else:
        api_key = config.get(f'{provider}_api_key', '')
        if api_key:
            print(f"API Key: {api_key[:8]}... (configured)")
        else:
            print("API Key: Not configured")

    print(f"Text Model: {config.get('text_model', 'Not configured')}")
    print(f"Vision Model: {config.get('vision_model', 'Not configured (optional)')}")

    feed_count = len(config.get('rss_feeds', []))
    print(f"RSS Feeds: {feed_count} configured")
    print()


def interactive_menu(config: Dict):
    """
    Display interactive menu for managing configuration.

    Args:
        config: Configuration dictionary
    """
    while True:
        clear_screen()
        display_config_summary(config)

        print("Options:")
        print("  [1] Change AI provider")
        print("  [2] Change text model")
        print("  [3] Change vision model")
        print("  [4] Add RSS feed")
        print("  [5] Remove RSS feed")
        print("  [6] View all feeds")
        print("  [7] Test AI connection")
        print("  [8] Reset configuration")
        print("  [9] Exit")
        print()

        choice = input("Select option [1-9]: ").strip()

        if choice == '1':
            # Change AI provider (requires full reconfiguration)
            print("\nChanging AI provider requires full reconfiguration.")
            if get_yes_no("Continue?", default=False):
                new_config = select_ai_provider()
                if new_config:
                    # Preserve RSS feeds
                    new_config['rss_feeds'] = config.get('rss_feeds', [])
                    new_config['first_run_complete'] = True
                    config.clear()
                    config.update(new_config)
                    save_config(config)
                    print("\nConfiguration updated!")
                    input("Press Enter to continue...")

        elif choice == '2':
            # Change text model
            provider = config.get('ai_provider', 'ollama')

            if provider == 'ollama':
                inspector = OllamaInspector(config.get('ollama_base_url', 'http://localhost:11434'))
                model = select_ollama_model(inspector, 'text')
                if model:
                    config['text_model'] = model
                    save_config(config)
                    print("\nText model updated!")
                    input("Press Enter to continue...")

            elif provider == 'lm_studio':
                model = select_lm_studio_model(config.get('lm_studio_base_url', 'http://localhost:1234'))
                if model:
                    config['text_model'] = model
                    config['vision_model'] = model  # LM Studio uses same model
                    save_config(config)
                    print("\nModel updated!")
                    input("Press Enter to continue...")

            else:
                print("\nManual model configuration for cloud providers:")
                model = get_input("Enter text model name", default=config.get('text_model', ''))
                if model:
                    config['text_model'] = model
                    save_config(config)
                    print("\nText model updated!")
                    input("Press Enter to continue...")

        elif choice == '3':
            # Change vision model
            provider = config.get('ai_provider', 'ollama')

            if provider == 'ollama':
                inspector = OllamaInspector(config.get('ollama_base_url', 'http://localhost:11434'))
                model = select_ollama_model(inspector, 'vision')
                if model:
                    config['vision_model'] = model
                    save_config(config)
                    print("\nVision model updated!")
                elif model is None:
                    # User chose to skip
                    config['vision_model'] = None
                    save_config(config)
                    print("\nVision model cleared!")
                input("Press Enter to continue...")

            elif provider == 'lm_studio':
                print("\nLM Studio uses the same model for text and vision.")
                print("Please use option [2] to change the model.")
                input("Press Enter to continue...")

            else:
                print("\nManual vision model configuration:")
                model = get_input("Enter vision model name", default=config.get('vision_model', ''))
                if model:
                    config['vision_model'] = model
                    save_config(config)
                    print("\nVision model updated!")
                    input("Press Enter to continue...")

        elif choice == '4':
            # Add RSS feed
            if add_rss_feed(config):
                save_config(config)
            input("Press Enter to continue...")

        elif choice == '5':
            # Remove RSS feed
            if remove_rss_feed(config):
                save_config(config)
            input("Press Enter to continue...")

        elif choice == '6':
            # View all feeds
            view_all_feeds(config)
            input("Press Enter to continue...")

        elif choice == '7':
            # Test AI connection
            test_ai_connection(config)
            input("Press Enter to continue...")

        elif choice == '8':
            # Reset configuration
            print("\nThis will delete your current configuration.")
            if get_yes_no("Are you sure?", default=False):
                if CONFIG_FILE.exists():
                    CONFIG_FILE.unlink()
                print("\nConfiguration reset! You will need to run setup again.")
                input("Press Enter to exit...")
                break

        elif choice == '9':
            # Exit
            print("\nExiting configuration wizard.")
            break

        else:
            print("\nInvalid option. Please select 1-9.")
            input("Press Enter to continue...")


def first_run_setup() -> Optional[Dict]:
    """
    Run first-time setup wizard.

    Returns:
        Configuration dictionary or None if setup was cancelled
    """
    clear_screen()
    print_header("RSS Feed Processor - First Run Setup")

    print("Welcome to the RSS Feed Processor configuration wizard!")
    print()
    print("This tool will help you set up:")
    print("  - AI provider for article summarization")
    print("  - Text and vision models")
    print("  - RSS feed sources")
    print()

    if not get_yes_no("Ready to begin setup?", default=True):
        print("\nSetup cancelled.")
        return None

    # Select and configure AI provider
    config = select_ai_provider()

    if not config:
        print("\nSetup cancelled.")
        return None

    # Add RSS feeds
    print_section("RSS Feed Configuration")
    print("You need to add at least one RSS feed to get started.")
    print()

    config['rss_feeds'] = []

    while True:
        if add_rss_feed(config):
            if len(config['rss_feeds']) >= 1:
                if not get_yes_no("\nAdd another feed?", default=True):
                    break
        else:
            if len(config['rss_feeds']) == 0:
                print("\nYou must add at least one feed to continue.")
            else:
                break

    # Mark first run as complete
    config['first_run_complete'] = True

    # Save configuration
    if save_config(config):
        print_section("Setup Complete")
        print("Configuration saved successfully!")
        print()
        print("You can now run the RSS Feed Processor with:")
        print("  python -m src.main")
        print()
        print("To modify your configuration later, run:")
        print("  python -m src.utils.config_wizard")
        print()
        return config
    else:
        print("\nFailed to save configuration.")
        return None


def main():
    """Main entry point for configuration wizard."""
    try:
        # Check if configuration exists
        config = load_config()

        if config and config.get('first_run_complete'):
            # Existing configuration - show menu
            interactive_menu(config)
        else:
            # First run - run setup wizard
            config = first_run_setup()

            if config:
                input("\nPress Enter to continue...")

    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
