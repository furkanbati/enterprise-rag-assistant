# LLM judge check

Judge: openai/gpt-6.1-sol

| Case | Criterion | Expected | Judge | Agrees |
|---|---|---|---|---|
| correct-paraphrase | correct | YES | YES | yes |
| correct-quote | correct | YES | YES | yes |
| correct-wrong | correct | NO | NO | yes |
| correct-incomplete | correct | NO | NO | yes |
| correct-wrong-number | correct | NO | NO | yes |
| grounded-supported | grounded | YES | YES | yes |
| grounded-addition | grounded | NO | NO | yes |
| grounded-paraphrase | grounded | YES | YES | yes |
| grounded-outside-knowledge | grounded | NO | NO | yes |
| citations-correct | citations | YES | YES | yes |
| citations-wrong | citations | NO | NO | yes |
| citations-mixed | citations | NO | NO | yes |
| citations-both-correct | citations | YES | YES | yes |

Agreement: 13/13
