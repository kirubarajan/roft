# Text Generation
We fine-tune a large instance of GPT-2 to generate adventure game text.

## Dataset Format
`example.json`
```
[
    {
        prompt: "Today is an important day.",
        text: "It is an important day for humans. It is a not important day for dogs.",
        boundary: -1
    },
    {
        prompt: "Today is an important day.",
        text: "It is an important day for humans. Sometimes, green blue yellow.",
        boundary: 1
    },
    {
        prompt: "Everyday, I wonder what AI truly is."
        text: "Somedays, it is a field. Other days, it is a hobby. On my worst days, it is my major. Tonight, we dine in hell."
        boundary: 3
    }
]
```
