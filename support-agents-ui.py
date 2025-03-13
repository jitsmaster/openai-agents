import streamlit as st
import asyncio
import uuid
from datetime import datetime
import graphviz
import sys
import os

# Import from support-agents.py
from support_agents import (
    support_engineer, handle_support_case, 
    support_cases, knowledge_base, devops_tickets
)

# Page configuration
st.set_page_config(
    page_title="Support Case Handling System",
    layout="wide"
)

# Title and description
st.title("Support Case Handling System")
st.markdown("Enter your case details below to get assistance from our support team.")

# Sidebar - can add some options or explanations
with st.sidebar:
    st.header("About")
    st.markdown("""
    This system uses AI agents to handle support cases:
    
    1. **Support Engineer** - Handles initial triage and provides solutions
    2. **Service Engineer** - Consulted for service implementation issues
    3. **Product Engineer** - Analyzes product features and determines if issues are bugs, documentation problems, or user errors
    4. **Documentation Ticketing Agent** - Creates documentation request tickets
    5. **Bug Ticketing Agent** - Creates bug tickets
    
    The system will show you the interaction between these agents and the final solution.
    """)
    
    # Add a reset button to clear the state
    if st.button("Reset"):
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()

# Main interface
col1, col2 = st.columns([1, 1])

with col1:
    # User input area
    st.header("Submit Your Case")
    
    # Add option to run demo case
    run_demo_case = st.checkbox("Run Demo Case (Complex Enterprise Dashboard Issue)", value=False)
    
    if run_demo_case:
        case_description = "We're experiencing issues with our Enterprise Dashboard. The data visualization components are not displaying correctly, API calls are timing out intermittently, and we can't find documentation on how to configure the advanced filtering options. This is blocking our business operations and needs urgent attention."
        st.text_area(
            "Case Description (Demo)",
            value=case_description,
            height=200,
            disabled=True
        )
    else:
        case_description = st.text_area(
            "Case Description",
            height=200,
            placeholder="Describe your issue here..."
        )
    
    submit_button = st.button("Submit Case")

# Initialize session state for storing results
if 'case_processed' not in st.session_state:
    st.session_state.case_processed = False
if 'result' not in st.session_state:
    st.session_state.result = None
if 'case_id' not in st.session_state:
    st.session_state.case_id = None
if 'handoffs_occurred' not in st.session_state:
    st.session_state.handoffs_occurred = []
if 'tickets' not in st.session_state:
    st.session_state.tickets = []

# Process submission
if submit_button and case_description:
    # Use CASE004 for demo case, otherwise generate a unique ID
    if run_demo_case:
        case_id = "CASE004"  # Use the same case ID as in run_demo
    else:
        case_id = f"CASE-{uuid.uuid4().hex[:6].upper()}"
    st.session_state.case_id = case_id
    
    # Display processing status
    with st.spinner("Processing your case..."):
        # Create temporary case
        temp_case = {
            "title": "Support Case",
            "description": case_description,
            "status": "New",
            "customer_email": "user@example.com",
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "product": "General Support",
            "service": "User Service"
        }
        
        # Add to case database
        support_cases[case_id] = temp_case
        
        # Clear previous tickets
        devops_tickets.clear()
        
        # Process case asynchronously
        try:
            # Create and run event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(handle_support_case(case_id, case_description))
            loop.close()
            
            # Store result in session state
            st.session_state.result = result
            st.session_state.case_processed = True
            
            # Extract handoff information
            if hasattr(result, 'all_handoffs'):
                # Use all_handoffs from complex case handler
                st.session_state.handoffs_occurred = result.all_handoffs
            elif hasattr(result, 'new_items') and result.new_items:
                # Use standard handoff mechanism
                handoffs_occurred = [item for item in result.new_items if item.type == "handoff_output_item"]
                st.session_state.handoffs_occurred = handoffs_occurred
            else:
                st.session_state.handoffs_occurred = []
            
            # Store tickets
            st.session_state.tickets = devops_tickets.copy()
            
        except Exception as e:
            st.error(f"Error processing case: {str(e)}")
            st.session_state.case_processed = False

