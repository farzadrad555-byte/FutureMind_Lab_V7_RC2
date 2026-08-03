
import json
from datetime import datetime


class IntelligenceReport:


    def generate(
        self,
        opportunities,
        threats,
        products
    ):


        report = {

            "date":
            datetime.now().strftime(
                "%Y-%m-%d"
            ),


            "top_opportunities":
            opportunities,


            "market_threats":
            threats,


            "recommended_products":
            products,


            "status":
            "READY"

        }


        return report




def save_report(report,path):


    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            report,
            f,
            ensure_ascii=False,
            indent=2
        )
