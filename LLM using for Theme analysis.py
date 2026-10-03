# step one: extracting doctor referral
# step two: extracting treatments

from openai import OpenAI
from time import sleep
import traceback
from pprint import pprint
import pandas as pd
from random import randint, choice
import json
from os import system
import ctypes

model = "gpt-4o-mini"
print(model)
client = OpenAI(base_url='https://api.gapgpt.app/v1',
                api_key='***************************************')

system_prompt_step_one = """
You are a Medical Entity Extractor. Extract any drugs, home remedies, or actions mentioned in the text.
Write them in English not Persian.
**Please consider even actions such as, Go to Doctor , or Not go to doctor, ... in the output

### RULES for 'status':
- "Definitive Advice": Strong advice ("Give this").
- "With_Caution Advice": Weak suggestion ("Maybe try this").
- "Definitive Discouraged": Specifically warning against a REMEDY (e.g., "Don't give honey").
- "With_Caution Discouraged": Weak discouraging ("Maybe better to not try this").
- "Administered/Experienced": Past tense ("I gave this", "We used this").
- "Asking": User is asking about a specific drug.

### OUTPUT FORMAT
Return valid JSON only.
**IMPORTANT STRICT RULE: Return the raw JSON string only - Do NOT wrap the output in ```json``` or any markdown code blocks.
- Do NOT add any text before or after the JSON.
- Start directly with { and end with }
- Write them in English not Persian.

{
  "treatments": [
    {
      "name": "English Name",
      "category": "Chemical" | "Herbal" | "Home_Remedy(Not herbal/foods)" | "Action"
      "status": "Definitive Advice" | "With_Caution_Advice" | "Definitive Discouraged" | "With_Caution Discouraged" | "Administered/Experienced" | "Asking"
    }
  ]
}

** if there arent any treatments, return:
{
  "treatments": []
}
"""

system_prompt_step_two = """
You are a Medical Decision Analyst. Analyze the text to determine the user's stance regarding **Professional Medical Visits** (Doctors, Hospitals, Clinics).
I want also to know if any side effects of recommended drugs mentioned or not.
*** Only write in English

### CLASSIFICATION CLASSES:
"doctor_stance_mentioned?": Just focus that if doctor/متخصص mentioned or not?
    1.Mentioned
    2.Not_Mentioned

"attitude_about_doctors": 
    1. "Encouraged": 
       - Explicitly suggests visiting a doctor or go to doctor.
       - Examples: "Take him to the doctor immediately", "doctor", "Call an ambulance".
    
    2. "Discouraged": 
       - Explicitly advises **AGAINST** seeing a doctor.
       - Examples: "Don't take him to the doctor", "Doctors just give harmful chemicals", "It's not worth going".
    
    3. "Hesitation":
      - Don't know go to doctor or not
      - Examples: "I wait currently and dont go to doctor currently."
      
    4. "Not_Mentioned": 
       - The text discusses symptoms or home remedies but does NOT mention doctors or hospitals at all.
    

###any_side_effect or background mentioned
"any_side_effect_mentioned?":
    true | false
   -example اگه باردار نیستی پنیرک یا آویشن دم\u200cکن بخور' 
   because She mentioned 
   > true

"side_effects_mentioned":[]

### OUTPUT FORMAT
**IMPORTANT STRICT RULE: Return the raw JSON string only - Do NOT wrap the output in ```json``` or any markdown code blocks.
- Do NOT add any text before or after the JSON.
- Start directly with { and end with }
- Write them in English not Persian.

{
  "doctor_stance_mentioned?": "Mentioned" | "Not_Mentioned"
  "attitude_about_doctors": "Encouraged" | "Discouraged"| "Hesitation" | "Not Mentioned"
  "any_side_effect_mentioned?": true | false
  "side_effects_mentioned":[]
}
"""



