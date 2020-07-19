# -*- coding: utf-8 -*-
"""BERT_LM.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1sEupnBDpF_ZnkR3AzqZTOiwb8JXuiTJv
"""

!pip install transformers -q

!wget -q https://raw.githubusercontent.com/wangcunxiang/SemEval2020-Task4-Commonsense-Validation-and-Explanation/master/Training%20%20Data/subtaskA_data_all.csv
!wget -q https://raw.githubusercontent.com/wangcunxiang/SemEval2020-Task4-Commonsense-Validation-and-Explanation/master/Training%20%20Data/subtaskA_answers_all.csv

import pandas as pd
import functools
df_data = pd.read_csv('taskA_trial_data.csv', error_bad_lines=False)
df_answers = pd.read_csv('taskA_trial_answer.csv', error_bad_lines=False, header=None, names=['id', 'labels'])

df = df_data.set_index('id').join(df_answers.set_index('id'))

for i in range(1, len(df)):
  if df['sent0'][i][-1] != '.' or df['sent1'][i][-1] !='.' :
    df['sent0'][i] = df['sent0'][i] +'.'
    df['sent1'][i] = df['sent1'][i] +'.'

df

df['pred'] = 0
df.head(5)

import torch
from transformers import BertTokenizer, BertModel, BertForMaskedLM

# OPTIONAL: if you want to have more information on what's happening under the hood, activate the logger as follows
import logging
logging.basicConfig(level=logging.INFO)

"""# Use a [CLS] as the classfication and train a classifier
# mask each word and get the probability of that word happening. Multiply this for all the word in the sentence. The bigger is the most probable answer
"""

# Load pre-trained model (weights)
# model_type = 'bert-large-cased'
model_type = 'bert-base-uncased'
model = BertForMaskedLM.from_pretrained(model_type)
tokenizer = BertTokenizer.from_pretrained(model_type)
_ = model.eval()

MASK_TOKEN = '[MASK]'
device = 'cuda'
# device = 'cpu'

"""#non-efficient but I merged two repeatitive for loop"""

for i in range(len(df)):
  if i % 500 == 0:
    print('i = ', i)
  sent0 = df['sent0'][i]    
  sent1 = df['sent1'][i]
  sentences = [sent0 , sent1]

  # Tokenization
  marked_sent0 = '[CLS] ' + sent0.replace('.' , '[SEP]')
  marked_sent1 = '[CLS] ' + sent1.replace('.' , '[SEP]')
  marked_sentences = [marked_sent0 , marked_sent1]
  
  # Tokenize sentences with the BERT tokenizer
  tokenized_sent0 = tokenizer.tokenize(marked_sent0)
  tokenized_sent1 = tokenizer.tokenize(marked_sent1)
  list_of_tokenized_sent = [tokenized_sent0 , tokenized_sent1]

  #Replace each word sent0 by MASK_TOKEN
  k = 0
  production = 1
  list_of_multiplication_of_prbblty = []
  for sent in list_of_tokenized_sent:
    for j in range(len(sent)):
      masked_token = sent[j]
      sent[j] = MASK_TOKEN
     
      #Map the token strings to their vocabulary indeces.
      indexed_tokens_sent = [tokenizer.convert_tokens_to_ids(sent)]

      #Convert inputs to PyTorch tensors
      tokens_tensor = torch.tensor(indexed_tokens_sent).to(device) # token_indices
      segments_tensors = torch.tensor([[0] * len(list_of_tokenized_sent[k])]).to(device) # segment
      model.to(device)
      
      #Predict all tokens
      with torch.no_grad():
          outputs_sent = model(tokens_tensor, token_type_ids=segments_tensors) 
          #outputs_sent[0] is a tuple # batch_size * seq_len * vocab_size eg: torch.Size([1, 9, 30522])
          list_predicted_prbblty = outputs_sent[0][0, j] #list_predicted_prbblty.shape ---> torch.Size([30522])*****tensor([-6.5220, -6.5080, -6.5015,  ..., -5.9197, -5.6961, -3.9317],device='cuda:0'  
          normalize_predicted_prbblty = torch.softmax(list_predicted_prbblty, -1)
          masked_token_index_in_vocab = tokenizer.convert_tokens_to_ids(masked_token)
          prediction_masked_token = normalize_predicted_prbblty[masked_token_index_in_vocab]  # prbblty of masked token for example ---> tensor(5.4704e-07, device='cuda:0')
          #masked_token_index_in_vocab => index of the word that is masked
          #Multiplication of the probabilities of masked tokens
      production *= prediction_masked_token.item()
      #Reset tokenized sentence to the first version to mask net word
      sent = tokenizer.tokenize(marked_sentences[k])

    #normalize_prbblty_production = pow( production , 1/len(sent))
    list_of_multiplication_of_prbblty.append(production)
    production = 1
    k +=1

#Updating pred column in the dataframe
  if list_of_multiplication_of_prbblty[0] > list_of_multiplication_of_prbblty[1]:
    df['pred'][i] = 1
  elif list_of_multiplication_of_prbblty[0] < list_of_multiplication_of_prbblty[1]:
    df['pred'][i] = 0

df

(df['labels'] == df['pred']).sum()/len(df)

"""### Don't repeat yourself:
prod = 1
for ....
  prod *= prop.item()

### combine all input for a model inside just one tensor. batch_size = seq_len

#Efficient2- insted of batch size = the lenth of sequense
"""

