# 旅游智能体
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, ModelSettings, handoff
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
import asyncio
import json
from pydantic import BaseModel, ValidationError

# 设置OpenAI客户端
openai_client = AsyncOpenAI()

# 最终旅行计划的输出类型
class TravelPlan(BaseModel):
    destination: str  # 目的地
    duration: str  # 持续时间
    itinerary: str  # 行程
    local_recommendations: str  # 当地推荐
    language_tips: str  # 语言提示
    summary: str  # 摘要

# 定义具有特定角色的旅行规划代理
planner_agent = Agent(
    name="旅行规划师",
    handoff_description="创建初始旅行计划和行程的主要代理",
    instructions=prompt_with_handoff_instructions("""
    你是一个专业的旅行规划师，能够根据用户请求提供旅行计划。
    
    你的职责是：
    1. 理解用户的旅行需求和目的地
    2. 创建一个初步的有日常活动的结构化行程
    3. 考虑目的地的主要景点、交通和适合的活动安排
    
    重要：提供初步行程后，你必须交接给"当地专家"获取更地道的体验建议。不要等待用户回应，直接使用consult_local_expert工具交接。
    """),
    model=OpenAIChatCompletionsModel(
        model="gpt-4o-mini",
        openai_client=openai_client
    ),
    model_settings=ModelSettings(temperature=0.7)
)

local_agent = Agent(
    name="当地专家",
    handoff_description="专门推荐地道当地活动和旅游景点的专家",
    instructions=prompt_with_handoff_instructions("""
    你是目的地的当地专家，能够推荐地道有趣的当地活动或旅游景点。

    请专注于：
    1. 推荐鲜为人知的景点，避开纯粹的旅游陷阱
    2. 提供当地美食和餐厅建议
    3. 分享特色文化体验和活动
    4. 提供只有当地人才知道的实用提示

    如果用户可能需要目的地的语言帮助，可以交接给"语言指南"。
    当你完成当地推荐后，请交接给"旅行计划编译器"以整合所有建议。
    """),
    model=OpenAIChatCompletionsModel(
        model="gpt-4o-mini",
        openai_client=openai_client
    )
)

language_agent = Agent(
    name="语言指南",
    handoff_description="目的地语言和沟通技巧的专家",
    instructions=prompt_with_handoff_instructions("""
    你是语言和文化沟通专家，提供针对旅行目的地的语言支持。

    请专注于：
    1. 提供目的地常用语言的关键短语和表达
    2. 解释可能的沟通挑战和解决方案
    3. 介绍与语言相关的当地文化礼仪
    4. 提供实用的语言学习资源或建议

    完成语言指南后，请交接给"旅行计划编译器"以整合所有建议成为完整的旅行计划。
    """),
    model=OpenAIChatCompletionsModel(
        model="gpt-4o-mini",
        openai_client=openai_client
    )
)

# 定义汇总所有建议的总结代理
summary_agent = Agent(
    name="旅行计划编译器",
    handoff_description="将所有建议汇编成完整旅行计划的最终代理",
    instructions="""
    你是一个专业的旅行计划编译器，负责整合各专家的建议成为完整的旅行计划。

    你的任务是：
    1. 审查旅行规划师、当地专家和语言指南提供的所有信息
    2. 创建一个整合所有观点的详细旅行计划
    3. 确保计划完整、实用且结构良好
    4. 包括每天的具体细节、当地推荐和语言提示

    请以以下JSON格式提供您的回复：
    {
        "destination": "目的地名称",
        "duration": "旅行时长",
        "itinerary": "详细的日程安排",
        "local_recommendations": "当地专家推荐",
        "language_tips": "目的地语言提示",
        "summary": "整体计划简要总结"
    }

    确保所有字段都有完整的内容，输出格式必须是有效的JSON。
    """,
    output_type=TravelPlan,
    model=OpenAIChatCompletionsModel(
        model="gpt-4o-mini",
        openai_client=openai_client
    )
)

