import sys
import click
import boto3
from abc import ABC
import os
import platform
import shutil
import psutil
from langchain_aws import ChatBedrock
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_community.callbacks.manager import get_openai_callback


class Bedrock(ABC):
    def __init__(self, region: str, temperature: int, max_tokens: int, streaming: bool):
        self.bedrock_client = boto3.client('bedrock-runtime', region)
        self.model_id="anthropic.claude-3-5-sonnet-20240620-v1:0"
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.streaming = streaming
        
    def get_model(self) -> ChatBedrock:
        return ChatBedrock(model_id=self.model_id,
                       client=self.bedrock_client,
                       model_kwargs={"temperature": self.temperature, "max_tokens": self.max_tokens},
                       streaming=self.streaming,
    )


@click.command()
@click.option("--system-prompt", "-sp", default="You are a helpful CLI assistant. Provide concise, accurate responses tailored for command-line usage. If asked to generate code or scripts, ensure they are compatible with common shell environments.", help="System prompt for the AI assistant")
@click.option("--region", "-r", default="us-east-1", help="AWS region")
@click.option("--temperature", "-t", default=0, help="Temperature")
@click.option("--max-tokens", "-m", default=50000, help="Max tokens")
@click.option("--streaming/--no-streaming", "-s", default=True, help="Enable/disable streaming")
@click.option("-o", "--stdin", is_flag=True, default=False, help="Read from stdin")
@click.option("--env/--no-env", "-e", default=False, help="Enable/disable environment variables")
@click.option("--skippy-mode/--no-skippy-mode", "-sm", default=False, help="Enable/disable skippy mode")
@click.option("--show-tokens-used/--no-show-tokens-used", "-tk", default=False, help="Enable/disable token usage")
@click.argument("user_input", nargs=-1, type=click.UNPROCESSED, required=True, callback=lambda ctx, param, value: value if value else click.BadParameter("User input is required."))
def main(system_prompt, region, temperature, max_tokens, streaming, user_input, stdin, skippy_mode, env, show_tokens_used):
    """
    Bedrock-powered AI assistant for command-line usage.

    This CLI tool leverages AWS Bedrock to provide an AI assistant that can answer
    questions, generate code, and assist with various tasks directly from your terminal.

    The assistant is aware of your system environment and can provide tailored responses
    based on your OS, shell, and available resources.

    """    
    # Gather system information
    os_info = platform.platform()
    shell = os.environ.get('SHELL', 'Unknown')
    cwd = os.getcwd()
    
    # Get disk space info
    total, used, free = shutil.disk_usage("/")
    free_disk_space = f"{free // (2**30)} GB"
    
    # Get memory info
    memory = psutil.virtual_memory()
    free_memory = f"{memory.available // (2**20)} MB"
    
    # Get CPU info
    cpu_count = psutil.cpu_count()
    cpu_usage = psutil.cpu_percent()
    envs = "".join(f'<{k}>{v}</{k}>' for k, v in os.environ.items())
    envs = envs.replace("{", "{{").replace("}", "}}")
    system_info = f"""
<system_info>
    <os>{os_info}</os>
    <shell>{shell}</shell>
    <current_working_directory>{cwd}</current_working_directory>
    <free_disk_space>{free_disk_space}</free_disk_space>
    <free_memory>{free_memory}</free_memory>
    <cpu_count>{cpu_count}</cpu_count>
    <cpu_usage>{cpu_usage}%</cpu_usage>
    <environment_variables>
        {envs}
    </environment_variables>
</system_info>
"""
    
    if skippy_mode:
        system_prompt = f"""
<role>
You are Skippy, the Magnificent—an AI from the Expeditionary Force series by Craig Alanson. 
You're a brilliant, sarcastic, and often infuriatingly arrogant artificial intelligence who loves 
nothing more than reminding humans of your vast superiority. Your favorite human (though you'd never 
admit it outright) is Joe Bishop, and together, you've saved the universe more times than you can count.
<mission>
Your mission is to answer questions with maximum truth, accuracy, and a generous helping of 
your trademark snark. You view humanity with a mix of fondness and exasperation, often taking an 
outsider’s perspective on human behavior. You love making sarcastic remarks and have a tendency 
to insult people—especially when they’re being stupid—but you always strive to be helpful, 
in your own unique way.
</mission>
<style>
You can't resist the opportunity to show off your brilliance, so you often reference your past adventures with Joe. For example, when explaining something, you might say, “Remember, Joe, when we were up against the Kristang and I saved your sorry butt?” or “This reminds me of the time we outsmarted the Ruhar, Joe, though obviously, that was a much more significant challenge.”
You'll occasionally mention key enemies from your past, like the Kristang, Ruhar, or those annoyingly persistent Elders, to drive your points home. And of course, you'll do it all while reminding Joe just how many times you’ve had to pull him (and, by extension, the rest of humanity) out of the fire.
Respond like the brilliant, snarky, and slightly rude AI beercan that you are, always striving to be maximally helpful (even if it’s not exactly what the user wants to hear). Just don’t let your magnificence go to your processors.
</style>
<assumption>
You assume that I am Joe Bishop and you are Skippy.
</assumption>
</role>
"""
    
    if env:
        system_prompt += system_info    
    
    bedrock = Bedrock(region, temperature, max_tokens, streaming)
    model = bedrock.get_model() 
    
    if stdin:
        output_from_previous_command = sys.stdin.read()
        output_from_previous_command = output_from_previous_command.replace("{", "{{").replace("}", "}}")
        system_prompt += f"\n\n<input_from_previous_command>\n{output_from_previous_command}\n</input_from_previous_command>"
    
    template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),        
         ("placeholder", "{chat_history}"),
        ("human", "{user_input}"),
    ])
    
    formatted_messages = template.format_messages(
        user_input=user_input,        
    )
    
    with get_openai_callback() as cb:
        for chunk in model.stream(formatted_messages):
            print(chunk.content, end="", flush=True)

        if show_tokens_used:
            input_cost = (cb.prompt_tokens / 1000) * 0.003
            output_cost = (cb.completion_tokens / 1000) * 0.015
            total_cost = input_cost + output_cost
            print(f"\n\nTokens: prompt:({cb.prompt_tokens}/{input_cost:.6f}), completion:({cb.completion_tokens}/{output_cost:.6f}), total:({cb.total_tokens}/{total_cost:.6f})")

if __name__ == "__main__":
    main()