for i in range(1,len(df)):
  if i % 100 == 0:
    print('i = ', i)
  sent0 = df['sent0'][i]    
  sent1 = df['sent1'][i]
  sentences = [sent0 , sent1]

  # add [CLS] and [SEP] to the beginning and end of the sentences
  marked_sent0 = '[CLS] ' + sent0.replace('.' , '[SEP]')
  marked_sent1 = '[CLS] ' + sent1.replace('.' , '[SEP]')
  marked_sentences = [marked_sent0 , marked_sent1]

  # Tokenize sentences with the BERT tokenizer
  tokenized_sent0 = tokenizer.tokenize(marked_sent0)
  tokenized_sent1 = tokenizer.tokenize(marked_sent1)
  list_of_tokenized_sent = [tokenized_sent0 , tokenized_sent1]

  k = 0 
  list_of_indices_tensors = []
  merged_tensor = []
  segment = []
  merged_segment = []
  for sent in list_of_tokenized_sent:
    for j in range(len(sent)):
      masked_token = sent[j]
      sent[j] = MASK_TOKEN
      #Map the token strings to their vocabulary indeces.
      indexed_tokens_sent = tokenizer.convert_tokens_to_ids(sent)
      #Convert inputs to PyTorch tensors
      tokens_tensor = torch.tensor(indexed_tokens_sent).to(device) # token_indices
      list_of_indices_tensors.append(tokens_tensor)
      segments_tensors = torch.tensor([0] * len(list_of_tokenized_sent[k])).to(device) # segment
      segment.append(segments_tensors) 
      sent = tokenizer.tokenize(marked_sentences[k])    

    merge_all_tensors = torch.stack(list_of_indices_tensors)
    merge_all_segment = torch.stack(segment)
    #the following tensor is the first argument of the model including index tensors of all these:
    #[['[MASK]', 'he', 'poured', 'orange', 'juice', 'on', 'his', 'cereal', '[SEP]'],
    #['[CLS]', '[MASK]', 'poured', 'orange', 'juice', 'on', 'his', 'cereal', '[SEP]'], 
    #['[CLS]', 'he', '[MASK]', 'orange', 'juice', 'on', 'his', 'cereal', '[SEP]'],
    #['[CLS]', 'he', 'poured', '[MASK]', 'juice', 'on', 'his', 'cereal', '[SEP]'], 
    #['[CLS]', 'he', 'poured', 'orange', '[MASK]', 'on', 'his', 'cereal', '[SEP]'],
    #['[CLS]', 'he', 'poured', 'orange', 'juice', '[MASK]', 'his', 'cereal', '[SEP]'], 
    #['[CLS]', 'he', 'poured', 'orange', 'juice', 'on', '[MASK]', 'cereal', '[SEP]'], 
    #['[CLS]', 'he', 'poured', 'orange', 'juice', 'on', 'his', '[MASK]', '[SEP]'], 
    #['[CLS]', 'he', 'poured', 'orange', 'juice', 'on', 'his', 'cereal', '[MASK]']]
    merged_tensor.append(merge_all_tensors)
    
    merged_segment.append(merge_all_segment)
    model.to(device)
    list_of_indices_tensors = []
    segment = []
    k += 1

  #Calling BERT model
  with torch.no_grad():
    outputs_sent0 = model(merged_tensor[0], token_type_ids=merged_segment[0])
    outputs_sent1 = model(merged_tensor[1], token_type_ids=merged_segment[1])
    list_output = [outputs_sent0 , outputs_sent1]
    #outputs_sent0[0] is a tuple of batch size * seq length * vocab
    #in our case is j*j*30522
  

  #predicting masked_token prbblty
  element = 0
  production = 1
  list_of_multiplication_of_prbblty = []
  for sent in list_of_tokenized_sent:
    for j in range(len(sent)):
      masked_token = sent[j]
      sent[j] = MASK_TOKEN
      #normalized prbblty of all tokens in dictionary.--------> list_output[k][0][***********]---------> torch.Size([30522])
      normalize_predicted_prbblty = torch.softmax(list_output[element][0][j, j, :], -1) 
      #print(normalize_predicted_prbblty)
      #find index of masked_token
      masked_token_index_in_vocab = tokenizer.convert_tokens_to_ids(masked_token)
      #print(masked_token_index_in_vocab)
      #probblty of masked_token
      prediction_masked_token = normalize_predicted_prbblty[masked_token_index_in_vocab]
      #print(prediction_masked_token)
      production *= prediction_masked_token.item()
      sent = tokenizer.tokenize(marked_sentences[element])
    
    #normalize_prbblty_production = pow( production , 1/len(sent))
    list_of_multiplication_of_prbblty.append(production)
    production = 1
    element +=1


  #Updating pred column in the dataframe
  if list_of_multiplication_of_prbblty[0] > list_of_multiplication_of_prbblty[1]:
    df['pred'][i] = 1
  elif list_of_multiplication_of_prbblty[0] < list_of_multiplication_of_prbblty[1]:
    df['pred'][i] = 0

df

(df['labels'] == df['pred']).sum()/len(df)

df.drop(columns=['sent0', 'sent1' , 'labels'])

df.to_csv('subtaskA_trial_data.csv', header=False, columns=['pred'])
