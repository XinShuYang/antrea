# Antrea Issue Data Processing Document

## Introduction

This document introduces how to process the Issue data from the Antrea project into a standardized format suitable for
training. Before processing the data, it is necessary to install the corresponding Python libraries. Please run the
following command in the Conda environment.

```plain
pip install -r requirements.txt
```

## What does it involve and how to use it?

This document covers two features, each implementing a different data processing method.

+ 1.The first feature is that when a user submits an issue, the model needs to assign specific tags, which is a
  classification task. The model is required to predict the tags. Therefore, the first type of data processing involves
  converting the raw issue data into trainable classification data.
+ 2.The second feature is that when a user submits an issue, the model needs to provide a clear solution. This is a
  challenging task, so the second type of data processing involves using OpenAI's GPT-4 API to process several comments
  under the issue, removing irrelevant information, such as personal names, and summarizing brief information from the
  comments. This information is mainly about the methods of how to solve the problem. Finally, the data is standardized
  into a fine-tunable question-answer pair dataset.
+ 3.Additional Information: When implementing the second feature, due to the insufficiency of open source data volume,
  it was necessary to use private issue data. However, private issue data is restricted. Therefore, we used OpenAI's
  GPT-4 API to process open source technical documents to generate document-based QA pairs and used them to train the
  local model. This approach was mainly because the logical capabilities of the local model are inferior to those of
  GPT-4. To bridge this gap and to endow the local model with prior background knowledge, we aimed to enhance the local
  model's ability to better analyze and summarize several comments under private issues, extracting content on how to
  resolve the issues. Then, we standardized the data into a fine-tunable private question-answer pair dataset and merged
  it with the open source data for comprehensive training.

### First，Download open source issue data

First of all, you need to change to the working directory of **github_issue_handling** in antrea after cloning the
repository:

```plain
cd ./antrea/ai/antrea_data_task
```

You need to obtain an OAuth2 token, which can increase the amount of ISSUE data downloaded from public repositories. You
need to create a new token in the "Developer settings" -> "Personal access tokens" -> "Generate new token" section of
your GitHub account settings.
When you create a token, you need to select the permissions for this token. To read issues from public repositories, you
need the "public_repo" permission.

When you run this command locally, you may encounter issues such as network interruptions that cause the program to
stop. Don't worry, just re-run the command. The program will download data from the point of interruption, rather than
downloading data from the beginning.

```plain
python issue_clawer.py --github-token 'OAuth2 token'
```

Although the data download program has taken steps to avoid downloading duplicate data, to ensure that the downloaded
data does not duplicate, please run the following command.

```plain
python issue_filter.py
```

### The first method of generating classification data and online model training.

#### Steps 1 : Process Issue data and generate training data.

Firstly, this step mainly processes the original Issue data into a standardized format, making the data more
understandable. The issue_label_train_datasets.py file mainly generates the training data set. To enhance the
flexibility for users to generate any training data set, this script provides four parameters.

+ 1.**--assign-labels** :  This represents specifying the 'label' names, creating data that only includes the
  specified 'label' names.
  Below is an example of generating a training dataset that only contains 'bug' and 'api' labels.
   ```plain
   python issue_label_train_datasets.py --assign-labels bug api
   ```
+ 2.**--add-labels** : It indicates adding additional 'label' names, requiring the specification of the label mapping
  relationship. And generate training data containing the specified 'label'. The following execution command is a
  reference example.
   ```plain
   python issue_label_train_datasets.py --add-labels "{'triage/duplicate': 'xx',}"
   ```
+ 3.**--body-prompt** : It indicates whether there is a need to use Chatgpt to briefly summarize the 'body' part of the
  Issue, with optional parameters ['body_prompt_1','body_prompt_2','body_prompt_3']. An API Key for Chatgpt needs to be
  applied for on the [OpenAI](https://openai.com/) official website. The following execution command is a reference
  example.
   ```plain
   python issue_label_train_datasets.py 'other parameter' --body-prompt body_prompt_3 --openai-key 'you openai key'
   ```

The final generated training dataset file name is: **issue_train_datasets.json**, and the file name of the dataset
without labels is: **issue_datasets_no_label.json**.

#### Steps 2 : Use the fine-tuned Chatgpt model to generate labels for unlabeled data.

Use the training data from Step 2 to fine-tune the Chatgpt model, and then use the fine-tuned model to generate labels
for unlabeled data. For information on how to fine-tune Chatgpt, please refer to
the [documentation](https://github.com/zgy0817/antrea/blob/ai/ai/docs/GPT%20Online%20Model%20Fine-tuning%20Documentation.md).

After obtaining the fine-tuned model, execute the following command to generate the validation dataset.

```plain
python issue_label_evaluate_datasets.py --openai-key 'You openai key' --job-id 'The job ID of the model after ChatGPT training has been completed.'
```

The final generated validation dataset file name is: **issue_evaluate_datasets.json**

### The second method for generating question-answer pair data.

#### Summary of conversation data regarding the Issue

The issue_summary_dataset.py program is primarily designed to summarize review data.The **--use-prompt-type** parameter
specifies the type of 'prompt' used to guide the model in summarization. There are three types available: **simple**、**COT**、**TOT**, with the default being **simple**.
Summarize several comment texts under open source issue data and generate fine-tunable question-answer pair data:

```plain
python issue_summary_dataset.py --OAuth2-token 'Personal GitHub Access Token: Please refer to step 1.' --openai-key 'openai key' --data-type public --public-data-dir issue.json --use-prompt-type simple --use-model-type GPT
```

### Additional Attention

We segment the document because it is very long and contains highly detailed technical knowledge. It is not feasible to
use GPT-4 to generate a comprehensive and complete Q&A set, so we divide the document by headings.
There are two methods for generating QA pairs from documents:

+ 1.For the segmented document, use GPT-4 to freely generate multiple QA pair data.
+ 2.Provide the headings of the segmented document to GPT-4 for completion and improvement. Without changing the
  original meaning of the headings, generate new text to be used as the question, and treat the text under the original
  headings as the answer.

#### Regarding the generation of QA pairs from documents

The script for generating QA pairs from the document is doc_generate_qa.py. The --docs-dir argument specifies the path
to the folder containing the documents.

Document is segmented to generate detailed QA pairs:

```plain
python doc_genratre_qa.py --docs-dir 'path to the document's folder' --openai-key 'openai key' --mode all
```

The document is segmented and questions are generated using headings:

```plain
python doc_genratre_qa.py --docs-dir 'path to the document's folder' --openai-key 'openai key' --mode title
```


