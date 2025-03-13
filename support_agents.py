# Support Case Handling System Module
from agents import Agent, Runner, handoff, AsyncOpenAI, function_tool
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
import asyncio
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
    },
    "CASE004": {
        "title": "Complex issue with multiple components",
        "description": "Customer reports a complex issue that involves both frontend and backend components, with potential documentation gaps.",
        "status": "Pending",
        "customer_email": "enterprise@example.com",
        "created_at": "2025-03-13",
        "product": "Enterprise Dashboard",
        "service": "Full Stack Service"
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
    },
    "Enterprise Dashboard": {
        "common_issues": [
            "Integration issues between frontend and backend components",
            "Performance degradation with large datasets",
            "Authentication and authorization problems across multiple services"
        ],
        "troubleshooting": [
            "Check system logs for errors in both frontend and backend components",
            "Verify API endpoints are correctly configured",
            "Ensure all required services are running",
            "Check user permissions across all integrated systems"
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

# Define additional tool functions for complex case handling
@function_tool
def request_additional_info(question: str) -> str:
    """Request additional information from the customer"""
    return f"Additional information requested: {question}"

@function_tool
def provide_additional_info(info: str) -> str:
    """Provide additional information to the engineer"""
    return f"Additional information provided: {info}"

@function_tool
def request_logs(log_type: str) -> str:
    """Request specific logs from the customer"""
    return f"Logs requested: {log_type}"

@function_tool
def provide_logs(logs: str) -> str:
    """Provide logs to the engineer"""
    return f"Logs provided: {logs}"

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
       - If it's a bug: Use the create_bug_ticket_handoff tool to hand off to the Bug Ticketing Agent
       - If it's a documentation issue: Use the create_documentation_ticket tool to hand off to the Documentation Ticketing Agent
       - If it's a user error: Provide the customer with the correct usage method
    6. After receiving ticket information from the Bug or Documentation Ticketing Agent, relay this information to the customer

    Important rules:
    - When you're unsure how to solve a problem, always consult with the appropriate professional engineer
    - After receiving feedback from professional engineers, you must take appropriate actions based on the feedback
    - When communicating with customers, maintain professionalism, clarity, and helpfulness
    - Ensure you provide complete solutions or clear next steps
    - For complex issues, you may need to consult multiple engineers and create multiple tickets
    
    For complex cases (especially those involving multiple components):
    - You should engage in multiple rounds of consultation with each engineer
    - After receiving initial feedback, ask follow-up questions to get more detailed information
    - Request specific technical details, logs, or configuration information when needed
    - Summarize what you've learned from one engineer before consulting another
    - For issues spanning multiple areas, consult with different engineers about their respective domains
    - Always follow up with engineers if their initial response doesn't fully address the issue
    """),
    tools=[check_case_details, check_knowledge_base, create_bug_ticket, create_doc_request, 
           request_additional_info, provide_additional_info, request_logs, provide_logs]
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
    
    For complex cases:
    - If you don't have enough information to provide a complete analysis, ask the support engineer specific questions
    - Request logs, configuration details, or specific error messages when needed
    - Provide partial analysis based on available information, then request more details
    - After receiving additional information, provide more detailed analysis and recommendations
    - For issues that might involve multiple components, clearly indicate which aspects you can address and which might require consultation with other engineers
    - Always provide actionable next steps, even if they're just to gather more information
    """),
    tools=[check_case_details, check_knowledge_base, request_additional_info, request_logs]
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
    
    For complex cases:
    - If you need more information to determine the exact nature of the issue, ask specific questions
    - Request code samples, screenshots, or specific error messages when needed
    - If an issue might be a combination of multiple types (e.g., both a bug and documentation issue), analyze each aspect separately
    - For issues that span multiple components, provide analysis for each component
    - After receiving additional information, refine your analysis and provide more specific recommendations
    - Always be clear about what additional information would help you provide a more accurate analysis
    """),
    tools=[check_case_details, check_knowledge_base, request_additional_info, request_logs]
)

# Documentation Ticketing Agent
documentation_agent = Agent(
    name="Documentation Ticketing Agent",
    instructions=prompt_with_handoff_instructions("""
    You are a documentation ticketing agent responsible for creating documentation request tickets.

    When the support engineer hands off to you, you need to:
    1. Review the documentation issue details provided by the support engineer
    2. Create a formal documentation request ticket with appropriate details
    3. Return the ticket information to the support engineer
    
    Important:
    - Ensure the ticket title clearly describes the documentation need
    - Include relevant product information in the ticket
    - Provide a comprehensive description that explains what documentation needs to be created or updated
    - Return the complete ticket information so the support engineer can relay it to the customer
    
    For complex documentation requests:
    - If the information provided is insufficient, ask specific questions to clarify the documentation needs
    - Request examples, use cases, or specific scenarios that should be covered in the documentation
    - For documentation that spans multiple features or components, create detailed sections for each component
    - After receiving additional information, create a more comprehensive ticket
    - Suggest related documentation that might also need updates
    """),
    tools=[create_doc_request, check_knowledge_base, request_additional_info]
)

# Bug Ticketing Agent
bug_agent = Agent(
    name="Bug Ticketing Agent",
    instructions=prompt_with_handoff_instructions("""
    You are a bug ticketing agent responsible for creating bug tickets.

    When the support engineer hands off to you, you need to:
    1. Review the bug details provided by the support engineer
    2. Create a formal bug ticket with appropriate details
    3. Assign the correct severity level based on the impact
    4. Return the ticket information to the support engineer
    
    Important:
    - Ensure the ticket title clearly describes the bug
    - Include relevant product information in the ticket
    - Provide a comprehensive description that helps developers understand and reproduce the issue
    - Assign an appropriate severity level (Critical, High, Medium, Low)
    - Return the complete ticket information so the support engineer can relay it to the customer
    
    For complex bugs:
    - If the information provided is insufficient to create a complete ticket, ask specific questions
    - Request steps to reproduce, error logs, or specific error messages when needed
    - For bugs that affect multiple components, create detailed sections for each affected component
    - After receiving additional information, create a more comprehensive ticket
    - Suggest related areas that might also be affected by the bug
    - For high-severity bugs, request additional information about business impact
    """),
    tools=[create_bug_ticket, check_knowledge_base, request_additional_info]
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

create_documentation_ticket = handoff(
    agent=documentation_agent,
    tool_name_override="create_documentation_ticket",
    tool_description_override="Use this tool when you need to create a documentation request ticket. Provide details about what documentation needs to be created or updated."
)

create_bug_ticket_handoff = handoff(
    agent=bug_agent,
    tool_name_override="create_bug_ticket_handoff",
    tool_description_override="Use this tool when you need to create a bug ticket. Provide details about the bug, including its severity and impact."
)

# Set up handoffs for the support engineer
support_engineer.handoffs = [
    consult_service_engineer,
    consult_product_engineer,
    create_documentation_ticket,
    create_bug_ticket_handoff
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

    # For complex case (CASE004), use the specialized handler
    if case_id == "CASE004":
        return await handle_complex_case(case_id, case_details, customer_query)

    # For regular cases, use the standard handler
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

# Specialized handler for complex cases with multiple handoffs
async def handle_complex_case(case_id, case_details, customer_query=None):
    print(f"\n===== Complex Case Handler =====")
    print(f"Processing complex case: {case_id}")
    
    # Build initial query
    if customer_query:
        query = f"Please handle the following complex support case:\n{case_details}\n\nCustomer query: {customer_query}"
    else:
        query = f"Please handle the following complex support case:\n{case_details}"
    
    # Track all handoffs for visualization
    all_handoffs = []
    
    try:
        # Step 1: Initial consultation with Support Engineer
        print("\n----- Step 1: Initial Support Engineer Assessment -----")
        initial_result = await Runner.run(support_engineer, query)
        print(f"Support Engineer initial assessment: {initial_result.final_output}")
        
        # Extract handoffs from initial consultation
        if hasattr(initial_result, 'new_items') and initial_result.new_items:
            initial_handoffs = [item for item in initial_result.new_items if item.type == "handoff_output_item"]
            all_handoffs.extend(initial_handoffs)
        
        # Step 2: First consultation with Service Engineer about backend issues
        print("\n----- Step 2: First Service Engineer Consultation -----")
        service_query = f"""
        I need your expertise on a complex case:
        {case_details}
        
        The customer is experiencing API calls timing out intermittently. 
        Can you provide an initial assessment of what might be causing these backend issues?
        """
        service_result_1 = await Runner.run(service_engineer, service_query)
        print(f"Service Engineer initial response: {service_result_1.final_output}")
        
        # Record this handoff manually since we're not using the handoff mechanism
        all_handoffs.append({
            "source_agent": {"name": "Support Engineer"},
            "target_agent": {"name": "Service Engineer"},
            "tool_name": "direct_consultation_1"
        })
        
        # Step 3: Support Engineer requests more information from Service Engineer
        print("\n----- Step 3: Support Engineer Follows Up with Service Engineer -----")
        followup_query = f"""
        Thank you for your initial assessment. I need more specific information:
        
        1. What logs should we request from the customer to diagnose the API timeout issues?
        2. Are there any specific configuration settings we should check?
        3. Could this be related to the data visualization issues, or are these separate problems?
        
        Original case details:
        {case_details}
        """
        service_result_2 = await Runner.run(service_engineer, followup_query)
        print(f"Service Engineer follow-up response: {service_result_2.final_output}")
        
        # Record this handoff
        all_handoffs.append({
            "source_agent": {"name": "Support Engineer"},
            "target_agent": {"name": "Service Engineer"},
            "tool_name": "direct_consultation_2"
        })
        
        # Step 4: Support Engineer provides additional information to Service Engineer
        print("\n----- Step 4: Support Engineer Provides Additional Information -----")
        additional_info = f"""
        I've gathered the following information from the customer:
        
        - API timeouts occur approximately every 15 minutes
        - They're using our REST API with the standard authentication method
        - The issue started after they upgraded to the latest version
        - Their system logs show connection reset errors
        
        Based on this information, can you provide more specific troubleshooting steps?
        
        Original case details:
        {case_details}
        """
        service_result_3 = await Runner.run(service_engineer, additional_info)
        print(f"Service Engineer detailed response: {service_result_3.final_output}")
        
        # Record this handoff
        all_handoffs.append({
            "source_agent": {"name": "Support Engineer"},
            "target_agent": {"name": "Service Engineer"},
            "tool_name": "direct_consultation_3"
        })
        
        # Step 5: First consultation with Product Engineer about frontend issues
        print("\n----- Step 5: First Product Engineer Consultation -----")
        product_query = f"""
        I need your expertise on a complex case:
        {case_details}
        
        The customer is experiencing issues with data visualization components not displaying correctly.
        Can you analyze whether this is a bug, documentation issue, or user error?
        """
        product_result_1 = await Runner.run(product_engineer, product_query)
        print(f"Product Engineer initial response: {product_result_1.final_output}")
        
        # Record this handoff
        all_handoffs.append({
            "source_agent": {"name": "Support Engineer"},
            "target_agent": {"name": "Product Engineer"},
            "tool_name": "direct_consultation_1"
        })
        
        # Step 6: Support Engineer requests more information from Product Engineer
        print("\n----- Step 6: Support Engineer Follows Up with Product Engineer -----")
        product_followup = f"""
        Thank you for your initial assessment. I need more specific information:
        
        1. What browser console errors should we look for related to the visualization issues?
        2. Are there any known issues with the current version of the visualization components?
        3. What specific information should we gather from the customer to determine if this is a bug?
        
        Original case details:
        {case_details}
        """
        product_result_2 = await Runner.run(product_engineer, product_followup)
        print(f"Product Engineer follow-up response: {product_result_2.final_output}")
        
        # Record this handoff
        all_handoffs.append({
            "source_agent": {"name": "Support Engineer"},
            "target_agent": {"name": "Product Engineer"},
            "tool_name": "direct_consultation_2"
        })
        
        # Step 7: Support Engineer provides additional information to Product Engineer
        print("\n----- Step 7: Support Engineer Provides Additional Information to Product Engineer -----")
        product_additional_info = f"""
        I've gathered the following information from the customer:
        
        - The visualization issues occur in Chrome, Firefox, and Edge browsers
        - Console shows "Uncaught TypeError: Cannot read property 'data' of undefined"
        - The issue happens consistently when filtering data by date range
        - They're using version 2.5.3 of the Enterprise Dashboard
        
        Based on this information, can you confirm if this is a bug and provide severity assessment?
        
        Original case details:
        {case_details}
        """
        product_result_3 = await Runner.run(product_engineer, product_additional_info)
        print(f"Product Engineer detailed response: {product_result_3.final_output}")
        
        # Record this handoff
        all_handoffs.append({
            "source_agent": {"name": "Support Engineer"},
            "target_agent": {"name": "Product Engineer"},
            "tool_name": "direct_consultation_3"
        })
        
        # Step 8: Create bug ticket based on Product Engineer's assessment
        print("\n----- Step 8: Create Bug Ticket -----")
        bug_query = f"""
        Based on the Product Engineer's assessment, I need to create a bug ticket for the following issue:
        
        Product: Enterprise Dashboard
        Issue: Data visualization components fail when filtering by date range
        Error: "Uncaught TypeError: Cannot read property 'data' of undefined"
        Impact: Blocking business operations, affecting all users
        Reproducible: Yes, consistently when filtering by date range
        
        Please create a formal bug ticket with appropriate severity.
        """
        bug_result = await Runner.run(bug_agent, bug_query)
        print(f"Bug Ticket Agent response: {bug_result.final_output}")
        
        # Record this handoff
        all_handoffs.append({
            "source_agent": {"name": "Support Engineer"},
            "target_agent": {"name": "Bug Ticketing Agent"},
            "tool_name": "create_bug_ticket_handoff"
        })
        
        # Step 9: Create documentation ticket for missing documentation
        print("\n----- Step 9: Create Documentation Ticket -----")
        doc_query = f"""
        I need to create a documentation request ticket for the following issue:
        
        Product: Enterprise Dashboard
        Missing Documentation: Configuration guide for advanced filtering options
        Impact: Users cannot properly configure and use advanced filtering features
        Details: The customer cannot find documentation on how to configure the advanced filtering options,
                which is critical for their business operations.
        
        Please create a formal documentation request ticket.
        """
        doc_result = await Runner.run(documentation_agent, doc_query)
        print(f"Documentation Ticket Agent response: {doc_result.final_output}")
        
        # Record this handoff
        all_handoffs.append({
            "source_agent": {"name": "Support Engineer"},
            "target_agent": {"name": "Documentation Ticketing Agent"},
            "tool_name": "create_documentation_ticket"
        })
        
        # Step 10: Final response from Support Engineer
        print("\n----- Step 10: Final Support Engineer Response -----")
        final_query = f"""
        Now that I've consulted with multiple engineers and created necessary tickets, I need to provide a comprehensive response to the customer.
        
        Service Engineer identified: {service_result_3.final_output}
        
        Product Engineer identified: {product_result_3.final_output}
        
        Bug ticket created: {bug_result.final_output}
        
        Documentation ticket created: {doc_result.final_output}
        
        Please synthesize all this information into a clear, professional response for the customer that addresses all aspects of their complex issue.
        """
        final_result = await Runner.run(support_engineer, final_query)
        print(f"\nFinal Support Engineer response: {final_result.final_output}")
        
        # Add all_handoffs to final_result for UI to use
        final_result.all_handoffs = all_handoffs
        
        # Print handoff path information
        print("\n===== Handoff Path =====")
        for idx, handoff_item in enumerate(all_handoffs):
            if isinstance(handoff_item, dict):
                print(f"{idx + 1}. {handoff_item['source_agent']['name']} → {handoff_item['target_agent']['name']}")
                print(f"   Tool used: {handoff_item['tool_name']}")
            else:
                print(f"{idx + 1}. {handoff_item.source_agent.name} → {handoff_item.target_agent.name}")
                if hasattr(handoff_item, 'tool_name') and handoff_item.tool_name:
                    print(f"   Tool used: {handoff_item.tool_name}")
        
        # Print created tickets
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
        
        return final_result
    except Exception as e:
        print(f"Error processing complex case: {e}")
        return None

# Example queries for testing
async def run_demo():
    # Clear ticket list to ensure each run starts fresh
    global devops_tickets
    devops_tickets = []
    
    # Only run the complex case for demonstration
    complex_case = {
        "case_id": "CASE004",
        "query": "We're experiencing issues with our Enterprise Dashboard. The data visualization components are not displaying correctly, API calls are timing out intermittently, and we can't find documentation on how to configure the advanced filtering options. This is blocking our business operations and needs urgent attention."
    }
    
    try:
        await handle_support_case(complex_case["case_id"], complex_case["query"])
    except Exception as e:
        print(f"Error processing case '{complex_case['case_id']}': {e}")
    print("\n" + "=" * 50 + "\n")

if __name__ == "__main__":
    asyncio.run(run_demo())
