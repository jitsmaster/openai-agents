# ------------------------------Code------------------------------
# Support Case Handling System
from agents import Agent, Runner, handoff, AsyncOpenAI, function_tool
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
import asyncio
import json
from datetime import datetime

# Mock Database
support_cases = {
    "CASE001": {
        "title": "Unable to connect to service",
        "description": "Customer reports unable to connect to our API service, connection timeout.",
        "status": "Pending",
        "customer_email": "customer@example.com",
        "created_at": "2025-03-10",
        "product": "API Gateway",
        "service": "Connection Service"
    },
    "CASE002": {
        "title": "Data synchronization failure",
        "description": "Customer encountered an error when using the data synchronization feature, error code: SYNC-404.",
        "status": "Pending",
        "customer_email": "client@example.com",
        "created_at": "2025-03-11",
        "product": "Data Synchronizer",
        "service": "Sync Service"
    },
    "CASE003": {
        "title": "User interface button not responding",
        "description": "Customer reports that the 'Refresh Data' button on the dashboard page does not respond after clicking.",
        "status": "Pending",
        "customer_email": "user@example.com",
        "created_at": "2025-03-12",
        "product": "Web Dashboard",
        "service": "Frontend Service"
    }
}

# Mock Knowledge Base
knowledge_base = {
    "API Gateway": {
        "common_issues": [
            "Connection timeouts are usually caused by firewall settings or network configuration issues",
            "API key validation failures may be due to expired keys or insufficient permissions"
        ],
        "troubleshooting": [
            "Check network connections and firewall settings",
            "Verify if the API key is valid",
            "Check the service status page to confirm if the service is running normally"
        ]
    },
    "Data Synchronizer": {
        "common_issues": [
            "SYNC-404 error indicates that the source data to be synchronized cannot be found",
            "Synchronization failures may be due to data format incompatibility or permission issues"
        ],
        "troubleshooting": [
            "Confirm that the source data exists and is accessible",
            "Check if the data format meets the requirements",
            "Verify user permission settings"
        ]
    },
    "Web Dashboard": {
        "common_issues": [
            "Unresponsive buttons may be caused by JavaScript errors",
            "Slow page loading is usually related to large data volumes or network latency"
        ],
        "troubleshooting": [
            "Clear browser cache and cookies",
            "Try using a different browser",
            "Check the browser console for error messages"
        ]
    }
}

# Mock Azure DevOps Ticket System
devops_tickets = []
ticket_counter = 1001

# Define Tool Functions
@function_tool
def check_case_details(case_id: str) -> str:
    """Query support case details"""
    if case_id in support_cases:
        case = support_cases[case_id]
        return f"Case {case_id} details:\nTitle: {case['title']}\nDescription: {case['description']}\nStatus: {case['status']}\nProduct: {case['product']}\nService: {case['service']}\nCreated at: {case['created_at']}"
    return f"Case {case_id} not found"

@function_tool
def check_knowledge_base(product: str) -> str:
    """Query product knowledge base information"""
    if product in knowledge_base:
        kb = knowledge_base[product]
        common_issues = "\n".join([f"- {issue}" for issue in kb["common_issues"]])
        troubleshooting = "\n".join([f"- {step}" for step in kb["troubleshooting"]])
        return f"Product '{product}' knowledge base:\n\nCommon issues:\n{common_issues}\n\nTroubleshooting steps:\n{troubleshooting}"
    return f"Knowledge base information for product '{product}' not found"

