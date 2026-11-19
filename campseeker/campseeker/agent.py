"""ADK entry point discovered by `adk run nps_camping` / `adk web .`."""
import os
from google.adk.agents import Agent
from google.adk.apps import App
from .config import load_environment
from .instructions import INSTRUCTION
from .tools import search_parks, get_campgrounds, get_alerts

load_environment()

root_agent = Agent(
    name='campseeker',
    model=os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
    description='Read-only, evidence-grounded NPS campground discovery and comparison.',
    instruction=INSTRUCTION,
    tools=[search_parks, get_campgrounds, get_alerts],
)

app = App(
    root_agent=root_agent,
    name="campseeker",
)