from pprint import pprint
from typing import Callable

from langchain.tools import tool as langchain_tool
from pctx_client import tool as pctx_tool

from eval_platform.eval_environment import EvalEnvironment


# ================= BOX =================
def test_box_operations_as_pctx_tools():
    with EvalEnvironment("box") as env:
        ops: list[Callable] = [
            env.ops.get_user,
            env.ops.get_user_by_email,
            env.ops.create_user,
            env.ops.get_folder,
            env.ops.create_folder,
            env.ops.update_folder,
            env.ops.delete_folder,
            env.ops.list_folder_items,
            env.ops.get_file,
            env.ops.create_file,
            env.ops.update_file,
            env.ops.delete_file,
            env.ops.upload_file_version,
            env.ops.create_comment,
            env.ops.get_comment,
            env.ops.update_comment,
            env.ops.delete_comment,
            env.ops.search_content,
        ]
        for op in ops:
            tool = pctx_tool(op, namespace="box")

            print("")
            print("=" * 20 + tool.name + "=" * 20)
            pprint(tool.get_input_jsonschema())
            pprint(tool.get_output_jsonschema())


def test_box_operations_as_langchain_tools():
    with EvalEnvironment("box") as env:
        ops: list[Callable] = [
            env.ops.get_user,
            env.ops.get_user_by_email,
            env.ops.create_user,
            env.ops.get_folder,
            env.ops.create_folder,
            env.ops.update_folder,
            env.ops.delete_folder,
            env.ops.list_folder_items,
            env.ops.get_file,
            env.ops.create_file,
            env.ops.update_file,
            env.ops.delete_file,
            env.ops.upload_file_version,
            env.ops.create_comment,
            env.ops.get_comment,
            env.ops.update_comment,
            env.ops.delete_comment,
            env.ops.search_content,
        ]
        for op in ops:
            tool = langchain_tool(op)

            print("")
            print("=" * 20 + tool.name + "=" * 20)
            pprint(tool.get_input_jsonschema())
            pprint(tool.get_output_jsonschema())


# ================= CALENDAR =================


def test_calendar_operations_as_pctx_tools():
    with EvalEnvironment("calendar") as env:
        for op in [
            env.ops.create_user,
            env.ops.get_user,
            env.ops.get_user_by_email,
            env.ops.create_calendar,
            env.ops.get_calendar,
            env.ops.update_calendar,
            env.ops.delete_calendar,
            env.ops.clear_calendar,
            env.ops.insert_calendar_list_entry,
            env.ops.get_calendar_list_entry,
            env.ops.list_calendar_list_entries,
            env.ops.create_event,
            env.ops.get_event,
            env.ops.list_events,
            env.ops.update_event,
            env.ops.delete_event,
            env.ops.quick_add_event,
        ]:
            tool = pctx_tool(op, namespace="calendar")

            print("")
            print("=" * 20 + tool.name + "=" * 20)
            pprint(tool.input_json_schema())
            pprint(tool.output_json_schema())


def test_calendar_operations_as_langchain_tools():
    with EvalEnvironment("calendar") as env:
        for op in [
            env.ops.create_user,
            env.ops.get_user,
            env.ops.get_user_by_email,
            env.ops.create_calendar,
            env.ops.get_calendar,
            env.ops.update_calendar,
            env.ops.delete_calendar,
            env.ops.clear_calendar,
            env.ops.insert_calendar_list_entry,
            env.ops.get_calendar_list_entry,
            env.ops.list_calendar_list_entries,
            env.ops.create_event,
            env.ops.get_event,
            env.ops.list_events,
            env.ops.update_event,
            env.ops.delete_event,
            env.ops.quick_add_event,
        ]:
            tool = langchain_tool(op)

            print("")
            print("=" * 20 + tool.name + "=" * 20)
            pprint(tool.get_input_jsonschema())
            pprint(tool.get_output_jsonschema())


# ================= SLACK =================


def test_slack_operations_as_pctx_tools():
    with EvalEnvironment("slack") as env:
        for op in [
            env.ops.create_team,
            env.ops.create_user,
            env.ops.get_user,
            env.ops.get_user_by_email,
            env.ops.list_users,
            env.ops.create_channel,
            env.ops.archive_channel,
            env.ops.unarchive_channel,
            env.ops.rename_channel,
            env.ops.set_channel_topic,
            env.ops.invite_user_to_channel,
            env.ops.kick_user_from_channel,
            env.ops.join_channel,
            env.ops.leave_channel,
            env.ops.list_user_channels,
            env.ops.list_public_channels,
            env.ops.send_message,
            env.ops.send_direct_message,
            env.ops.update_message,
            env.ops.delete_message,
            env.ops.add_emoji_reaction,
            env.ops.remove_emoji_reaction,
            env.ops.get_reactions,
            env.ops.list_channel_history,
            env.ops.list_thread_messages,
        ]:
            tool = pctx_tool(op, namespace="slack")

            print("")
            print("=" * 20 + tool.name + "=" * 20)
            pprint(tool.input_json_schema())
            pprint(tool.output_json_schema())


