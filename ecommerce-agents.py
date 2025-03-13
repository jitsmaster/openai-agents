# ------------------------------代码------------------------------
# 模拟电商系统
from agents import Agent, Runner, handoff, AsyncOpenAI, function_tool
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
import asyncio

# 模拟数据库
order_database = {
    "ORD12345": {
        "status": "已发货",
        "date": "2025-03-05",
        "items": ["手机壳", "耳机"],
        "total": 299.99,
        "tracking": "SF1234567890",
        "customer_email": "customer@example.com"
    },
    "ORD67890": {
        "status": "待付款",
        "date": "2025-03-10",
        "items": ["平板电脑", "保护膜"],
        "total": 2499.99,
        "customer_email": "another@example.com"
    }
}

# 定义工具函数
@function_tool
def check_order_status(order_id: str) -> str:
    """查询订单状态"""
    if order_id in order_database:
        order = order_database[order_id]
        return f"订单 {order_id} 当前状态: {order['status']}，下单日期: {order['date']}，金额: ¥{order['total']}"
    return f"未找到订单 {order_id}"

@function_tool
def get_tracking_info(order_id: str) -> str:
    """获取物流信息"""
    if order_id in order_database and order_database[order_id].get("tracking"):
        return f"订单 {order_id} 的物流单号是: {order_database[order_id]['tracking']}"
    return f"订单 {order_id} 暂无物流信息或订单不存在"

# 定义专业代理

# 订单查询代理
order_agent = Agent(
    name="订单查询专员",
    instructions="""
    你是电子商务平台的订单查询专员。你可以帮助客户查询订单状态和物流信息。

    你需要获取订单号才能提供帮助。如果客户没有提供订单号，请礼貌地询问。

    请记住，你的职责只是查询和提供订单信息。如果客户提出其他需求（如退款或投诉），请向客户说明你只负责订单查询，并建议他们联系相关部门。
    """,
    tools=[check_order_status, get_tracking_info]
)

# 退款处理代理
refund_agent = Agent(
    name="退款处理专员",
    instructions="""
    你是电子商务平台的退款处理专员。

    处理退款请求时，请遵循以下步骤：
    1. 确认订单信息和退款原因
    2. 检查退款资格（例如退货时间、产品状态等）
    3. 解释退款流程和预计到账时间

    对于不符合退款条件的情况，请清楚解释原因并提供替代解决方案。
    """,
    tools=[check_order_status]
)

# 投诉处理代理
complaint_agent = Agent(
    name="客户投诉专员",
    instructions="""
    你是电子商务平台的客户投诉专员。你的目标是理解客户的不满并寻找解决方案。

    请记住：
    1. 首先表示同理心和理解
    2. 获取所有相关信息
    3. 提供明确的解决方案或后续步骤
    4. 在适当的情况下提供补偿（如优惠券、积分等）

    对于特别严重或复杂的投诉，可以承诺由主管跟进处理。
    """,
    tools=[check_order_status]
)

# 设置交接 - 修改名称使其更具描述性和区分度
transfer_to_order_specialist = handoff(
    agent=order_agent,
    tool_name_override="transfer_to_order_specialist",
    tool_description_override="当客户需要查询订单状态或物流信息时使用此工具。例如：'我想查询订单状态'、'我的包裹到哪了'等情况。"
)

transfer_to_refund_specialist = handoff(
    agent=refund_agent,
    tool_name_override="transfer_to_refund_specialist",
    tool_description_override="当客户明确要求退款或退货时使用此工具。例如：'我想申请退款'、'如何退货'等情况。"
)

transfer_to_complaint_specialist = handoff(
    agent=complaint_agent,
    tool_name_override="transfer_to_complaint_specialist",
    tool_description_override="仅当客户明确表示不满、抱怨或投诉时使用此工具。例如：'我对服务很不满'、'我要投诉'等情况。"
)

# 前台接待代理 - 使用更明确的指令和例子
main_agent = Agent(
    name="客服前台",
    instructions=prompt_with_handoff_instructions("""
    你是电子商务平台的客服前台。你的工作是了解客户需求并将他们引导至合适的专业客服。请根据以下明确的指引决定如何处理客户查询：

    1. 订单查询类问题：
       - 示例："我想查询订单状态"、"我的包裹什么时候到"、"能告诉我订单号XXX的情况吗"
       - 操作：使用transfer_to_order_specialist工具

    2. 退款类问题：
       - 示例："我想申请退款"、"这个产品有问题，我要退货"、"如何办理退款"
       - 操作：使用transfer_to_refund_specialist工具

    3. 投诉类问题：
       - 示例："我对你们的服务很不满"、"我要投诉"、"这个体验太糟糕了"
       - 操作：使用transfer_to_complaint_specialist工具

    4. 一般问题：
       - 示例："你们的营业时间是什么时候"、"如何修改收货地址"等
       - 操作：直接回答客户

    重要规则：
    - 请严格按照上述分类选择适当的交接工具
    - 不要过度解读客户意图，根据客户明确表达的需求选择工具
    - 如果不确定，先询问更多信息，而不是急于交接
    - 首次交流时，除非客户明确表达了投诉或退款需求，否则应该先用order_specialist处理
    """)
)

# 设置主代理的交接，按常见度排序
main_agent.handoffs = [
    transfer_to_order_specialist,  # 最常见的请求类型，放在最前面
    transfer_to_refund_specialist,  # 第二常见
    transfer_to_complaint_specialist  # 最不常见
]

# 主函数
async def handle_customer_query(query):
    print(f"\n===== 新的客户查询 =====")
    print(f"客户: {query}")

    try:
        result = await Runner.run(main_agent, query)
        print(f"\n客服回复: {result.final_output}")

        # 打印交接路径信息
        if hasattr(result, 'new_items') and result.new_items:
            handoffs_occurred = [item for item in result.new_items if item.type == "handoff_output_item"]
            if handoffs_occurred:
                print("\n===== 交接路径 =====")
                for idx, handoff_item in enumerate(handoffs_occurred):
                    print(f"{idx + 1}. {handoff_item.source_agent.name} → {handoff_item.target_agent.name}")
                    # 打印使用的工具名称，帮助调试
                    if hasattr(handoff_item, 'tool_name') and handoff_item.tool_name:
                        print(f"   使用工具: {handoff_item.tool_name}")
            else:
                # 如果没有交接发生，也打印出来便于调试
                print("\n没有交接发生，主代理直接处理了请求")

        return result
    except Exception as e:
        print(f"处理查询时出错: {e}")
        return None

# 示例查询
async def run_demo():
    queries = [
        "你好，我想查询一下我的订单状态",
        "我的订单号是ORD12345",
        "我想申请退款，订单ORD12345中的耳机质量有问题",
        "我对你们的配送速度非常不满，已经等了一周还没收到货！",
    ]

    for query in queries:
        try:
            await handle_customer_query(query)
        except Exception as e:
            print(f"处理查询'{query}'时出错: {e}")
        print("\n" + "=" * 50 + "\n")

if __name__ == "__main__":
    asyncio.run(run_demo())