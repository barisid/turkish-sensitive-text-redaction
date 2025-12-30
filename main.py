#%%
# -*- coding: utf-8 -*-
"""
This project includes software from:

Project: akdeniz27/bert-base-turkish-cased-ner (HuggingFace)
Licensed under the MIT License

"""
import os
import re
import argparse
from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline
class Redaction():

    def __init__(self, text, types_for_redaction, number_redactions, currency_format):
        self.text: str= text
        self.model = AutoModelForTokenClassification.from_pretrained("akdeniz27/bert-base-turkish-cased-ner")
        self.tokenizer = AutoTokenizer.from_pretrained("akdeniz27/bert-base-turkish-cased-ner")
        self.ner = pipeline('ner', model=self.model, tokenizer=self.tokenizer, aggregation_strategy="first")
        self.types_for_redaction = types_for_redaction
        self.number_redactions = number_redactions
        self.currency_format = currency_format

    def __call__(self):
        return self.text_redaction()
        

    def text_redaction(self):
        output_text = self.text
        result = self.ner(output_text)
        for entity in result:
            if "Person" in self.types_for_redaction:
                if entity["entity_group"] == "PER":
                    output_text = output_text.replace(entity["word"], "PERSON")
            if "Organization" in self.types_for_redaction:
                if entity["entity_group"] == "ORG":
                    output_text = output_text.replace(entity["word"], "ORGANIZATION")
            if "Number" in self.types_for_redaction:
                for num_length in self.number_redactions:
                    regex_pattern = "[0-9]"+ "{" + str(num_length) + "}"
                    number_matches = re.findall(regex_pattern, output_text)
                    if len(number_matches) > 0:
                        for num_match in number_matches:
                            output_text = output_text.replace(num_match, "NUMBER")
            if "IBAN" in self.types_for_redaction:
                iban_matches = re.findall("TR[0-9]{24}", output_text)
                if len(iban_matches) > 0:
                    for iban_match in iban_matches:
                        output_text = output_text.replace(iban_match, "IBAN")
                iban_matches = re.findall(re.findall(r"TR\d{2}\s\d{4}\s\d{4}\s\d{4}\s\d{4}\s\d{4}\s\d{2}", output_text))
                if len(iban_matches) > 0:
                    for iban_match in iban_matches:
                        output_text = output_text.replace(iban_match, "IBAN")
            if "Amount" in self.types_for_redaction:
                if self.currency_format == "Type1":
                    currency_matches = re.findall(r"[0-9]{0,3}\.{0,1}[0-9]{0,3}\.{0,1}[0-9]{0,3}\.{0,1}[0-9]{0,3},{0,1}[0-9]{0,2}",output_text)
                    for currency_match in currency_matches:
                        if len(currency_match) >= 3:
                            output_text = output_text.replace(currency_match, "AMOUNT")
                elif self.currency_format == "Type2":
                    currency_matches = re.findall(r"[0-9]{0,3}\,{0,1}[0-9]{0,3}\,{0,1}[0-9]{0,3}\,{0,1}[0-9]{0,3}.{0,1}[0-9]{0,2}",output_text)
                    for currency_match in currency_matches:
                        if len(currency_match) >= 3:
                            output_text = output_text.replace(currency_match, "AMOUNT")
        return output_text
            

parser = argparse.ArgumentParser(description="Sensitive Information Redaction Tool")

parser.add_argument("--input", help="Input txt file path")
parser.add_argument("--output", help="Redacted file path")
parser.add_argument("--redaction_types", help="Information type to be redacted:Person, Organization, Number, IBAN, Amount")
parser.add_argument("--number_redactions", help="Length of numbers to be redacted")
parser.add_argument("--currency_format", help="Currency format to be redacted. Type1=dd.ddd.ddd,dd, Type2=dd,ddd,ddd.dd")

args=parser.parse_args()

try:
    with open(args.input, "r") as file:
        input_text = file.read()
except Exception as e:
    raise FileNotFoundError("File read error: " + e)

redaction_types = [str(i).strip() for i in args.redaction_types.split(",")]
number_redactions = [str(q).strip() for q in args.number_redactions.split(",")]
currency_format = args.currency_format

res = Redaction(text=input_text, types_for_redaction=redaction_types, number_redactions=number_redactions, currency_format=currency_format)

output_text = res()

try:
    with open(args.output, "w") as file:
        input_text = file.write(output_text)
except Exception as e:

    raise FileExistsError
