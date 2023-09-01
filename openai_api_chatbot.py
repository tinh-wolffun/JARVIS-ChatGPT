print('### LOADING CREDENTIALS ###')
from dotenv import load_dotenv
import os

from Assistant.research_mode import ResearchAssistant

load_dotenv()

if len(os.environ['OPENAI_API_KEY'])==0: 
    print('openai API key not detected in .env')
    raise Exception("[$] openai API key is required. Learn more at https://platform.openai.com/account/api-keys")

if len(os.environ['IBM_API_KEY'])==0: print('[free] IBM cloud API Key not detected in .env\nLearn more at: https://cloud.ibm.com/catalog/services/text-to-speech')

if len(os.environ['IBM_TTS_SERVICE'])==0: print('[free] IBM cloud TTS service not detected in .env\nLearn more at: https://cloud.ibm.com/catalog/services/text-to-speech')

use_porcupine = True
if len(os.environ['PORCUPINE_KEY']) == 0: 
    print('[free] PicoVoice not detected in .env\nLearn more at: https://picovoice.ai/platform/porcupine/')
    use_porcupine = False


print('DONE\n')

print('### IMPORTING DEPENDANCIES ###')
import pygame

from Assistant import get_audio as myaudio
from Assistant.VirtualAssistant import VirtualAssistant
from Assistant.tools import count_tokens

print('DONE\n')

### MAIN
if __name__=="__main__":
    print("### SETTING UP ENVIROMENT ###")
    OFFLINE = False
    pygame.mixer.init()

    # INITIATE JARVIS
    print('initiating JARVIS voice...')
    jarvis = VirtualAssistant(
        openai_api   = os.getenv('OPENAI_API_KEY'),
        ibm_api      = os.getenv('IBM_API_KEY'),
        ibm_url      = os.getenv('IBM_TTS_SERVICE'),
        elevenlabs_api = os.getenv('ELEVENLABS_API_KEY'),
        elevenlabs_voice = 'Antoni',
        voice_id     = {'en':'jarvis_en'},
        whisper_size = 'medium',
        awake_with_keywords=["jarvis"],
        model= "gpt-3.5-turbo",
        embed_model= "text-embedding-ada-002",
        RESPONSE_TIME = 3,
        SLEEP_DELAY = 30,
        mode = 'CHAT'
        )

    while True:
        if not(jarvis.is_awake):
            print('\n awaiting for triggering words...')

            #block until the wakeword is heard, using porcupine
            if use_porcupine:
                jarvis.block_until_wakeword()
            else:
                while not(jarvis.is_awake):
                    jarvis.listen_passively()
        
        jarvis.record_to_file('output.wav')
        

        if jarvis.is_awake:
            prompt, detected_language = myaudio.whisper_wav_to_text('output.wav', jarvis.interpreter, prior=jarvis.languages.keys())

            # check exit command
            if "THANKS" in prompt.upper() or len(prompt.split())<=1:
                jarvis.go_to_sleep()
                continue
            
            if detected_language=='en':
                VoiceIdx = 'jarvis'
            else:
                VoiceIdx = detected_language
            
            jarvis.expand_conversation(role="user", content=prompt)

            # PROMPT MANAGING [BETA]
            #flag = jarvis.analyze_prompt(prompt)
            flag = '-1'

            # redirect the conversation to an action manager or to the LLM
            if (("1" in flag or "tool" in flag) and '-' not in flag):
                print('(though): action')
                response = jarvis.use_tools(prompt)
                response = response
            
            elif "2" in flag or "respond" in flag:
                print('(though): response')
                response = jarvis.get_answer(prompt)
            elif "-1" in flag:
                response = jarvis.switch_mode()
            else:
                print('(though): internet')
                response = jarvis.secondary_agent(prompt)

            jarvis.expand_conversation(role='assistant', content=response)
            pygame.mixer.stop()
            jarvis.say(response, VoiceIdx=VoiceIdx, IBM=True)

            print('\n')