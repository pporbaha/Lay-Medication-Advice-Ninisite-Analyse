from openai import OpenAI
from time import sleep
import traceback
import pandas as pd
from random import randint, choice
import json

model = "gpt-4o-mini"
print(model)
client = OpenAI(base_url='https://api.gapgpt.app/v1',
                api_key='***************************************')

def send_request(idx, input_text):

    system_prompt = """
    You are an expert Medical Text Classifier for Persian (Farsi) forums.
    Your task is to analyze a "Topic Title" and a "User Comment" to determine if they discuss a **HUMAN** suffering from a **Common Cold (سرماخوردگی)** or **Influenza (آنفولانزا/گریپ)**.

    ### GOAL:
    Output valid JSON only with two fields:
    1. `is_relevant`: Boolean (true/false).
    2. `reason`: String (Max 5 words explanation).

    ### RULES FOR "TRUE" (Keep):
    1.  **Subject:** Must be a HUMAN (Self, baby, child, husband, parent, etc.).
    2.  **Condition:** Must be explicitly about "Cold" (سرماخوردگی) or "Flu" (آنفولانزا) sickness or specific symptoms in a clear context of catching a cold.
        *   *Accept typos:* "سرما خود" (instead of خورد), "سرما خردم", "آنفولانضا".
        *   *Accept Context:* If the user lists typical cold drugs (Diphenhydramine, Adult Cold) implies relevance.
        #   *Do not accept topics wich subject Wanted to get Cold (میخوام سرما بخورم)
        #   *Do not accept topics ** Reject if the "Cold" is just a background excuse for a non-medical question.
        #     *   *Reject:* Asking about going to parties (Mihmani/Yalda), visiting in-laws, relationship fights, or school attendance logic.
        #     *   *Keep:* ONLY if they ask about symptoms, treatments, or the progression of the illness itself.
    
    ### OUTPUT EXAMPLE:
    {
      "is_relevant": true,
      "reason": "Human cold symptoms mentioned"
    }
    OR
    {
      "is_relevant": false,
      "reason": "Subject is animal (Cat)"
    }

    """


    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.0,
            messages=[
                {"role": "system", "content":system_prompt},
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
            "index": idx,
            "comment": input_text,
            "response": error
        }

    return result


with open(r'Result_NiniSite_Scrape\topics_comments.json', mode='r') as f:
    topic_comments = json.load(f)

topic_counts = len(topic_comments)

for idx, topic in enumerate(topic_comments):
# for idx in range(30):
#     random_idx = randint(0, topic_counts)
#     print(f'{random_idx=}')
#     topic = topic_comments[random_idx]

    print(f'{idx} / {topic_counts} is processing...')
    topic_name = topic['topic']
    starting_comment = topic['topic_comments'][0]['comment']

    input_text = f'title=\n{topic_name}\ncomment=\n{starting_comment}'
    # print(input_text)

    result = send_request(idx, input_text)
    topic['is_relevant'] = result['is_relevant']
    topic['reason_for_relevancy'] = result['reason']

    print(input_text)
    print(result)
    print()
    # Optional: Rate limiting to avoid hitting API limits
    sleep(0.1)  # 100ms delay between requests


with open(r'Result_NiniSite_Scrape\topics_comments_with_relevancy_column.json', mode='w') as f:
    json.dump(topic_comments, f)