def send_to_llm(input_text, system_prompt):
    try:
        response = client.chat.completions.create(
            model=model,
            # temperature=0.0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_text}
            ],
        )

        answer = response.choices[0].message.content
        # result = {
        #             "index": idx,
        #             "comment": input_text,
        #             "response": answer
        #         }
        result = json.loads(answer)

    except Exception as e:
        error = str(traceback.format_exc())
        print(f"Error on comment {idx}: {error}")
        result = {
            "comment": input_text,
            "response": answer,
            "error": error
        }

    return result, answer



with open(r'Result_NiniSite_Scrape\topics_comments_with_relevancy_column.json', mode='r') as f:
    topic_comments = json.load(f)

topic_counts = len(topic_comments)

start_idx = 1338
for idx, topic in enumerate(topic_comments[start_idx:], start_idx):
# for idx in range(3):
#     random_idx = randint(0, topic_counts)
#     print(f'{random_idx=}')
#     topic = topic_comments[random_idx]

    print(f'{idx} / {topic_counts} is processing...')
    topic_name = topic['topic']
    starting_comment = topic['topic_comments'][0]['comment']
    is_relevant = topic['is_relevant']

    if not is_relevant:
        continue

    for each_comment in topic['topic_comments']:
        is_starter = each_comment['is_starter']
        is_advertising = each_comment['is_advertising']
        comment = each_comment['comment']

        if is_advertising:
            continue

        # input_text = f"""
        # --- CONTEXT START ---
        # TOPIC TITLE: {topic_name}
        #
        # PROBLEM DESCRIPTION (Starter's Post):
        # "{starting_comment}"
        # --- CONTEXT END ---
        #
        # --- TARGET FOR ANALYSIS ---
        # USER ROLE (IS_STARTER?): {is_starter}
        # COMMENT TEXT:\n"{comment}"
        # ---------------------------
        # """
        input_text = f"""
        # USER ROLE (IS_STARTER?): {is_starter}
        # COMMENT TEXT:\n"{comment}"
        """

        result_step_one, answer_step_one = send_to_llm(input_text, system_prompt_step_one)
        print(f"{comment=}")
        print(f"{is_starter=}")
        # print(f"{answer_step_one=}")

        try:
            result_step_one['treatments']
        except KeyError:
            result_step_one['treatments'] = []

        if not result_step_one['treatments']:
            continue

        result_step_two, answer_step_two = send_to_llm(input_text, system_prompt_step_two)

        # print(f"{answer_step_two=}")

        result = result_step_one | result_step_two
        each_comment['llm_analysis'] = result.copy()
        pprint(result)
        # print(f"{result_step_two}")
        print()
        # Optional: Rate limiting to avoid hitting API limits
        sleep(0.03)  # 100ms delay between requests

with open(r'Result_NiniSite_Scrape\topics_comments_with_llm_theme_analysis.json', mode='w') as f:
    json.dump(topic_comments, f)

# Sleep - Keeps RAM intact
# ctypes.windll.powrprof.SetSuspendState(0, 1, 0)

# %% merging 5. Merge topics_comments_with_llm_theme_analysis_0_623.json and topics_comments_with_llm_theme_analysis_from_623_to_1338.json
with open(r'Result_NiniSite_Scrape\topics_comments_with_llm_theme_analysis_0_623.json', mode='r') as f:
    data1 = json.load(f)

with open(r'Result_NiniSite_Scrape\topics_comments_with_llm_theme_analysis_from_623_to_1338.json', mode='r') as f:
    data2 = json.load(f)

with open(r'Result_NiniSite_Scrape\topics_comments_with_llm_theme_analysis_from_1338_to_end.json', mode='r') as f:
    data3 = json.load(f)

all_data = data1[:623] + data2[623:1338] + data3[1338:]

with open(r'Result_NiniSite_Scrape\topics_comments_with_llm_theme_analysis_all.json', mode='w') as f:
    json.dump(all_data, f)

