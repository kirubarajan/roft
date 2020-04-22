# Learning to Trick Humans
> Evaluation Criteria for Human and Computer Written Text

Help us understand what makes text "sound human" by taking part in our experiment [here](http://18.218.3.184:8000) and annotating a few examples!

## Introduction
There is little agreement on how to evaluate natural language generation systems using human annotation due to the wide variety of existing standards [1]. This experiment will be focused on using human annotation to answer what qualitative and linguistic qualities in particular give away the fact that a text is or is not human-written. Annotators will be able to select from a predefined list of error categories, and select sentences that provide the evidence for the annotator distinction. For example, an annotator may notice a failing coreference resolution, and provide the sentence containing the original named entity as context for the error. The goal of this project is to obtain qualitative human assessment of provided text in a systemized fashion in order to increase the accuracy and “human”-ness of text generation.

## Related Work
ChatEval provides a suite of human metrics, however the human metrics only compares a human annotator’s preference between two systems [2]. The goal of this project is to offer additional insight into the reasons for a certain annotator’s preference, but still maintain a consistent metric across systems. Another inspiration for this idea is the bAbI dataset [3] which aims to offer the ability to diagnose a model's limitations by providing the granular tasks for which it fails. In a similar fashion, we aim to develop a system of categories for annotators to tag generated sentences with, as a means of analyzing a model’s capabilities and the text’s overall linguistic quality. 

Previous work [4] has analyzed how choices in sampling strategy contribute to the accuracies of both human and machine systems to detect generated text. This project aims to provide two other dimensions to this work: 1) the distribution of qualitative linguistic qualities that annotators can use to identify generated texts and 2) the relative speeds (e.g. number of sentences) that it takes before an annotator can determine that something is machine generated and what errors tend to occur at these boundaries. While the incorporation of qualitative metrics into classifiers and other mainly empirical applications is more difficult, we believe that a focused study of these qualitative domains can lead to a greater understanding of the statistical trends underlying “human-like” text and in turn allow generation systems to better sample from the tail of the distribution of words in a more human fashion.

Additionally, while previous work [4] has investigated differing lengths of prompts as it pertains to the identification of generated text, we believe our study will extend on this front and allow for a more comprehensive study of the effects of prompt length on human-like generation and what errors are more likely to happen given a longer prompt as opposed to a shorter prompt (i.e. systems make more factual errors when prompts are large but make more coherence errors when prompts are short).

## Experimental Design
### Annotators

We will select individuals with either a background in linguistics (or NLP) or a pre-approved understanding of the tags included in our annotation task. We do this to ensure that all annotators properly understand the meanings of tags such as “Entailment” and “Coreference”. That being said, for things such as “Grammatical” and “Common-sense” we will refrain from giving strict guidelines as to what constitutes common-sense or grammaticality in an effort to better model the inherently multifaceted nature of these phenomena. 

### Tags
The annotation system will be an application that presents sentences of text (one-by-one), as well as allow the annotator to select a list of tags to describe a given sentence. The tags are as follows:

**Machine Categories:**
1. Grammatical error (failing to even “appear” English)
2. Repetition error (repeating text in a non-meaningful fashion)
3. Coreference error (failing to resolve coreferring entities)
4. Entailment error (failing to reason about text which was previously generated)
5. Common-sense error (failing to having common understanding of the world)

**Human Categories:**
1. Idiomatic Text (use of common spoken language constructs)
2. Grammatical Fluidity (grammar flows in human-like fashion)
3. Meaningful (interesting text with non-trivial reasoning, analysis, or insight behind it)
4. Cohesive (text stays tightly to one topic and limits to mentioning relevant details)
5. Emotive (text expresses believable levels of emotion, excitement)

### Annotation System
Our annotation system presents generated sentences of text one-by-one for a given prompt+generation passage and allows the annotator to stop the presentation once they are confident that the prompt has ended and the generation has begun, i.e. that the text is now being generated by a machine. Upon stopping the presentation, depending on their selection (e.g. machine or human) the annotator selects from a list of pre-defined tags to describe the phenomena that provides the annotator the reasoning behind their decision, as well as selects the sentences that were relevant to the instance of the phenomena.

We will be having at least 4 annotators for this task (likely more) and will have at least two annotators per example so as to allow for the measurement of inter-annotator agreement. The preliminary annotations will all be done by Arun and I to ensure we properly understand the problem and to allow us to troubleshoot any issues with both our systems and the proposed tag selection.

We will be measuring the efficiency, inter-annotator agreement, and distribution of these tags for the initial sample of our annotations to decide whether or not to prompt our future annotators to select reasonings for all sentences in the generation or just the designated boundary sentence. While it would be interesting to have more qualitative judgements we fear that we run the risk of spending too much time collecting spurious data that is irrelevant to answering our question if we prompt our annotators for too much. 

We are also considering allowing annotators to select the sentence where they believe the machine generation starts as well as a different sentence that clued them in to the fact that the text is now being generated. This is because we believe that these two might not necessarily be the same thing, and once an annotator is clued in to the fact that text is generated, they might reassess their previous judgements as to when the generation started. We will use preliminary results to decide whether or not to separate these two or whether to stick with the original designation.

### Models
The experiment has the ability to test a variety of models and generation strategies. Due to time limitations and resource constraints, we will be testing OpenAI’s GPT-2 model with two different sampling algorithms: random (i.e. not altering the output distribution), and nucleus (or top-p). We will have a random distribution for the length of the prompt that varies between 1 and 10 sentences and we will also ensure that at least 25% of our generations are fully human. This prevents annotators from reading too far into the text with the expectation of it being generated and also allows us to check the frequency of which machine-like errors are most commonly over classified on a per annotator basis. We may even weight annotators later based on how quick they are to mis-classify human sentences as machine sentences and analyze if this has any effect on when they decide to place the human-machine boundary in the non-fully human passages

### Prompt Sources

We will be sampling our prompts from a variety of different sources to ensure that we are able to gain insight as to which domains are more challenging for generation systems to produce plausible human-like outputs and to understand how the distribution of qualitative errors differs between domains (i.e. more factual errors are made during news article prompts but more coreference errors are made during dialogue-heavy novels). 

## Research Questions
1. Which domains are more likely to give text generation systems trouble with?
2. Which qualitative categories are most likely for generation systems to mess up on?
3. Does the distribution of errors within these categories change with the length of the prompt?
4. How does the sampling strategy affect the errors made by these generation systems
5. How reliably can humans properly detect the boundary sentence?
6. How reliably can humans detect generated text to begin with?
7. How much do our annotators agree on the boundary sentence and how much do they agree on the reasonings between mistakes?

## References
1. [Best practices for the human evaluation of automatically generated text](https://www.aclweb.org/anthology/W19-8643.pdf)
2. [ChatEval: A Tool for Chatbot Evaluation](https://www.aclweb.org/anthology/N19-4011/)
3. [Towards AI-Complete Question Answering: A Set of Prerequisite Toy Tasks](https://arxiv.org/abs/1502.05698)
4. [Human and Automatic Detection of Generated Text](https://arxiv.org/abs/1911.00650)
