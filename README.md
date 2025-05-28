# Policy Corpus Clau  

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)  
[![CI Status](https://github.com/ClaudiaAgromayor/policy-corpus/actions/workflows/validate.yml/badge.svg)](https://github.com/ClaudiaAgromayor/policy-corpus/actions)

This repository stands as a corpus of business policies to support research studies, academic courses and experiments.
It includes synthetic policies and a catalog of links of real public policies for various business domains.

## Key Features  
✔ Standardized policy format (JSON + natural language)  
✔ Validated Python implementations  
✔ Synthetic test data generators  
✔ Ready-to-use benchmark datasets  
✔ Covers airlines, finance, HR, and insurance  

## Repository Structure
/policies
  /airlines        # Airline-specific policies
  /financial       # Financial service policies
/schema           # Validation schemas
/scripts          # Utility scripts
/tests            # Validation tests

## Usage
## Quick Start  

1. **Install dependencies**:  
```bash  
npm install
2. **Validate Policies**:
npm test
3. **Run benckmarks**:
python benchmarks/compare.py --policy=luggage  

## Policy reference implementation
For a panel of business domain and use cases, this project proposes data and code to benchmark automated decisions with respect to a business policy expressed in plain text.
Each policy is described by:
- a plain text specifying the requirements, criteria and logic to deduce a decision from a given context.
- a Python code implementating the policy. This implementation has been validated by a human, based on an interpretation where policy brings ambiguity or misses information.
- a Data generator code. It invokes the automation code on synthetic inputs to produce outcomes
- a list of decision datasets. They are ready to use as a baseline to measure the performances of any machines (pure LLMs, code generated thanks to LLMs, others) that automate the decision making.  

## Policy list
| Policy | Description | Code | Test Cases |  
|--------|-------------|------|------------|  
| [Luggage](luggage/luggage_policy.md) | Airline baggage rules | [Python](luggage/impl.py) | [JSON](luggage/tests.json) |  
| [Time Off](human-resources/time_off.md) | Employee leave | [Python](hr/impl.py) | [CSV](hr/tests.csv) |  
| [Insurance](insurance/policy.md) | Claim approval | [Python](insurance/impl.py) | [JSON](insurance/tests.json) |  
| [Loans](loan/policy.md) | Credit decisions | [Python](loan/impl.py) | [CSV](loan/tests.csv) |

## Motivations
## Research Goals  
Compare different automation methods:  
- **Pure LLM decisions** (single prompt)  
- **LLM-generated code**  
- **Human-validated implementations**  

## How to benchmark your policy automation against a test dataset
You want to measure quantitatively the performance of your policy automation, then this project is made for you.
Run your own implementation (pure LLM, LLM generating code, etc) to produce decisions and compare these decisions with reference ones in the available datasets.
Please have a look at this section: [Benchmark your policy implementation](benchmark_your_policy_automation_docs/README.md)

## Common framework
As we are cooking a similar recipe for each policy, the project proposes a common framework to support and accelerate the definition, and data generation of a policy: [Common framework](common/commons_descriptor.md)

## How to extend the corpus to your own policies
If you intend to extend the corpus with a new policy please have a look to this section: [Adding a policy](policy_corpus_extension_docs/README.md)

## License  
MIT © 2023 [Claudia Agromayor]  
