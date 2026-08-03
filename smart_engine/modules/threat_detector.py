
import json
from datetime import datetime


class ThreatDetector:


    def __init__(self):

        self.risk_levels = {
            "LOW":0,
            "MEDIUM":1,
            "HIGH":2
        }



    def analyze(self,item):

        risk = 0
        reasons = []


        if item.get("competition",0) > 70:

            risk += 1
            reasons.append(
                "High Competition"
            )


        if item.get("growth",100) < 30:

            risk += 1
            reasons.append(
                "Low Growth"
            )


        if item.get("demand",100) < 30:

            risk += 1
            reasons.append(
                "Low Demand"
            )


        if risk >= 2:

            level="HIGH"

        elif risk == 1:

            level="MEDIUM"

        else:

            level="LOW"



        return {

            "name":
            item.get("name"),


            "risk":
            level,


            "reasons":
            reasons,


            "checked":
            datetime.now().isoformat()

        }



def run_threat_scan(path):


    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        data=json.load(f)


    results=[]


    detector=ThreatDetector()


    for item in data:

        results.append(
            detector.analyze(item)
        )


    return results
