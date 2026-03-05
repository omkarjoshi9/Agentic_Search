# import json
# import yaml
# import os
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from termcolor import colored
from models.groq_models import GroqModel, GroqJSONModel
from utils.steamlit import displayResponse
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
from prompts.prompts import (
    planner_prompt_template,
    selector_prompt_template,
    reporter_prompt_template,
    reviewer_prompt_template,
    router_prompt_template
)
from utils.helper_functions import get_current_utc_datetime, check_for_content
from states.state import AgentGraphState

class Agent:
    def __init__(self, state: AgentGraphState, model=None, server=None, temperature=0, model_endpoint=None, stop=None, guided_json=None):
        self.state = state
        self.model = model
        self.server = server
        self.temperature = temperature
        self.model_endpoint = model_endpoint
        self.stop = stop
        self.guided_json = guided_json
        self.script_ctx = get_script_run_ctx()

    def safe_display_response(self, message):
        """Thread-safe way to display responses"""
        if self.script_ctx:
            add_script_run_ctx(self.script_ctx)
        displayResponse(message)
        
    def get_llm(self, json_model=True):


        if self.server == 'groq':
            return GroqJSONModel(
                model=self.model,
                temperature=self.temperature
            ) if json_model else GroqModel(
                model=self.model,
                temperature=self.temperature
            )


    def update_state(self, key, value):
        self.state = {**self.state, key: value}

class PlannerAgent(Agent):
    def invoke(self, research_question, prompt=planner_prompt_template, feedback=None):
        feedback_value = feedback() if callable(feedback) else feedback
        feedback_value = check_for_content(feedback_value)

        planner_prompt = prompt.format(
            feedback=feedback_value,
            datetime=get_current_utc_datetime()
        )

        messages = [
            {"role": "system", "content": planner_prompt},
            {"role": "user", "content": f"research question: {research_question}"}
        ]

        llm = self.get_llm()
        ai_msg = llm.invoke(messages)
        response = ai_msg.content

        self.update_state("planner_response", response)
        print(colored(f"Planner 👩🏿‍💻: {response}", 'cyan'))
        displayResponse(f"Planner 👩🏿‍💻: {response}")
        return self.state

class SelectorAgent(Agent):
    def invoke(self, research_question, prompt=selector_prompt_template, feedback=None, previous_selections=None, serp=None):
        feedback_value = feedback() if callable(feedback) else feedback
        previous_selections_value = previous_selections() if callable(previous_selections) else previous_selections

        feedback_value = check_for_content(feedback_value)
        previous_selections_value = check_for_content(previous_selections_value)

        selector_prompt = prompt.format(
            feedback=feedback_value,
            previous_selections=previous_selections_value,
            serp=serp().content,
            datetime=get_current_utc_datetime()
        )

        messages = [
            {"role": "system", "content": selector_prompt},
            {"role": "user", "content": f"research question: {research_question}"}
        ]

        llm = self.get_llm()
        ai_msg = llm.invoke(messages)
        response = ai_msg.content

        print(colored(f"selector 🧑🏼‍💻: {response}", 'green'))
        displayResponse(f"selector 🧑🏼‍💻: {response}")
        self.update_state("selector_response", response)
        return self.state

class ReporterAgent(Agent):
    def invoke(self, research_question, prompt=reporter_prompt_template, feedback=None, previous_reports=None, research=None):
        feedback_value = feedback() if callable(feedback) else feedback
        previous_reports_value = previous_reports() if callable(previous_reports) else previous_reports
        research_value = research() if callable(research) else research

        feedback_value = check_for_content(feedback_value)
        previous_reports_value = check_for_content(previous_reports_value)
        research_value = check_for_content(research_value)
        
        reporter_prompt = prompt.format(
            feedback=feedback_value,
            previous_reports=previous_reports_value,
            datetime=get_current_utc_datetime(),
            research=research_value
        )

        messages = [
            {"role": "system", "content": reporter_prompt},
            {"role": "user", "content": f"research question: {research_question}"}
        ]

        llm = self.get_llm(json_model=False)
        ai_msg = llm.invoke(messages)
        response = ai_msg.content

        print(colored(f"Reporter 👨‍💻: {response}", 'yellow'))
        displayResponse(f"Reporter 👨‍💻: {response}")
        self.update_state("reporter_response", response)
        return self.state

class ReviewerAgent(Agent):
    def invoke(self, research_question, loop,prompt=reviewer_prompt_template, reporter=None, feedback=None):
        reporter_value = reporter() if callable(reporter) else reporter
        feedback_value = feedback() if callable(feedback) else feedback


        reporter_value = check_for_content(reporter_value)
        feedback_value = check_for_content(feedback_value)

        self.update_state("loop", loop+1)

        # self.update_state("loop", loop)
        reviewer_prompt = prompt.format(
            reporter=reporter_value,
            state=str(self.state),
            feedback=feedback_value,
            datetime=get_current_utc_datetime(),
            loop=loop
        )

        messages = [
            {"role": "system", "content": reviewer_prompt},
            {"role": "user", "content": f"research question: {research_question}"}
        ]

        llm = self.get_llm()
        try:
            ai_msg = llm.invoke(messages)
            response = ai_msg.content
            print(colored(f"Reviewer 👩🏽‍⚖️: {response}", 'magenta'))
            displayResponse(f"Reviewer 👩🏽‍⚖️: {response}")
            self.update_state("reviewer_response", response)
        except Exception as e:
            response = f"Error in invoking model! {str(e)}"
            print(colored(f"Reviewer 👩🏽‍⚖️: {response}", 'red'))
            self.update_state("reviewer_response", response)
        return self.state
    
class RouterAgent(Agent):
    def invoke(self, feedback=None, research_question=None, prompt=router_prompt_template,):
        feedback_value = feedback() if callable(feedback) else feedback
        feedback_value = check_for_content(feedback_value)

        router_prompt = prompt.format(feedback=feedback_value,loop=self.state["loop"])
        print("Router Prompt", router_prompt)
        messages = [
            {"role": "system", "content": router_prompt},
            {"role": "user", "content": f"research question: {research_question}"}
        ]

        llm = self.get_llm()
        ai_msg = llm.invoke(messages)
        response = ai_msg.content

        print(colored(f"Router 🧭: {response}", 'blue'))
        displayResponse(f"Router 🧭: {response}")
        self.update_state("router_response", response)
        return self.state

class FinalReportAgent(Agent):
    def invoke(self, final_response=None):
        final_response_value = final_response() if callable(final_response) else final_response
        response = final_response_value.content

        print(colored(f"Final Report 📝: {response}", 'blue'))
        displayResponse(f"Final Report 📝: {response}")
        self.update_state("final_reports", response)
        return self.state

class EndNodeAgent(Agent):
    def invoke(self):
        self.update_state("end_chain", "end_chain")
        return self.state