# Display results in the second column
with col2:
    if st.session_state.case_processed and st.session_state.result:
        st.header("Support Response")
        st.markdown(st.session_state.result.final_output)
        
        # Display handoff path
        if st.session_state.handoffs_occurred:
            st.header("Agent Interaction Flow")
            
            # Create interaction flow chart showing each step of handoff
            graph = graphviz.Digraph()
            graph.attr(rankdir='TB')  # Top to bottom layout for sequential steps
            
            # Add user as the starting point
            graph.node("User", "User", shape="person")
            
            # Add initial connection to Support Engineer
            graph.node("Support_Engineer_0", "Support Engineer", shape="box")
            graph.edge("User", "Support_Engineer_0")
            
            # Track the last node for each agent to connect steps
            last_node_for_agent = {"Support Engineer": "Support_Engineer_0"}
            
            # Add each handoff as a sequential step
            for idx, handoff_item in enumerate(st.session_state.handoffs_occurred):
                # Handle both object and dictionary handoff items
                if isinstance(handoff_item, dict):
                    source = handoff_item['source_agent']['name']
                    target = handoff_item['target_agent']['name']
                    tool = handoff_item.get('tool_name', 'handoff')
                else:
                    source = handoff_item.source_agent.name
                    target = handoff_item.target_agent.name
                    tool = getattr(handoff_item, 'tool_name', 'handoff')
                
                # Create unique node IDs for this step
                source_node_id = f"{source.replace(' ', '_')}_{idx}"
                target_node_id = f"{target.replace(' ', '_')}_{idx}"
                
                # If source has appeared before, use its last node as the source
                if source in last_node_for_agent:
                    source_node_id = last_node_for_agent[source]
                else:
                    # Create a new node for this source
                    graph.node(source_node_id, source, shape="box")
                    last_node_for_agent[source] = source_node_id
                
                # Create a new node for this target
                graph.node(target_node_id, target, shape="box")
                last_node_for_agent[target] = target_node_id
                
                # Add edge for this handoff step with the tool name as label
                graph.edge(source_node_id, target_node_id, label=f"Step {idx+1}: {tool}")
            
            # Add final edge back to Support Engineer if needed
            if "Support Engineer" in last_node_for_agent and last_node_for_agent["Support Engineer"] != "Support_Engineer_0":
                final_node_id = f"Final_Response_{len(st.session_state.handoffs_occurred)}"
                graph.node(final_node_id, "Final Response", shape="box")
                graph.edge(last_node_for_agent["Support Engineer"], final_node_id)
            
            st.graphviz_chart(graph)
        else:
            st.info("Support Engineer handled your case directly without consulting other agents.")
        
        # Display created tickets
        if st.session_state.tickets:
            st.header("Created Tickets")
            for ticket in st.session_state.tickets:
                ticket_type = ticket['type']
                ticket_id = ticket['id']
                ticket_title = ticket['title']
                
                with st.expander(f"{ticket_type} Ticket: {ticket_id} - {ticket_title}"):
                    # Display ticket details in a more readable format
                    st.markdown(f"**ID:** {ticket['id']}")
                    st.markdown(f"**Type:** {ticket['type']}")
                    st.markdown(f"**Title:** {ticket['title']}")
                    st.markdown(f"**Product:** {ticket['product']}")
                    if 'severity' in ticket:
                        st.markdown(f"**Severity:** {ticket['severity']}")
                    st.markdown(f"**Status:** {ticket['status']}")
                    st.markdown(f"**Created at:** {ticket['created_at']}")
                    st.markdown(f"**URL:** [View in Azure DevOps](https://dev.azure.com/company/project/_workitems/edit/{ticket['id']})")
                    st.markdown("**Description:**")
                    st.text(ticket['description'])
        
        # Add detailed logs section (collapsed by default)
        st.header("Detailed Process Logs")
        with st.expander("View detailed process logs", expanded=False):
            # Display case details
            st.subheader("Case Details")
            if st.session_state.case_id in support_cases:
                case = support_cases[st.session_state.case_id]
                st.code(f"Case ID: {st.session_state.case_id}\nTitle: {case['title']}\nDescription: {case['description']}\nProduct: {case['product']}\nService: {case['service']}")
            
            # Display initial assessment
            st.subheader("Initial Support Engineer Assessment")
            st.code(st.session_state.result.final_output)
            
            # Display handoff steps
            if st.session_state.handoffs_occurred:
                st.subheader("Handoff Steps")
                for idx, handoff_item in enumerate(st.session_state.handoffs_occurred):
                    # Handle both object and dictionary handoff items
                    if isinstance(handoff_item, dict):
                        source = handoff_item['source_agent']['name']
                        target = handoff_item['target_agent']['name']
                        tool = handoff_item.get('tool_name', 'handoff')
                    else:
                        source = handoff_item.source_agent.name
                        target = handoff_item.target_agent.name
                        tool = getattr(handoff_item, 'tool_name', 'handoff')
                    
                    st.markdown(f"**Step {idx + 1}: {source} → {target}**")
                    st.code(f"Tool used: {tool}")
            
            # Display created tickets
            if st.session_state.tickets:
                st.subheader("Created Tickets")
                for ticket in st.session_state.tickets:
                    ticket_details = (
                        f"ID: {ticket['id']}\n"
                        f"Type: {ticket['type']}\n"
                        f"Title: {ticket['title']}\n"
                        f"Product: {ticket['product']}\n"
                    )
                    if 'severity' in ticket:
                        ticket_details += f"Severity: {ticket['severity']}\n"
                    ticket_details += (
                        f"Status: {ticket['status']}\n"
                        f"Created at: {ticket['created_at']}\n"
                        f"URL: https://dev.azure.com/company/project/_workitems/edit/{ticket['id']}\n"
                        f"Description: {ticket['description']}"
                    )
                    st.code(ticket_details)
