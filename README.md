# RoFT: Real or Fake Text? 
<h2 align="center"> Do you think you can reliably detect generated text? Test your skills at <a href="http://roft.io" text>http://roft.io</a></h2>
</p>
<p align="center">
<img align="center" src="./resources/demo.gif" >
</p>

<h3 align="center">
(Read <a href="https://arxiv.org/abs/2010.03070" text>our demo paper</a>
at EMNLP 2020 for more on our methodology)
</h3>

# Project Goal
In this project, we aim to measure how good neural langauge models are at writing text. If you're familiar with the Turing Test, RoFT is a very similar experiment!

We hope that by testing how good humans are at detecting text we can better understand what makes text sound "human".

## How does it work?

1. See text one sentence at a time
2. Determine when the text switches from human written text to machine-generated text
3. Recieve points according to your precision 
4. Climb the leaderboard and see how good you are at detecting generated text!


## Research Questions
1. Which domains are more likely to give text generation systems trouble with?
2. Which qualitative categories are most likely for generation systems to mess up on?
3. Does the distribution of errors within these categories change with the length of the prompt?
4. How does the sampling strategy affect the errors made by these generation systems?
5. How reliably can humans detect generated text?
6. How reliably can humans detect generated text to begin with?
7. How much do our annotators agree on the boundary sentence and how much do they agree on the reasonings between mistakes?

## Data Sources
1. [New York Times Annotated Corpus (Sandhaus, 2008)](https://catalog.ldc.upenn.edu/LDC2008T19)
2. [Reddit Writing Prompts (Fan et al., 2018)](https://dl.fbaipublicfiles.com/fairseq/data/writingPrompts.tar.gz)
3. [Corpus of Presidential Speeches (Brown, 2016)](http://www.thegrammarlab.com/?nor-portfolio=corpus-of-presidential-speeches-cops-and-a-clintontrump-corpus)
4. [Recipe1M+ (Marin et al., 2019)](http://pic2recipe.csail.mit.edu/)

## Language Models
1. [GPT2-XL (Radford et al., 2019)](https://openai.com/blog/better-language-models/)
2. [CTRL (Keskar et al., 2019)](https://blog.einstein.ai/introducing-a-conditional-transformer-language-model-for-controllable-generation/)
3. [GROVER (Zellers et al., 2019)](https://rowanzellers.com/grover/)

## Citation
If you use the RoFT tool for your research, please cite us as:
<pre>
@article{dugan2020roft,
  title={RoFT: A Tool for Evaluating Human Detection of Machine-Generated Text},
  author={Dugan, Liam and Ippolito, Daphne and Kirubarajan, Arun and Callison-Burch, Chris},
  booktitle={Empirical Methods in Natural Language Processing, Demo Track},
  year={2020}
}
</pre>