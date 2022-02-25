# coding=utf8
import random
import spacy
import zh_core_web_lg
import neuralcoref
from summarizer import Summarizer
from summarizer.text_processors.sentence_handler import SentenceHandler
from spacy.lang.zh import Chinese
from transformers import AutoConfig, AutoTokenizer, AutoModel
from DialogueExtractor import Clip

nlp = zh_core_web_lg.load()
neuralcoref.add_to_pipe(nlp)
modelName = "bert-base-chinese"
# modelName = "uer/roberta-base-finetuned-chinanews-chinese"
custom_config = AutoConfig.from_pretrained(modelName)
custom_config.output_hidden_states=True
custom_tokenizer = AutoTokenizer.from_pretrained(modelName)
custom_model = AutoModel.from_pretrained(modelName, config=custom_config)
model = Summarizer(
    custom_model=custom_model, 
    custom_tokenizer=custom_tokenizer,
    sentence_handler = SentenceHandler(language=Chinese),
)

def extractive_summarize(sentences, source, target, seed=666):
    """
    sentences: list of string sentences
    source: if integer, use specified amount of sentences as the pool. Treat as ratio if float
    target: if integer, generate specified amount of sentences from the pool. Treat as ratio if float
    seed: random seed
    """
    source = float(source)
    target = float(target)
    if source % 1 != 0:
        if source > 1:
            source = min(len(sentences), int(source))
        else:
            source = min(1, abs(source))
            source = int(len(sentences) * source)
    else:
        source = int(min(source, len(sentences)))
    
    if target % 1 != 0:
        if target > 1:
            target = min(source, int(target))
        else:
            target = min(1, abs(target))
            target = int(source * target)
    else:
        target = int(min(target, source))
    
    seed = int(seed)
    
    # Sample data
    random.seed(seed)
    sampled_keys = random.sample(sentences.keys(), source)
    result = model(
        body="。".join(sampled_keys),
        min_length=10,
        max_length=50,
        num_sentences=target
    )
    return result.split("。 ")