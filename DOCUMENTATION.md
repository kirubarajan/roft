# Documentation
This repository contains a web application that is used to load generated/written text, segment the text into displayable sentences, and programmatically aggregate annotatons.

## Setup
1. Clone the repository.
2. Install dependencies.
3. Run `main.py` to start the application.

## Format
Annotations are recorded in the following JSON format:

```javascript
{
    prompt_id: Integer,
    annotator_name: String, 
    prediction: Integer, 
    label: Integer, 
    boundary: Integer,
    tags: Array[String], 
    evidence: Array[Integer]
}
```

## Screenshots

![screenshot](https://i.imgur.com/l0Uxjku.png)