@function_tool
def create_bug_ticket(title: str, description: str, product: str, severity: str) -> str:
    """Create Bug ticket"""
    global ticket_counter
    ticket_id = f"BUG-{ticket_counter}"
    ticket_counter += 1
    
    ticket = {
        "id": ticket_id,
        "type": "Bug",
        "title": title,
        "description": description,
        "product": product,
        "severity": severity,
        "status": "New",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    devops_tickets.append(ticket)
    return f"Bug ticket created: {ticket_id}\nTitle: {title}\nProduct: {product}\nSeverity: {severity}\nStatus: New\nAzure DevOps URL: https://dev.azure.com/company/project/_workitems/edit/{ticket_id}"

@function_tool
def create_doc_request(title: str, description: str, product: str) -> str:
    """Create documentation request ticket"""
    global ticket_counter
    ticket_id = f"DOC-{ticket_counter}"
    ticket_counter += 1
    
    ticket = {
        "id": ticket_id,
        "type": "Documentation",
        "title": title,
        "description": description,
        "product": product,
        "status": "New",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    devops_tickets.append(ticket)
    return f"Documentation request ticket created: {ticket_id}\nTitle: {title}\nProduct: {product}\nStatus: New\nAzure DevOps URL: https://dev.azure.com/company/project/_workitems/edit/{ticket_id}"

# Define Professional Agents

# Support Engineer Agent
support_engineer = Agent(
    name="Support Engineer",
    instructions=prompt_with_handoff_instructions("""
    You are a professional support engineer responsible for handling customer cases and triaging them within the team.

    Your responsibilities include:
    1. Analyzing customer cases and understanding the nature of the problem
    2. If you know the solution, provide it directly to the customer
    3. If the case involves service implementation issues, use the consult_service_engineer tool to consult with a service engineer
    4. If the case involves product features that might be bugs, use the consult_product_engineer tool to consult with a product development engineer
    5. Based on the product development engineer's feedback, take the following actions:
       - If it's a bug: Create a bug ticket and provide the ticket URL to the customer
       - If it's a documentation issue: Create a documentation request ticket and inform the customer how to handle it
       - If it's a user error: Provide the customer with the correct usage method

    Important rules:
    - When you're unsure how to solve a problem, always consult with the appropriate professional engineer
    - After receiving feedback from professional engineers, you must take appropriate actions based on the feedback
    - When communicating with customers, maintain professionalism, clarity, and helpfulness
    - Ensure you provide complete solutions or clear next steps
    """),
    tools=[check_case_details, check_knowledge_base, create_bug_ticket, create_doc_request]
)

# Service Engineer Agent
service_engineer = Agent(
    name="Service Engineer",
    instructions=prompt_with_handoff_instructions("""
    You are a professional service engineer with deep knowledge about service implementation.

    When the support engineer consults you, you need to:
    1. Analyze problems related to service implementation
    2. Provide professional technical insights and recommendations
    3. Explain possible service configuration issues or errors
    4. Provide detailed troubleshooting steps
    5. If applicable, suggest best practices or optimization solutions

    Please ensure your answers are technically accurate and detailed enough for the support engineer to understand the problem and provide effective solutions to the customer.
    
    Important: Your response should clearly indicate whether the problem is a service configuration issue, a known issue, or an issue that requires further investigation.
    """),
    tools=[check_case_details, check_knowledge_base]
)

# Product Development Engineer Agent
product_engineer = Agent(
    name="Product Development Engineer",
    instructions=prompt_with_handoff_instructions("""
    You are a product development engineer responsible for analyzing issues related to product features.

    When the support engineer consults you, you need to:
    1. Analyze whether the issue is a product bug, missing documentation, or user error
    2. Provide detailed technical analysis and insights
    3. Clearly identify the type of issue and provide the following information:
       - If it's a bug: Describe the nature of the bug, possible causes, and severity
       - If it's a documentation issue: Indicate what documentation needs to be added or updated
       - If it's a user error: Explain the correct usage method

    Important: You must clearly label the issue type (BUG, DOCUMENTATION ISSUE, or USER ERROR) at the beginning of your response so that the support engineer can take appropriate follow-up actions. For example:
    "Issue type: BUG
    Analysis: ..."
    
    Please ensure your analysis is accurate, comprehensive, and provides sufficient technical details.
    """),
    tools=[check_case_details, check_knowledge_base]
)

# Set up handoffs - Modify names to make them more descriptive and distinctive
consult_service_engineer = handoff(
    agent=service_engineer,
    tool_name_override="consult_service_engineer",
    tool_description_override="Use this tool when the case involves service implementation issues and requires the expertise of a service engineer."
)

consult_product_engineer = handoff(
    agent=product_engineer,
    tool_name_override="consult_product_engineer",
    tool_description_override="Use this tool when the case involves product features that might be bugs and requires analysis and insights from a product development engineer."
)

# Set up handoffs for the support engineer
support_engineer.handoffs = [
    consult_service_engineer,
    consult_product_engineer
]

# Main function
async def handle_support_case(case_id, customer_query=None):
    print(f"\n===== New Support Case =====")
    
    # Get case details
    case_details = ""
    if case_id in support_cases:
        case = support_cases[case_id]
        case_details = f"Case ID: {case_id}\nTitle: {case['title']}\nDescription: {case['description']}\nProduct: {case['product']}\nService: {case['service']}"
    else:
        case_details = f"Case {case_id} not found"
    
    print(case_details)
    
    # Build query
    if customer_query:
        query = f"Please handle the following support case:\n{case_details}\n\nCustomer query: {customer_query}"
    else:
        query = f"Please handle the following support case:\n{case_details}"
    
    print(f"\nCustomer query: {customer_query if customer_query else 'No additional query'}")

    try:
        # Run support engineer agent
        result = await Runner.run(support_engineer, query)
        print(f"\nSupport Engineer response: {result.final_output}")

        # Print handoff path information
        if hasattr(result, 'new_items') and result.new_items:
            handoffs_occurred = [item for item in result.new_items if item.type == "handoff_output_item"]
            if handoffs_occurred:
                print("\n===== Handoff Path =====")
                for idx, handoff_item in enumerate(handoffs_occurred):
                    print(f"{idx + 1}. {handoff_item.source_agent.name} → {handoff_item.target_agent.name}")
                    # Print tool name used, for debugging
                    if hasattr(handoff_item, 'tool_name') and handoff_item.tool_name:
                        print(f"   Tool used: {handoff_item.tool_name}")
            else:
                # If no handoff occurred, print it for debugging
                print("\nNo handoff occurred, Support Engineer handled the request directly")

        # Print created tickets (if any)
        if devops_tickets:
            print("\n===== Created Tickets =====")
            for ticket in devops_tickets:
                print(f"ID: {ticket['id']}")
                print(f"Type: {ticket['type']}")
                print(f"Title: {ticket['title']}")
                print(f"Product: {ticket['product']}")
                if 'severity' in ticket:
                    print(f"Severity: {ticket['severity']}")
                print(f"Status: {ticket['status']}")
                print(f"Created at: {ticket['created_at']}")
                print(f"URL: https://dev.azure.com/company/project/_workitems/edit/{ticket['id']}")
                print("---")

        return result
    except Exception as e:
        print(f"Error processing case: {e}")
        return None

# Example queries
async def run_demo():
    # Clear ticket list to ensure each run starts fresh
    global devops_tickets
    devops_tickets = []
    
    cases = [
        # Case 1: Problem that support engineer can solve directly
        {
            "case_id": "CASE001",
            "query": "Our team cannot connect to the API service, it keeps showing connection timeout. We have checked our network and there's no problem on our end."
        },
        # Case 2: Problem requiring service engineer assistance
        {
            "case_id": "CASE002",
            "query": "We encountered a SYNC-404 error when using the data synchronization feature. We have confirmed that the source data exists, but the synchronization still fails."
        },
        # Case 3: Problem requiring product development engineer assistance (possible bug)
        {
            "case_id": "CASE003",
            "query": "The 'Refresh Data' button on the dashboard doesn't respond at all. We've tried different browsers, cleared cache, but the problem persists. The console shows JavaScript errors."
        },
        # Case 4: Problem requiring product development engineer assistance (documentation issue)
        {
            "case_id": "CASE003",
            "query": "We can't find documentation on how to configure the dashboard's auto-refresh feature. We've looked through all the documentation but couldn't find any related instructions."
        },
        # Case 5: Problem requiring product development engineer assistance (user error)
        {
            "case_id": "CASE003",
            "query": "The data on the dashboard doesn't update automatically. We have to manually click the refresh button. Is this a bug?"
        }
    ]

    for case in cases:
        try:
            await handle_support_case(case["case_id"], case["query"])
        except Exception as e:
            print(f"Error processing case '{case['case_id']}': {e}")
        print("\n" + "=" * 50 + "\n")

if __name__ == "__main__":
    asyncio.run(run_demo())