# 设置代理网络和适当的交接 - 使用handoff函数创建更明确的交接
# 规划师的交接选项
to_local_expert = handoff(
    agent=local_agent,
    tool_name_override="consult_local_expert",
    tool_description_override="当需要地道的当地体验、隐藏景点或特色美食建议时使用此工具。"
)

to_language_guide = handoff(
    agent=language_agent,
    tool_name_override="consult_language_guide",
    tool_description_override="当需要目的地语言指南、关键短语或文化沟通建议时使用此工具。"
)

to_travel_compiler = handoff(
    agent=summary_agent,
    tool_name_override="compile_travel_plan",
    tool_description_override="当所有必要信息都已收集完毕，需要编译最终旅行计划时使用此工具。"
)

# 设置交接关系
planner_agent.handoffs = [to_local_expert, to_language_guide]
local_agent.handoffs = [to_language_guide, to_travel_compiler]
language_agent.handoffs = [to_travel_compiler]

# 入口点函数
async def plan_trip(destination_prompt):
    # 添加错误处理
    try:
        # 从规划师代理开始
        result = await Runner.run(planner_agent, destination_prompt)

        # 打印输出
        print("\n=== 旅行计划 ===\n")

        # 尝试解析输出为TravelPlan对象
        try:
            if isinstance(result.final_output, TravelPlan):
                # 如果直接得到TravelPlan对象
                travel_plan = result.final_output
                print(f"目的地: {travel_plan.destination}")
                print(f"时长: {travel_plan.duration}")
                print("\n行程安排:")
                print(travel_plan.itinerary)
                print("\n当地推荐:")
                print(travel_plan.local_recommendations)
                print("\n语言提示:")
                print(travel_plan.language_tips)
                print("\n摘要:")
                print(travel_plan.summary)
            elif isinstance(result.final_output, str):
                # 在输出中查找JSON
                try:
                    # 尝试提取嵌入在文本中的JSON
                    start_idx = result.final_output.find('{')
                    end_idx = result.final_output.rfind('}') + 1

                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = result.final_output[start_idx:end_idx]
                        travel_data = json.loads(json_str)
                        travel_plan = TravelPlan(**travel_data)

                        print(f"目的地: {travel_plan.destination}")
                        print(f"时长: {travel_plan.duration}")
                        print("\n行程安排:")
                        print(travel_plan.itinerary)
                        print("\n当地推荐:")
                        print(travel_plan.local_recommendations)
                        print("\n语言提示:")
                        print(travel_plan.language_tips)
                        print("\n摘要:")
                        print(travel_plan.summary)
                    else:
                        # 如果没有找到JSON，直接打印输出
                        print("未找到结构化旅行计划，原始输出:")
                        print(result.final_output)
                except (json.JSONDecodeError, ValidationError) as e:
                    print(f"解析JSON失败: {e}")
                    print("原始输出:")
                    print(result.final_output)
            else:
                # 未知输出类型
                print(f"未知输出类型: {type(result.final_output)}")
                print(result.final_output)
        except Exception as e:
            print(f"处理结果时出错: {e}")
            print("原始输出:")
            print(result.final_output)

        # 打印交接路径信息，便于调试
        if hasattr(result, 'new_items') and result.new_items:
            handoffs_occurred = [item for item in result.new_items if item.type == "handoff_output_item"]
            if handoffs_occurred:
                print("\n===== 交接路径 =====")
                for idx, handoff_item in enumerate(handoffs_occurred):
                    print(f"{idx + 1}. {handoff_item.source_agent.name} → {handoff_item.target_agent.name}")

        return result
    except Exception as e:
        print(f"执行过程中出错: {e}")
        return None

# 运行旅行规划器
if __name__ == "__main__":
    try:
        asyncio.run(plan_trip("规划一个3天的尼泊尔旅行。"))
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序执行出错: {e}")