
from datetime import datetime


class ProductIntelligence:


    def evaluate(self,item):

        score = 0


        score += item.get(
            "demand",0
        )


        score += item.get(
            "growth",0
        )


        score -= item.get(
            "competition",0
        ) / 2



        if score >= 70:

            recommendation="BUILD"

        elif score >=40:

            recommendation="WATCH"

        else:

            recommendation="AVOID"



        return {

            "product":
            item.get("name"),


            "market":
            item.get("market"),


            "score":
            round(score),


            "recommendation":
            recommendation,


            "generated":
            datetime.now().isoformat()

        }



def analyze_product(item):

    engine=ProductIntelligence()

    return engine.evaluate(item)