def test_slack_operations_as_langchain_tools():
    with EvalEnvironment("slack") as env:
        for op in [
            env.ops.create_team,
            env.ops.create_user,
            env.ops.get_user,
            env.ops.get_user_by_email,
            env.ops.list_users,
            env.ops.create_channel,
            env.ops.archive_channel,
            env.ops.unarchive_channel,
            env.ops.rename_channel,
            env.ops.set_channel_topic,
            env.ops.invite_user_to_channel,
            env.ops.kick_user_from_channel,
            env.ops.join_channel,
            env.ops.leave_channel,
            env.ops.list_user_channels,
            env.ops.list_public_channels,
            env.ops.send_message,
            env.ops.send_direct_message,
            env.ops.update_message,
            env.ops.delete_message,
            env.ops.add_emoji_reaction,
            env.ops.remove_emoji_reaction,
            env.ops.get_reactions,
            env.ops.list_channel_history,
            env.ops.list_thread_messages,
        ]:
            tool = langchain_tool(op)

            print("")
            print("=" * 20 + tool.name + "=" * 20)
            pprint(tool.get_input_jsonschema())
            pprint(tool.get_output_jsonschema())


# ================= LINEAR =================


def test_linear_operations_as_pctx_tools():
    with EvalEnvironment("linear") as env:
        ops: list[Callable] = [
            env.ops.create_organization,
            env.ops.get_organization,
            env.ops.create_user,
            env.ops.get_user,
            env.ops.get_user_by_email,
            env.ops.create_team,
            env.ops.get_team,
            env.ops.create_workflow_state,
            env.ops.get_workflow_state,
            env.ops.create_issue,
            env.ops.get_issue,
            env.ops.update_issue,
            env.ops.delete_issue,
            env.ops.create_comment,
            env.ops.get_comment,
            env.ops.update_comment,
            env.ops.delete_comment,
            env.ops.create_project,
            env.ops.get_project,
            env.ops.update_project,
            env.ops.delete_project,
            env.ops.list_projects,
            env.ops.create_project_milestone,
            env.ops.get_project_milestone,
            env.ops.update_project_milestone,
            env.ops.delete_project_milestone,
            env.ops.create_cycle,
            env.ops.get_cycle,
            env.ops.update_cycle,
            env.ops.delete_cycle,
            env.ops.create_initiative,
            env.ops.get_initiative,
            env.ops.update_initiative,
            env.ops.delete_initiative,
            env.ops.create_document,
            env.ops.get_document,
            env.ops.update_document,
            env.ops.delete_document,
            env.ops.create_attachment,
            env.ops.get_attachment,
            env.ops.delete_attachment,
            env.ops.create_issue_label,
            env.ops.get_issue_label,
            env.ops.update_issue_label,
            env.ops.delete_issue_label,
            env.ops.create_issue_relation,
            env.ops.get_issue_relation,
            env.ops.delete_issue_relation,
            env.ops.list_issue_relations,
        ]
        for op in ops:
            tool = pctx_tool(op, namespace="linear")

            print("")
            print("=" * 20 + tool.name + "=" * 20)
            pprint(tool.input_json_schema())
            pprint(tool.output_json_schema())


def test_linear_operations_as_langchain_tools():
    with EvalEnvironment("linear") as env:
        ops: list[Callable] = [
            env.ops.create_organization,
            env.ops.get_organization,
            env.ops.create_user,
            env.ops.get_user,
            env.ops.get_user_by_email,
            env.ops.create_team,
            env.ops.get_team,
            env.ops.create_workflow_state,
            env.ops.get_workflow_state,
            env.ops.create_issue,
            env.ops.get_issue,
            env.ops.update_issue,
            env.ops.delete_issue,
            env.ops.create_comment,
            env.ops.get_comment,
            env.ops.update_comment,
            env.ops.delete_comment,
            env.ops.create_project,
            env.ops.get_project,
            env.ops.update_project,
            env.ops.delete_project,
            env.ops.list_projects,
            env.ops.create_project_milestone,
            env.ops.get_project_milestone,
            env.ops.update_project_milestone,
            env.ops.delete_project_milestone,
            env.ops.create_cycle,
            env.ops.get_cycle,
            env.ops.update_cycle,
            env.ops.delete_cycle,
            env.ops.create_initiative,
            env.ops.get_initiative,
            env.ops.update_initiative,
            env.ops.delete_initiative,
            env.ops.create_document,
            env.ops.get_document,
            env.ops.update_document,
            env.ops.delete_document,
            env.ops.create_attachment,
            env.ops.get_attachment,
            env.ops.delete_attachment,
            env.ops.create_issue_label,
            env.ops.get_issue_label,
            env.ops.update_issue_label,
            env.ops.delete_issue_label,
            env.ops.create_issue_relation,
            env.ops.get_issue_relation,
            env.ops.delete_issue_relation,
            env.ops.list_issue_relations,
        ]
        for op in ops:
            tool = langchain_tool(op)

            print("")
            print("=" * 20 + tool.name + "=" * 20)
            pprint(tool.get_input_jsonschema())
            pprint(tool.get_output_jsonschema())
