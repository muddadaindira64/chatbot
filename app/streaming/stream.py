async def stream(
    self,
    message: str,
    user_id: int | None = None,
    conversation_id: int | None = None,
    history: list[dict[str, str]] | None = None,
) -> AsyncGenerator[dict[str, Any], None]:

    logger.info(
        "STREAM START user_id=%s conversation_id=%s",
        user_id,
        conversation_id,
    )

    # -----------------------------------------------------
    # Load user memory
    # -----------------------------------------------------

    memory_context = ""

    if user_id is not None:
        try:
            async with AsyncSessionLocal() as db:
                memory_context = await build_user_context(
                    db=db,
                    user_id=user_id,
                )
        except Exception:
            logger.exception(
                "Failed to load memory user_id=%s",
                user_id,
            )

    # -----------------------------------------------------
    # Build messages
    # -----------------------------------------------------

    messages = self.build_messages(
        message=message,
        memory_context=memory_context or None,
        history=history,
    )

    try:

        # =================================================
        # FIRST LLM CALL
        # =================================================

        llm_with_tools = self.llm_service.get_tools_client()

        first_response = await llm_with_tools.ainvoke(
            messages
        )

        tool_calls = (
            getattr(
                first_response,
                "tool_calls",
                None,
            )
            or []
        )

        # =================================================
        # TOOL REQUIRED
        # =================================================

        if tool_calls:

            first_call = tool_calls[0]

            if isinstance(first_call, dict):
                tool_name = first_call.get("name")
            else:
                tool_name = getattr(
                    first_call,
                    "name",
                    None,
                )

            logger.info(
                "STREAM TOOL SELECTED: %s",
                tool_name,
            )

            yield {
                "type": "tool",
                "name": tool_name,
            }

            # -------------------------------------------------
            # Execute MCP tool
            # -------------------------------------------------

            tool_result = await atool_execution_node(
                {
                    "messages": [
                        first_response
                    ]
                }
            )

            tool_messages = (
                tool_result.get(
                    "messages",
                    []
                )
                if isinstance(
                    tool_result,
                    dict,
                )
                else []
            )

            logger.info(
                "STREAM TOOL RESULT COUNT: %s",
                len(tool_messages),
            )

            # -------------------------------------------------
            # IMPORTANT:
            # Assistant tool-call message MUST be followed
            # by the corresponding ToolMessage.
            # -------------------------------------------------

            messages.append(
                first_response
            )

            messages.extend(
                tool_messages
            )

            # =================================================
            # SECOND LLM CALL - FINAL ANSWER
            # =================================================

            logger.info(
                "STREAMING FINAL ANSWER AFTER TOOL"
            )

            final_llm = (
                self.llm_service.get_client()
            )

            async for chunk in final_llm.astream(
                messages
            ):

                content = getattr(
                    chunk,
                    "content",
                    "",
                )

                if not content:
                    continue

                # Some providers can return content
                # as structured blocks.
                if isinstance(
                    content,
                    list,
                ):
                    text_parts = []

                    for block in content:
                        if isinstance(
                            block,
                            dict,
                        ):
                            text = block.get(
                                "text",
                                "",
                            )

                            if text:
                                text_parts.append(
                                    text
                                )

                    content = "".join(
                        text_parts
                    )

                if content:

                    logger.debug(
                        "STREAM CHUNK: %r",
                        content,
                    )

                    yield {
                        "type": "content",
                        "content": content,
                    }

            logger.info(
                "STREAM FINAL ANSWER COMPLETED"
            )

            return

        # =================================================
        # NO TOOL REQUIRED
        # =================================================

        logger.info(
            "STREAMING DIRECT LLM ANSWER"
        )

        final_llm = (
            self.llm_service.get_client()
        )

        async for chunk in final_llm.astream(
            messages
        ):

            content = getattr(
                chunk,
                "content",
                "",
            )

            if not content:
                continue

            if isinstance(
                content,
                list,
            ):
                text_parts = []

                for block in content:

                    if isinstance(
                        block,
                        dict,
                    ):

                        text = block.get(
                            "text",
                            "",
                        )

                        if text:
                            text_parts.append(
                                text
                            )

                content = "".join(
                    text_parts
                )

            if content:

                logger.debug(
                    "STREAM CHUNK: %r",
                    content,
                )

                yield {
                    "type": "content",
                    "content": content,
                }

        logger.info(
            "STREAM DIRECT ANSWER COMPLETED"
        )

    except Exception as exc:

        logger.exception(
            "STREAM ERROR: %s",
            exc,
        )

        yield {
            "type": "error",
            "content": (
                "Sorry, I encountered an error "
                "while generating the response."
            ),
        }