
import json
from datetime import datetime


class OpportunityDetector:


    def __init__(self):

        self.score_rules = {
            "growth": 30,
            "demand": 30,
            "competition": 20,
            "future": 20
        }



    def analyze(self, item):

        score = 0


        score += item.get(
            "growth",
            0
        )


        score += item.get(
            "demand",
            0
        )


        score += (
            20 -
            item.get(
            "competition",
            20)
        )


        score += item.get(
            "future",
            0
        )



        return {

            "name":
            item.get("name"),


            "score":
            min(score,100),


            "status":
            "HIGH OPPORTUNITY"
            if score >=70
            else
            "WATCH",


            "checked":
            datetime.now().isoformat()

        }



def run_opportunity_scan(path):


    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        data=json.load(f)


    results=[]


    for item in data:

        results.append(
            OpportunityDetector()
            .analyze(item)
        )


    return results
