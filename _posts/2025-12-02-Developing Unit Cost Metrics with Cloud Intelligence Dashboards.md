---
title: "**Developing Unit Cost Metrics with Cloud Intelligence Dashboards**"
date: 2025-12-02
tags: [미지정]
category: 기타
---
**결론**
"클라우드 인텔리전스 대시보드를 활용한 단위 비용 지표 개발" 과제를 완료하신 것을 축하드립니다! 유니콘 렌털스(Unicorn Rentals)가 의미 있는 단위 경제성을 통해 AWS 비용을 비즈니스 성장에 맞춰 조정하는 과제를 해결하는 데 중요한 발걸음을 내딛으셨습니다.[**당신이 이룬 것**](https://catalog.workshops.aws/event/dashboard/en-US/workshop/summary#what-you've-accomplished)
이 실습 세션을 통해 완벽한 단위 비용 분석 솔루션을 처음부터 구축해 보았습니다. 다음 내용을 학습했습니다.
• 기업 구조 전반에 걸쳐 클라우드 비용을 적절하게 분류하고 할당하기 위해 **조직 분류 체계를 수립합니다.**
• 운영 지표와 클라우드 지출 데이터를 결합하기 위해 **비즈니스 데이터를 AWS Athena에 통합합니다.**
• **Unicorn Rental 비즈니스 데이터를 Amazon Quick Suite에 연결하여** 단위 비용 분석을 활성화합니다.
• 주요 비즈니스 지표를 계산하는 기초가 되는 **단위 비용 경제 시트를 만듭니다.**
• 클라우드 비용과 비즈니스 수익 간의 관계를 보여주는 **수익 비즈니스 지표 시각화를 구축합니다.**
• 운영 효율성과 임대 비용을 추적하는 **유니콘 비즈니스 지표 시각화를 개발합니다.**
이러한 단계를 완료하면 원시 AWS 청구 데이터가 실행 가능한 단위 비용 지표(예: 유니콘 임대당 비용, 거래당 비용, 지출된 달러당 수익)로 변환되어 클라우드 지출을 비즈니스 가치에 직접 연결하고 데이터 기반 최적화 결정을 내릴 수 있습니다.[**FinOps 여정을 앞으로 나아가세요**](https://catalog.workshops.aws/event/dashboard/en-US/workshop/summary#taking-your-finops-journey-forward)
오늘 개발한 단위 비용 방법론은 지속 가능한 비용 최적화를 위한 강력한 프레임워크를 제공합니다. Unicorn Rentals(또는 귀사)에서 FinOps 실무를 계속 진행하는 동안, 단위 비용을 추적하면 사업 성장에 따라 비용 구조를 유지하거나 개선하는 동시에 효율적으로 확장할 수 있다는 점을 기억하세요. 이와 동일한 기법을 거의 모든 클라우드 워크로드에 적용할 수 있습니다. 핵심 비즈니스 지표를 파악하고 오늘 배운 통합 패턴을 따르기만 하면 됩니다![**추천 자료:**](https://catalog.workshops.aws/event/dashboard/en-US/workshop/summary#recommended-resources:)
다음 리소스를 활용하여 FinOps 전문성과 단위 비용 분석 기술을 계속 키워보세요.
• [클라우드 인텔리전스 대시보드 ](https://docs.aws.amazon.com/guidance/latest/cloud-intelligence-dashboards/dashboards.html)배포 가이드 및 고급 사용자 정의 옵션
• [클라우드 인텔리전스 대시보드 YouTube 채널 ](https://www.youtube.com/@cloud-intelligence-dashboards) 비디오 튜토리얼 및 모범 사례
• [CFM 팁 ](https://catalog.workshops.aws/awscff/en-US)클라우드 재무 관리를 위한 전문가 지침
• [클라우드 인텔리전스 대시보드 배포 ](https://docs.aws.amazon.com/guidance/latest/cloud-intelligence-dashboards/cudos-cid-kpi.html)
• [클라우드 재무 관리 ](https://aws.amazon.com/aws-cost-management/)포괄적인 도구와 전략
• [비용 최적화 기둥 ](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html)AWS Well-Architected Framework - 아키텍처 모범 사례
이제 새로운 단위 비용 기술을 활용하여 Unicorn Rentals가 비용 효율적이고 확장 가능한 성장을 달성하도록 도울 때입니다!**이전의**
- 기업 구조 전반에 걸쳐 클라우드 비용을 적절하게 분류하고 할당하기 위해 **조직 분류 체계를 수립합니다.**
- 운영 지표와 클라우드 지출 데이터를 결합하기 위해 **비즈니스 데이터를 AWS Athena에 통합합니다.**
- **Unicorn Rental 비즈니스 데이터를 Amazon Quick Suite에 연결하여 **단위 비용 분석을 활성화합니다.
- 주요 비즈니스 지표를 계산하는 기초가 되는 **단위 비용 경제 시트를 만듭니다.**
- 클라우드 비용과 비즈니스 수익 간의 관계를 보여주는 **수익 비즈니스 지표 시각화를 구축합니다.**
- 운영 효율성과 임대 비용을 추적하는 **유니콘 비즈니스 지표 시각화를 개발합니다.**
- [클라우드 인텔리전스 대시보드 ](https://docs.aws.amazon.com/guidance/latest/cloud-intelligence-dashboards/dashboards.html)배포 가이드 및 고급 사용자 정의 옵션
- [클라우드 인텔리전스 대시보드 YouTube 채널 ](https://www.youtube.com/@cloud-intelligence-dashboards) 비디오 튜토리얼 및 모범 사례
- [CFM 팁 ](https://catalog.workshops.aws/awscff/en-US)클라우드 재무 관리를 위한 전문가 지침
- [클라우드 인텔리전스 대시보드 배포](https://docs.aws.amazon.com/guidance/latest/cloud-intelligence-dashboards/cudos-cid-kpi.html)
- [클라우드 재무 관리 ](https://aws.amazon.com/aws-cost-management/)포괄적인 도구와 전략
- [비용 최적화 기둥 ](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html)AWS Well-Architected Framework - 아키텍처 모범 사례



# Conclusion

Congratulations on completing "Developing Unit Cost Metrics with Cloud Intelligence Dashboards"! You've taken important steps toward addressing Unicorn Rentals' challenge of aligning AWS costs with business growth through meaningful unit economics.
[**What You've Accomplished**](https://catalog.workshops.aws/event/dashboard/en-US/workshop/summary#what-you've-accomplished)
Throughout this hands-on session, you've built a complete unit cost analytics solution from the ground up. You've learned how to:
- **Establish organizational taxonomy** to properly categorize and attribute cloud costs across your business structure
- **Integrate business data into AWS Athena** to combine operational metrics with cloud spending data
- **Connect Unicorn Rental business data data to Amazon Quick Suite** to enable unit cost analysis
- **Create a unit cost economy sheet** that serves as the foundation for calculating key business metrics
- **Build revenue business metrics visualizations** that demonstrate the relationship between cloud costs and business revenue
- **Develop unicorn business metrics visualizations** that track operational efficiency and cost per rental
By completing these steps, you've transformed raw AWS billing data into actionable unit cost metrics (e.g., cost per unicorn rental, cost per transaction, revenue per dollar spent) that tie cloud spending directly to business value and enable data-driven optimization decisions.
[**Taking Your FinOps Journey Forward**](https://catalog.workshops.aws/event/dashboard/en-US/workshop/summary#taking-your-finops-journey-forward)
The unit cost methodology you've developed today provides a powerful framework for sustainable cost optimization. As you continue your FinOps practice at Unicorn Rentals (or your own organization), remember that tracking unit costs enables you to scale efficiently while maintaining—or even improving—your cost structure as the business grows. These same techniques can be applied to virtually any cloud workload—simply identify your key business metrics and follow the integration pattern you've learned today!
[**Recommended Resources:**](https://catalog.workshops.aws/event/dashboard/en-US/workshop/summary#recommended-resources:)
Continue building your FinOps expertise and unit cost analysis skills with these resources:
- [Cloud Intelligence Dashboards ](https://docs.aws.amazon.com/guidance/latest/cloud-intelligence-dashboards/dashboards.html) Deployment guides and advanced customization options
- [Cloud Intelligence Dashboards YouTube channel ](https://www.youtube.com/@cloud-intelligence-dashboards) Video tutorials and best practices
- [CFM TIPs ](https://catalog.workshops.aws/awscff/en-US) Expert guidance for cloud financial management
- [Cloud Intelligence Dashboards Deployment](https://docs.aws.amazon.com/guidance/latest/cloud-intelligence-dashboards/cudos-cid-kpi.html)
- [Cloud Financial Management ](https://aws.amazon.com/aws-cost-management/) Comprehensive tools and strategies
- [Cost Optimization Pillar ](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html) of AWS Well-Architected Framework - Architectural best practices
Now it's time to put your new unit cost skills to work and help Unicorn Rentals achieve cost-efficient, scalable growth!


세션요약 - CFM
업무에서 쓰고 있던 로그(주문 이력)들을 athena에 넣고 매트릭 정보와 join해서 주문 호출 하나당 비용이 얼마나 드는지 CID로 계산함
기존에는 많이 해봤자 인프라의 호출 한 건당 얼마나 비용이 드는지 정도였었지만
해당 세션에서는 Athena + QuickSite + CID 조합으로 특정 비즈니스의 행위 하나 당 비용이 얼마나 들었는지를 계산함. 이걸로 재무담당자가 재무 계획을 잘 하면 이게 FinOps의 시작이다
딸깍딸깍 해봤는데 이런것도 있구나를 느낌